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
    QSlider, QPushButton, QComboBox, QStackedWidget
)
from PyQt6.QtCore import Qt, QPointF, QRectF, QTimer
from PyQt6.QtGui import (
    QPainter, QPen, QColor, QFont, QPainterPath,
    QPolygonF, QBrush
)

from src.ui.theme import Theme


class LayerViewerWidget(QFrame):
    """Widget for viewing G-code toolpath layers with pan/zoom and pressure coloring."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(650)
        self.setStyleSheet(f"""
            LayerViewerWidget {{
                background-color: {Theme.BG_SECONDARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 8px;
            }}
        """)

        self._all_moves: list[list[dict]] = []
        self._all_pressure: list = []
        
        self._sim_time_sec = -1.0
        self._current_layer_total_time = 0.0
        self._is_playing = False
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_sim_tick)

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

        # Canvas 3D
        self._canvas_3d = self._LayerCanvas3D(self)
        layout.addWidget(self._canvas_3d, 1)

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
        self._toggle_3d_btn.setChecked(True)
        self._toggle_3d_btn.setText("2D View")
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
        
        # Simulation controls
        sim_layout = QHBoxLayout()
        sim_layout.setContentsMargins(0, 0, 0, 0)
        sim_layout.setSpacing(10)
        
        self._play_btn = QPushButton("▶ Play")
        self._play_btn.setFixedWidth(80)
        self._play_btn.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self._play_btn.setStyleSheet(fit_btn.styleSheet())
        sim_layout.addWidget(self._play_btn)
        
        self._play_start_btn = QPushButton("⏮ From Start")
        self._play_start_btn.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self._play_start_btn.setStyleSheet(fit_btn.styleSheet())
        sim_layout.addWidget(self._play_start_btn)
        
        self._sim_slider = QSlider(Qt.Orientation.Horizontal)
        self._sim_slider.setRange(0, 0)
        self._sim_slider.setStyleSheet(self._layer_slider.styleSheet().replace(Theme.ACCENT_PRIMARY, Theme.SUCCESS))
        sim_layout.addWidget(self._sim_slider, 1)
        
        self._speed_combo = QComboBox()
        self._speed_combo.addItems(["1x", "2x", "5x", "10x", "Max"])
        self._speed_combo.setCurrentIndex(2) # Default 5x
        self._speed_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {Theme.BG_TERTIARY};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 4px;
                padding: 4px 8px;
            }}
        """)
        sim_layout.addWidget(self._speed_combo)
        
        layout.addLayout(sim_layout)


        # Connect signals
        self._layer_slider.valueChanged.connect(self._on_layer_changed)
        fit_btn.clicked.connect(self._canvas_3d.fit_to_view)
        self._play_btn.clicked.connect(self._toggle_playback)
        self._play_start_btn.clicked.connect(self._play_from_start)
        self._sim_slider.valueChanged.connect(self._on_sim_scrub)
        self._speed_combo.currentIndexChanged.connect(self._update_timer_speed)

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
            self._canvas_3d.set_layer(0)
            self._layer_label.setText("Layer: 0 / 0")
    def set_layer(self, layer_number: int):
        """Display a specific layer.

        Args:
            layer_number: Zero-based layer index.
        """
        # Tell 3D canvas first so we can get layer duration
        self._canvas_3d.set_layer(layer_number)
        
        self._current_layer_total_time = self._canvas_3d.get_current_layer_duration()
            
        # Reset simulation state
        if not self._is_playing:
            self._sim_time_sec = self._current_layer_total_time
            
        self._sim_slider.blockSignals(True)
        self._sim_slider.setRange(0, 1000)
        perc = 1000
        if self._current_layer_total_time > 0 and self._sim_time_sec >= 0:
            perc = int((min(self._sim_time_sec, self._current_layer_total_time) / self._current_layer_total_time) * 1000)
        self._sim_slider.setValue(perc)
        self._sim_slider.blockSignals(False)

        self._canvas_3d._sim_time_sec = self._sim_time_sec
        self._canvas_3d._update_geometry()
        
        total = max(len(self._all_moves), 1)
        self._layer_label.setText(f"Layer: {layer_number + 1} / {total}")

    def _play_from_start(self):
        if not self._all_moves:
            return
        self._layer_slider.setValue(0)
        self._sim_time_sec = 0.0
        if not self._is_playing:
            self._toggle_playback()

    def _toggle_playback(self):
        if not self._all_moves:
            return
            
        self._is_playing = not self._is_playing
        if self._is_playing:
            self._play_btn.setText("⏸ Pause")
            if self._sim_time_sec >= self._current_layer_total_time - 0.001:
                self._sim_time_sec = 0.0
            self._timer.setInterval(16) # 60fps
            self._timer.start()
        else:
            self._play_btn.setText("▶ Play")
            self._timer.stop()
            
    def _update_timer_speed(self):
        # We handle speed internally in _on_sim_tick via multiplier now
        pass
            
    def _on_sim_tick(self):
        dt = 0.016
        multipliers = [1.0, 2.0, 5.0, 10.0, 50.0]
        mult = multipliers[self._speed_combo.currentIndex()]
        
        self._sim_time_sec += dt * mult
        
        if self._sim_time_sec >= self._current_layer_total_time:
            # Reached end of layer
            current_layer = self._layer_slider.value()
            if current_layer < len(self._all_moves) - 1:
                self._sim_time_sec = 0.0
                self._layer_slider.setValue(current_layer + 1)
                self._update_canvases_sim() 
            else:
                self._sim_time_sec = self._current_layer_total_time
                self._update_canvases_sim()
                self._toggle_playback() # auto pause at very end
        else:
            self._sim_slider.blockSignals(True)
            if self._current_layer_total_time > 0:
                perc = int((self._sim_time_sec / self._current_layer_total_time) * 1000)
                self._sim_slider.setValue(perc)
            self._sim_slider.blockSignals(False)
            self._update_canvases_sim()

    def _on_sim_scrub(self, value: int):
        self._sim_time_sec = (value / 1000.0) * self._current_layer_total_time
        self._update_canvases_sim()
        
    def _update_canvases_sim(self):
        self._canvas_3d._sim_time_sec = self._sim_time_sec
        self._canvas_3d._update_geometry()

                
    def _on_layer_changed(self, value: int):
        """Handle layer slider value change."""
        self.set_layer(value)

    Theme.TEXT_MUTED_QCOLOR = QColor(Theme.TEXT_MUTED)
    class _LayerCanvas3D(gl.GLViewWidget):
        """Inner canvas widget that renders the toolpath visualization in 3D."""
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setMinimumHeight(250)
            
            # Store mouse pos for inversion
            self._last_mouse_pos = None

            # Set background to match theme
            bg_color = QColor(Theme.BG_SECONDARY)
            self.setBackgroundColor(bg_color)
            
            self._all_moves = []
            self._current_layer = 0
            
            self._print_item = gl.GLLinePlotItem(mode='lines', width=2)
            self.addItem(self._print_item)
            
            self._travel_item = gl.GLLinePlotItem(mode='lines', width=1)
            self.addItem(self._travel_item)
            
            self._nozzle_item = gl.GLScatterPlotItem(size=10, pxMode=True)
            self.addItem(self._nozzle_item)
            
            self._grid_item = gl.GLGridItem()
            # Set grid color to be very subtle
            grid_c = QColor(Theme.TEXT_MUTED)
            self._grid_item.setColor((grid_c.redF(), grid_c.greenF(), grid_c.blueF(), 0.3))
            self.addItem(self._grid_item)
            
            self._sim_time_sec = -1.0
            
            # Pre-computed arrays
            self._full_print_pos = np.zeros((0, 3), dtype=np.float32)
            self._full_print_color = np.zeros((0, 4), dtype=np.float32)
            self._full_travel_pos = np.zeros((0, 3), dtype=np.float32)
            self._full_travel_color = np.zeros((0, 4), dtype=np.float32)
            
            # Layer indices
            self._print_layer_indices = []
            self._travel_layer_indices = []
            
            # Physics time arrays
            self._layer_durations = []
            self._move_cum_times = [] # List of numpy arrays, one per layer
            self._print_cum_times = [] # same
            self._travel_cum_times = [] # same

        def mouseMoveEvent(self, ev):
            # Invert the default PyQtGraph orbit movement for standard CAD feel
            lpos = ev.position() if hasattr(ev, 'position') else ev.localPos()
            if self._last_mouse_pos is None:
                self._last_mouse_pos = lpos
            diff = lpos - self._last_mouse_pos
            self._last_mouse_pos = lpos
            
            # Use Qt.MouseButton.LeftButton for PyQt6
            import PyQt6.QtCore as QtCore
            if ev.buttons() == QtCore.Qt.MouseButton.LeftButton:
                if (ev.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier):
                    self.pan(diff.x(), diff.y(), 0, relative='view')
                else:
                    # Inverted from PyQtGraph default (-diff.x, diff.y)
                    self.orbit(diff.x(), -diff.y())
            elif ev.buttons() == QtCore.Qt.MouseButton.MiddleButton:
                if (ev.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier):
                    self.pan(diff.x(), 0, diff.y(), relative='view-upright')
                else:
                    self.pan(diff.x(), diff.y(), 0, relative='view-upright')

        def mouseReleaseEvent(self, ev):
            super().mouseReleaseEvent(ev)
            self._last_mouse_pos = None

        def get_current_layer_duration(self):
            if 0 <= self._current_layer < len(self._layer_durations):
                return self._layer_durations[self._current_layer]
            return 0.0
            
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
            
            self._layer_durations = []
            self._move_cum_times = []
            self._print_cum_times = []
            self._travel_cum_times = []
            
            for layer in self._all_moves:
                layer_t = 0.0
                layer_times = []
                p_times = []
                t_times = []
                
                for m in layer:
                    dur = m.get('duration', 0.0)
                    layer_t += dur
                    layer_times.append(layer_t)
                    
                    x1, y1, z1 = m.get('x1',0), m.get('y1',0), m.get('z1',0)
                    x2, y2, z2 = m.get('x2',0), m.get('y2',0), m.get('z2',0)
                    
                    if m.get('type') == 'travel':
                        t_times.append(layer_t)
                        travel_pos.extend([[x1, y1, z1], [x2, y2, z2]])
                    else:
                        p_times.append(layer_t)
                        print_pos.extend([[x1, y1, z1], [x2, y2, z2]])
                        vpi = m.get('vpi', 0.0)
                        qcolor = Theme.pressure_color(vpi)
                        r, g, b, a = qcolor.redF(), qcolor.greenF(), qcolor.blueF(), qcolor.alphaF()
                        print_color.extend([[r, g, b, a], [r, g, b, a]])
                        
                self._print_layer_indices.append(len(print_pos))
                self._travel_layer_indices.append(len(travel_pos))
                
                self._layer_durations.append(layer_t)
                self._move_cum_times.append(np.array(layer_times, dtype=np.float32))
                self._print_cum_times.append(np.array(p_times, dtype=np.float32))
                self._travel_cum_times.append(np.array(t_times, dtype=np.float32))
                
            self._full_print_pos = np.array(print_pos, dtype=np.float32)
            self._full_print_color = np.array(print_color, dtype=np.float32)
            self._full_travel_pos = np.array(travel_pos, dtype=np.float32)
            
            if travel_pos:
                travel_c = QColor(Theme.TEXT_MUTED)
                tc = [travel_c.redF(), travel_c.greenF(), travel_c.blueF(), 0.5]
                self._full_travel_color = np.tile(tc, (len(travel_pos), 1)).astype(np.float32)
            else:
                self._full_travel_color = np.zeros((0, 4), dtype=np.float32)
                
            # Update grid to encompass the print bounds
            if len(self._full_print_pos) > 0:
                min_x = np.min(self._full_print_pos[:, 0])
                max_x = np.max(self._full_print_pos[:, 0])
                min_y = np.min(self._full_print_pos[:, 1])
                max_y = np.max(self._full_print_pos[:, 1])
                
                cx = (min_x + max_x) / 2
                cy = (min_y + max_y) / 2
                
                # Make the grid a multiple of 50, larger than the print
                size_x = max(int(max_x - min_x + 100), 200)
                size_y = max(int(max_y - min_y + 100), 200)
                
                import PyQt6.QtGui as QtGui
                # Size takes QtGui.QVector3D according to Pyqtgraph's GLGridItem, 
                # but older versions just take x,y,z or Vector.
                import pyqtgraph as pg
                self._grid_item.setSize(x=size_x, y=size_y, z=1)
                self._grid_item.setSpacing(x=10, y=10, z=1)
                
                self._grid_item.resetTransform()
                self._grid_item.translate(cx, cy, 0)
            else:
                self._grid_item.setSize(x=200, y=200, z=1)
                self._grid_item.setSpacing(x=10, y=10, z=1)
                self._grid_item.resetTransform()

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
            if self._current_layer >= len(self._all_moves) or self._current_layer < 0:
                self._print_item.setData(pos=np.zeros((0,3), dtype=np.float32), color=np.zeros((0,4), dtype=np.float32))
                self._travel_item.setData(pos=np.zeros((0,3), dtype=np.float32), color=np.zeros((0,4), dtype=np.float32))
                self._nozzle_item.setData(pos=np.zeros((0,3), dtype=np.float32))
                return
                
            prev_p_idx = self._print_layer_indices[self._current_layer - 1] if self._current_layer > 0 else 0
            prev_t_idx = self._travel_layer_indices[self._current_layer - 1] if self._current_layer > 0 else 0
            
            p_idx = self._print_layer_indices[self._current_layer]
            t_idx = self._travel_layer_indices[self._current_layer]
            
            is_simulating = (0 <= self._sim_time_sec < self.get_current_layer_duration() - 0.001)
            
            if is_simulating:
                t = self._sim_time_sec
                
                # Find which move we are in
                move_idx = np.searchsorted(self._move_cum_times[self._current_layer], t)
                if move_idx >= len(self._all_moves[self._current_layer]):
                    move_idx = len(self._all_moves[self._current_layer]) - 1
                
                # Find how many print/travel moves are fully completed
                p_count = np.searchsorted(self._print_cum_times[self._current_layer], t) * 2
                t_count = np.searchsorted(self._travel_cum_times[self._current_layer], t) * 2
                
                p_idx = prev_p_idx + p_count
                t_idx = prev_t_idx + t_count
                
                m = self._all_moves[self._current_layer][move_idx]
                
                # Interpolate nozzle position
                start_t = self._move_cum_times[self._current_layer][move_idx - 1] if move_idx > 0 else 0.0
                end_t = self._move_cum_times[self._current_layer][move_idx]
                duration = max(end_t - start_t, 0.0001)
                frac = (t - start_t) / duration
                frac = max(0.0, min(1.0, frac))
                
                x1, y1, z1 = m.get('x1',0), m.get('y1',0), m.get('z1',0)
                x2, y2, z2 = m.get('x2',0), m.get('y2',0), m.get('z2',0)
                
                nx = x1 + (x2 - x1) * frac
                ny = y1 + (y2 - y1) * frac
                nz = z1 + (z2 - z1) * frac
                
                # We need to append the partial move to the array data
                # But PyQTGraph setData is fast, so we can just concat the partial line dynamically
                partial_pos = np.array([[x1, y1, z1], [nx, ny, nz]], dtype=np.float32)
                
                if m.get('type') == 'travel':
                    # Has partial travel
                    t_pos = np.concatenate((self._full_travel_pos[:t_idx], partial_pos)) if t_idx > 0 else partial_pos
                    tc = [Theme.TEXT_MUTED_QCOLOR.redF(), Theme.TEXT_MUTED_QCOLOR.greenF(), Theme.TEXT_MUTED_QCOLOR.blueF(), 0.5]
                    t_col = np.concatenate((self._full_travel_color[:t_idx], np.tile(tc, (2,1)).astype(np.float32))) if t_idx > 0 else np.tile(tc, (2,1)).astype(np.float32)
                    
                    self._travel_item.setData(pos=t_pos, color=t_col)
                    if p_idx > 0:
                        self._print_item.setData(pos=self._full_print_pos[:p_idx], color=self._full_print_color[:p_idx])
                    else:
                        self._print_item.setData(pos=np.zeros((0,3), dtype=np.float32), color=np.zeros((0,4), dtype=np.float32))
                else:
                    # Has partial print
                    p_pos = np.concatenate((self._full_print_pos[:p_idx], partial_pos)) if p_idx > 0 else partial_pos
                    qcolor = Theme.pressure_color(m.get('vpi', 0.0))
                    pc = [qcolor.redF(), qcolor.greenF(), qcolor.blueF(), qcolor.alphaF()]
                    p_col = np.concatenate((self._full_print_color[:p_idx], np.tile(pc, (2,1)).astype(np.float32))) if p_idx > 0 else np.tile(pc, (2,1)).astype(np.float32)
                    
                    self._print_item.setData(pos=p_pos, color=p_col)
                    if t_idx > 0:
                        self._travel_item.setData(pos=self._full_travel_pos[:t_idx], color=self._full_travel_color[:t_idx])
                    else:
                        self._travel_item.setData(pos=np.zeros((0,3), dtype=np.float32), color=np.zeros((0,4), dtype=np.float32))

                nc = QColor(Theme.SUCCESS)
                self._nozzle_item.setData(pos=np.array([[nx, ny, nz]], dtype=np.float32), 
                                          color=np.array([[nc.redF(), nc.greenF(), nc.blueF(), 1.0]], dtype=np.float32))
            else:
                # Show full layer
                if p_idx > 0:
                    self._print_item.setData(pos=self._full_print_pos[:p_idx], color=self._full_print_color[:p_idx])
                else:
                    self._print_item.setData(pos=np.zeros((0,3), dtype=np.float32), color=np.zeros((0,4), dtype=np.float32))
                    
                if t_idx > 0:
                    self._travel_item.setData(pos=self._full_travel_pos[:t_idx], color=self._full_travel_color[:t_idx])
                else:
                    self._travel_item.setData(pos=np.zeros((0,3), dtype=np.float32), color=np.zeros((0,4), dtype=np.float32))
                    
                # Nozzle at the very end
                if len(self._all_moves[self._current_layer]) > 0:
                    last_m = self._all_moves[self._current_layer][-1]
                    nx, ny, nz = last_m.get('x2',0), last_m.get('y2',0), last_m.get('z2',0)
                    nc = QColor(Theme.SUCCESS)
                    self._nozzle_item.setData(pos=np.array([[nx, ny, nz]], dtype=np.float32), 
                                              color=np.array([[nc.redF(), nc.greenF(), nc.blueF(), 1.0]], dtype=np.float32))
                else:
                    self._nozzle_item.setData(pos=np.zeros((0,3), dtype=np.float32))

            if p_idx > 0:
                self._print_item.setData(pos=self._full_print_pos[:p_idx], color=self._full_print_color[:p_idx])
            else:
                self._print_item.setData(pos=np.zeros((0,3), dtype=np.float32), color=np.zeros((0,4), dtype=np.float32))
                
            if t_idx > 0:
                self._travel_item.setData(pos=self._full_travel_pos[:t_idx], color=self._full_travel_color[:t_idx])
            else:
                self._travel_item.setData(pos=np.zeros((0,3), dtype=np.float32), color=np.zeros((0,4), dtype=np.float32))
