"""
Layer viewer widget for visualizing G-code toolpath layers with interactive
pan/zoom navigation. Displays print and travel moves with pressure-based
coloring and directional arrows.
"""

import math
import numpy as np
import pyqtgraph as pg
import pyqtgraph.opengl as gl

from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QWidget,
    QSlider, QPushButton, QStackedWidget
)
from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import (
    QPainter, QPen, QColor, QFont, QPainterPath,
    QPolygonF, QBrush
)

from src.ui.theme import Theme


class LayerViewerWidget(QFrame):
    """Widget for viewing G-code toolpath layers with pan/zoom and pressure coloring."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(350)
        self.setStyleSheet(f"""
            LayerViewerWidget {{
                background-color: {Theme.BG_SECONDARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 8px;
            }}
        """)

        self._all_moves: list[list[dict]] = []
        self._all_pressure: list = []

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        # Title label
        title_label = QLabel("Layer View")
        title_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; border: none; background: transparent;")
        layout.addWidget(title_label)

        # Canvas Stack
        self._stack = QStackedWidget()
        layout.addWidget(self._stack, 1)
        
        self._canvas = self._LayerCanvas(self)
        self._canvas_3d = self._LayerCanvas3D(self)
        
        self._stack.addWidget(self._canvas)
        self._stack.addWidget(self._canvas_3d)

        # Controls bar
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(0, 4, 0, 0)
        controls_layout.setSpacing(10)

        # Layer slider
        self._layer_slider = QSlider(Qt.Orientation.Horizontal)
        self._layer_slider.setRange(0, 0)
        self._layer_slider.setValue(0)
        self._layer_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                background: {Theme.BG_TERTIARY};
                height: 6px;
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {Theme.ACCENT_PRIMARY};
                width: 14px;
                height: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }}
            QSlider::sub-page:horizontal {{
                background: {Theme.ACCENT_PRIMARY};
                border-radius: 3px;
            }}
        """)
        controls_layout.addWidget(self._layer_slider, 1)

        # Layer label
        self._layer_label = QLabel("Layer: 0 / 0")
        self._layer_label.setFont(QFont("Segoe UI", 10))
        self._layer_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; border: none; background: transparent;")
        self._layer_label.setMinimumWidth(100)
        controls_layout.addWidget(self._layer_label)

        # Toggle 3D Button
        self._toggle_3d_btn = QPushButton("3D View")
        self._toggle_3d_btn.setFont(QFont("Segoe UI", 9))
        self._toggle_3d_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._toggle_3d_btn.setCheckable(True)
        self._toggle_3d_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.BG_TERTIARY};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 4px;
                padding: 4px 12px;
            }}
            QPushButton:hover {{
                background-color: {Theme.BG_ELEVATED};
                border-color: {Theme.ACCENT_PRIMARY};
            }}
            QPushButton:checked {{
                background-color: {Theme.ACCENT_PRIMARY};
                border-color: {Theme.ACCENT_PRIMARY};
            }}
        """)
        controls_layout.addWidget(self._toggle_3d_btn)

        # Fit to View button
        fit_btn = QPushButton("Fit to View")
        fit_btn.setFont(QFont("Segoe UI", 9))
        fit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        fit_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.BG_TERTIARY};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 4px;
                padding: 4px 12px;
            }}
            QPushButton:hover {{
                background-color: {Theme.BG_ELEVATED};
                border-color: {Theme.ACCENT_PRIMARY};
            }}
            QPushButton:pressed {{
                background-color: {Theme.ACCENT_PRIMARY};
            }}
        """)
        controls_layout.addWidget(fit_btn)

        layout.addLayout(controls_layout)

        # Connect signals
        self._layer_slider.valueChanged.connect(self._on_layer_changed)
        fit_btn.clicked.connect(self._canvas.fit_to_view)
        fit_btn.clicked.connect(self._canvas_3d.fit_to_view)
        self._toggle_3d_btn.toggled.connect(self._on_toggle_3d)

    def set_moves(self, moves: list, pressure_results: list = None):
        """Set layer move data and optional pressure results.

        Args:
            moves: List of lists. Each inner list contains move dicts with keys:
                   'type' ('print'|'travel'), 'x1', 'y1', 'x2', 'y2', and optionally 'vpi'.
            pressure_results: Optional list that can be used to augment VPI data.
                              If provided and moves lack VPI data, pressure values
                              are applied sequentially.
        """
        self._all_moves = list(moves) if moves else []
        self._all_pressure = list(pressure_results) if pressure_results else []

        # If pressure_results is provided, apply VPI values to moves
        if self._all_pressure:
            pressure_idx = 0
            for layer_moves in self._all_moves:
                for move in layer_moves:
                    if 'vpi' not in move and pressure_idx < len(self._all_pressure):
                        if isinstance(self._all_pressure[pressure_idx], dict):
                            move['vpi'] = self._all_pressure[pressure_idx].get('vpi', 0.0)
                        elif isinstance(self._all_pressure[pressure_idx], (int, float)):
                            move['vpi'] = float(self._all_pressure[pressure_idx])
                        pressure_idx += 1

        num_layers = max(len(self._all_moves), 1)
        self._layer_slider.setRange(0, num_layers - 1)
        self._layer_slider.setValue(0)

        # Set all moves to 3D canvas
        self._canvas_3d.set_all_moves(self._all_moves)
        
        if self._all_moves:
            self.set_layer(0)
        else:
            self._canvas._moves = []
            self._canvas._bounds_cache = None
            self._canvas_3d.set_layer(0)
            self._layer_label.setText("Layer: 0 / 0")
            self._canvas.update()

    def set_layer(self, layer_number: int):
        """Display a specific layer.

        Args:
            layer_number: Zero-based layer index.
        """
        if 0 <= layer_number < len(self._all_moves):
            self._canvas._moves = self._all_moves[layer_number]
        else:
            self._canvas._moves = []

        self._canvas._bounds_cache = None
        self._canvas._needs_redraw = True
        self._canvas_3d.set_layer(layer_number)
        
        total = max(len(self._all_moves), 1)
        self._layer_label.setText(f"Layer: {layer_number + 1} / {total}")
        self._canvas.update()

    def _on_toggle_3d(self, checked: bool):
        if checked:
            self._stack.setCurrentWidget(self._canvas_3d)
            self._toggle_3d_btn.setText("2D View")
        else:
            self._stack.setCurrentWidget(self._canvas)
            self._toggle_3d_btn.setText("3D View")
            
    def _on_layer_changed(self, value: int):
        """Handle layer slider value change."""
        self.set_layer(value)

    class _LayerCanvas(QWidget):
        """Inner canvas widget that renders the layer toolpath visualization."""

        def __init__(self, parent=None):
            super().__init__(parent)
            self.setMinimumHeight(250)
            self.setMouseTracking(True)
            self.setStyleSheet("background: transparent; border: none;")

            self._moves: list[dict] = []
            self._all_moves: list[list[dict]] = []
            self._all_pressure: list = []

            # Transform state
            self._pan_offset = QPointF(0.0, 0.0)
            self._zoom = 1.0
            self._dragging = False
            self._last_mouse_pos = QPointF()

            # Cached bounds
            self._bounds_cache = None

        def _calculate_bounds(self) -> tuple[float, float, float, float]:
            """Calculate and cache min/max x,y bounds across current layer moves.

            Returns:
                Tuple of (min_x, min_y, max_x, max_y).
            """
            if self._bounds_cache is not None:
                return self._bounds_cache

            if not self._moves:
                self._bounds_cache = (0.0, 0.0, 1.0, 1.0)
                return self._bounds_cache

            min_x = float('inf')
            min_y = float('inf')
            max_x = float('-inf')
            max_y = float('-inf')

            for move in self._moves:
                for coord_key_x, coord_key_y in [('x1', 'y1'), ('x2', 'y2')]:
                    x = move.get(coord_key_x, 0.0)
                    y = move.get(coord_key_y, 0.0)
                    min_x = min(min_x, x)
                    min_y = min(min_y, y)
                    max_x = max(max_x, x)
                    max_y = max(max_y, y)

            # Ensure non-zero extent
            if max_x - min_x < 1e-6:
                min_x -= 1.0
                max_x += 1.0
            if max_y - min_y < 1e-6:
                min_y -= 1.0
                max_y += 1.0

            # Add padding (5%)
            pad_x = (max_x - min_x) * 0.05
            pad_y = (max_y - min_y) * 0.05
            self._bounds_cache = (min_x - pad_x, min_y - pad_y, max_x + pad_x, max_y + pad_y)
            return self._bounds_cache

        def _transform_point(self, gx: float, gy: float) -> QPointF:
            """Map G-code coordinates to widget pixel coordinates.

            Scales to fit the widget, then applies pan and zoom transforms.
            G-code Y is typically inverted relative to screen Y.

            Args:
                gx: G-code X coordinate.
                gy: G-code Y coordinate.

            Returns:
                QPointF in widget pixel space.
            """
            bounds = self._calculate_bounds()
            min_x, min_y, max_x, max_y = bounds
            extent_x = max_x - min_x
            extent_y = max_y - min_y

            w = self.width()
            h = self.height()

            # Scale to fit, maintaining aspect ratio
            scale_x = w / extent_x if extent_x > 0 else 1.0
            scale_y = h / extent_y if extent_y > 0 else 1.0
            scale = min(scale_x, scale_y) * 0.9  # 90% to leave margin

            # Center offset
            cx = w / 2.0
            cy = h / 2.0
            data_cx = (min_x + max_x) / 2.0
            data_cy = (min_y + max_y) / 2.0

            # Map to widget coords (invert Y for screen)
            px = cx + (gx - data_cx) * scale * self._zoom + self._pan_offset.x()
            py = cy - (gy - data_cy) * scale * self._zoom + self._pan_offset.y()

            return QPointF(px, py)

        def paintEvent(self, event):
            try:
                self._safe_paintEvent(event)
            except Exception as e:
                import traceback
                with open('paintevent_error.txt', 'a') as errf:
                    errf.write(f'Error in src/ui/widgets/layer_viewer_widget.py: {str(e)}\n{traceback.format_exc()}\n')

        def _safe_paintEvent(self, event):
            painter = QPainter(self)
            painter.fillRect(self.rect(), QColor(Theme.BG_TERTIARY))
            
            if not self._moves:
                painter.setPen(QColor(Theme.TEXT_MUTED))
                painter.setFont(QFont("Segoe UI", 11))
                painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No layer data available")
                painter.end()
                return
                
            from PyQt6.QtGui import QPixmap
            from PyQt6.QtCore import QLineF
            
            # If pixmap is missing or wrong size, or needs redraw, recreate it
            if self._needs_redraw or self._pixmap_cache is None or self._pixmap_cache.size() != self.size():
                self._pixmap_cache = QPixmap(self.size())
                self._pixmap_cache.fill(Qt.GlobalColor.transparent)
                
                cache_painter = QPainter(self._pixmap_cache)
                cache_painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                
                draw_arrows = len(self._moves) < 1000
                num_buckets = 20
                buckets = [[] for _ in range(num_buckets)]
                travel_lines = []
                arrow_data = []
                
                # Precompute transforms
                bounds = self._calculate_bounds()
                min_x, min_y, max_x, max_y = bounds
                extent_x = max_x - min_x
                extent_y = max_y - min_y
                w = self.width()
                h = self.height()
                scale_x = w / extent_x if extent_x > 0 else 1.0
                scale_y = h / extent_y if extent_y > 0 else 1.0
                scale = min(scale_x, scale_y) * 0.9
                cx = w / 2.0
                cy = h / 2.0
                data_cx = (min_x + max_x) / 2.0
                data_cy = (min_y + max_y) / 2.0

                eff_scale = scale * self._zoom
                pan_x = self._pan_offset.x()
                pan_y = self._pan_offset.y()
                
                for move in self._moves:
                    x1 = move.get('x1', 0.0)
                    y1 = move.get('y1', 0.0)
                    x2 = move.get('x2', 0.0)
                    y2 = move.get('y2', 0.0)
                    move_type = move.get('type', 'travel')
                    vpi = move.get('vpi', 0.0)
                    
                    px1 = cx + (x1 - data_cx) * eff_scale + pan_x
                    py1 = cy - (y1 - data_cy) * eff_scale + pan_y
                    px2 = cx + (x2 - data_cx) * eff_scale + pan_x
                    py2 = cy - (y2 - data_cy) * eff_scale + pan_y
                    
                    p1 = QPointF(px1, py1)
                    p2 = QPointF(px2, py2)
                    
                    line = QLineF(p1, p2)
                    
                    if move_type == 'travel':
                        travel_lines.append(line)
                    else:
                        bucket_idx = max(0, min(num_buckets - 1, int(vpi * num_buckets)))
                        buckets[bucket_idx].append(line)
                        if draw_arrows:
                            color = Theme.pressure_color(bucket_idx / float(num_buckets - 1))
                            arrow_data.append((p1, p2, color))
                
                if travel_lines:
                    cache_painter.setPen(QPen(QColor(Theme.TEXT_MUTED), 1, Qt.PenStyle.DotLine, Qt.PenCapStyle.RoundCap))
                    cache_painter.drawLines(travel_lines)
                    
                for i in range(num_buckets):
                    if buckets[i]:
                        color = Theme.pressure_color(i / float(max(1, num_buckets - 1)))
                        cache_painter.setPen(QPen(color, 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                        cache_painter.drawLines(buckets[i])
                        
                if draw_arrows:
                    for p1, p2, color in arrow_data:
                        self._draw_direction_arrow(cache_painter, p1, p2, color)
                        
                cache_painter.end()
                self._needs_redraw = False
                
            # Draw the cached pixmap (0ms)
            painter.drawPixmap(0, 0, self._pixmap_cache)
            painter.end()

        def _draw_direction_arrow(self, painter: QPainter, p1: QPointF, p2: QPointF, color: QColor):
            """Draw a small triangular direction arrow at the midpoint of a move.

            Args:
                painter: Active QPainter.
                p1: Start point in pixel coords.
                p2: End point in pixel coords.
                color: Arrow fill color.
            """
            dx = p2.x() - p1.x()
            dy = p2.y() - p1.y()
            length = math.sqrt(dx * dx + dy * dy)

            if length < 8:
                return  # Too short to draw arrow

            # Midpoint
            mx = (p1.x() + p2.x()) / 2.0
            my = (p1.y() + p2.y()) / 2.0

            # Normalize direction
            nx = dx / length
            ny = dy / length

            # Perpendicular
            px = -ny
            py = nx

            # Arrow size
            arrow_size = min(5.0, length * 0.15)

            # Triangle vertices: tip at midpoint + forward, base behind
            tip = QPointF(mx + nx * arrow_size, my + ny * arrow_size)
            base_left = QPointF(
                mx - nx * arrow_size * 0.5 + px * arrow_size * 0.5,
                my - ny * arrow_size * 0.5 + py * arrow_size * 0.5
            )
            base_right = QPointF(
                mx - nx * arrow_size * 0.5 - px * arrow_size * 0.5,
                my - ny * arrow_size * 0.5 - py * arrow_size * 0.5
            )

            arrow_polygon = QPolygonF([tip, base_left, base_right])

            arrow_color = QColor(color)
            arrow_color.setAlpha(200)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(arrow_color))
            painter.drawPolygon(arrow_polygon)

        def fit_to_view(self):
            """Reset pan and zoom to fit the entire layer in view."""
            self._pan_offset = QPointF(0, 0)
            self._zoom = 1.0
            self._pixmap_cache = None
            self._needs_redraw = True
            self.update()

        def _invalidate_cache(self):
            self._bounds_cache = None
            self._needs_redraw = True
            
        def resizeEvent(self, event):
            self._needs_redraw = True
            super().resizeEvent(event)

        def mousePressEvent(self, event):
            if event.button() == Qt.MouseButton.LeftButton:
                self._dragging = True
                pos = event.position() if hasattr(event, 'position') else event.pos()
                self._last_mouse_pos = QPointF(pos)
                self.setCursor(Qt.CursorShape.ClosedHandCursor)

        def mouseMoveEvent(self, event):
            if self._dragging:
                pos = event.position() if hasattr(event, 'position') else event.pos()
                current_pos = QPointF(pos)
                delta = current_pos - self._last_mouse_pos
                self._pan_offset += delta
                self._last_mouse_pos = current_pos
                self.update()

        def mouseReleaseEvent(self, event):
            if event.button() == Qt.MouseButton.LeftButton:
                self._dragging = False
                self.setCursor(Qt.CursorShape.ArrowCursor)

        def wheelEvent(self, event):
            delta = event.angleDelta().y()
            if delta > 0:
                self._zoom *= 1.1
            elif delta < 0:
                self._zoom /= 1.1

            # Clamp zoom
            self._zoom = max(0.1, min(20.0, self._zoom))
            self.update()

    class _LayerCanvas3D(gl.GLViewWidget):
        """Inner canvas widget that renders the toolpath visualization in 3D."""
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setMinimumHeight(250)
            # Set background to match theme
            bg_color = QColor(Theme.BG_SECONDARY)
            self.setBackgroundColor(bg_color)
            
            self._all_moves = []
            self._current_layer = 0
            
            self._print_item = gl.GLLinePlotItem(mode='lines', width=2)
            self.addItem(self._print_item)
            
            self._travel_item = gl.GLLinePlotItem(mode='lines', width=1)
            self.addItem(self._travel_item)
            
            # Pre-computed arrays
            self._full_print_pos = np.zeros((0, 3), dtype=np.float32)
            self._full_print_color = np.zeros((0, 4), dtype=np.float32)
            self._full_travel_pos = np.zeros((0, 3), dtype=np.float32)
            self._full_travel_color = np.zeros((0, 4), dtype=np.float32)
            
            # Layer indices
            self._print_layer_indices = []
            self._travel_layer_indices = []
            
        def set_all_moves(self, all_moves):
            self._all_moves = all_moves
            self._current_layer = 0
            self._precompute_arrays()
            self._update_geometry()
            
        def _precompute_arrays(self):
            print_pos = []
            print_color = []
            travel_pos = []
            
            self._print_layer_indices = []
            self._travel_layer_indices = []
            
            for layer in self._all_moves:
                for m in layer:
                    x1, y1, z1 = m.get('x1',0), m.get('y1',0), m.get('z1',0)
                    x2, y2, z2 = m.get('x2',0), m.get('y2',0), m.get('z2',0)
                    
                    if m.get('type') == 'travel':
                        travel_pos.extend([[x1, y1, z1], [x2, y2, z2]])
                    else:
                        print_pos.extend([[x1, y1, z1], [x2, y2, z2]])
                        vpi = m.get('vpi', 0.0)
                        qcolor = Theme.pressure_color(vpi)
                        r, g, b, a = qcolor.redF(), qcolor.greenF(), qcolor.blueF(), qcolor.alphaF()
                        print_color.extend([[r, g, b, a], [r, g, b, a]])
                        
                self._print_layer_indices.append(len(print_pos))
                self._travel_layer_indices.append(len(travel_pos))
                
            self._full_print_pos = np.array(print_pos, dtype=np.float32)
            self._full_print_color = np.array(print_color, dtype=np.float32)
            self._full_travel_pos = np.array(travel_pos, dtype=np.float32)
            
            if travel_pos:
                travel_c = QColor(Theme.TEXT_MUTED)
                tc = [travel_c.redF(), travel_c.greenF(), travel_c.blueF(), 0.5]
                self._full_travel_color = np.tile(tc, (len(travel_pos), 1)).astype(np.float32)
            else:
                self._full_travel_color = np.zeros((0, 4), dtype=np.float32)

        def set_layer(self, layer_number: int):
            self._current_layer = layer_number
            self._update_geometry()
            
        def fit_to_view(self):
            if len(self._full_print_pos) == 0:
                return
            
            min_x = np.min(self._full_print_pos[:, 0])
            max_x = np.max(self._full_print_pos[:, 0])
            min_y = np.min(self._full_print_pos[:, 1])
            max_y = np.max(self._full_print_pos[:, 1])
            min_z = np.min(self._full_print_pos[:, 2])
            max_z = np.max(self._full_print_pos[:, 2])
            
            cx = (min_x + max_x) / 2
            cy = (min_y + max_y) / 2
            cz = (min_z + max_z) / 2
            self.opts['center'] = pg.Vector(cx, cy, cz)
            distance = max(max_x - min_x, max_y - min_y, max_z - min_z) * 1.5
            self.opts['distance'] = max(distance, 10.0)
            self.update()

        def _update_geometry(self):
            if not self._all_moves or self._current_layer < 0 or self._current_layer >= len(self._print_layer_indices):
                self._print_item.setData(pos=np.zeros((0,3), dtype=np.float32), color=np.zeros((0,4), dtype=np.float32))
                self._travel_item.setData(pos=np.zeros((0,3), dtype=np.float32), color=np.zeros((0,4), dtype=np.float32))
                return
                
            p_idx = self._print_layer_indices[self._current_layer]
            t_idx = self._travel_layer_indices[self._current_layer]
            
            if p_idx > 0:
                self._print_item.setData(pos=self._full_print_pos[:p_idx], color=self._full_print_color[:p_idx])
            else:
                self._print_item.setData(pos=np.zeros((0,3), dtype=np.float32), color=np.zeros((0,4), dtype=np.float32))
                
            if t_idx > 0:
                self._travel_item.setData(pos=self._full_travel_pos[:t_idx], color=self._full_travel_color[:t_idx])
            else:
                self._travel_item.setData(pos=np.zeros((0,3), dtype=np.float32), color=np.zeros((0,4), dtype=np.float32))
