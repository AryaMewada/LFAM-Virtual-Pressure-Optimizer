"""
Pressure chart widget for visualizing VPI (Volumetric Pressure Index) distribution
across G-code moves. Displays original and optimized pressure data with interactive
hover tooltips, threshold lines, and hotspot region highlighting.
"""

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QWidget, QToolTip
from PyQt6.QtCore import Qt, QRect, QPoint, QRectF
from PyQt6.QtGui import (
    QPainter, QPen, QColor, QFont, QFontMetrics,
    QPainterPath, QBrush, QPolygonF
)

from src.ui.theme import Theme


class PressureChartWidget(QFrame):
    """Widget displaying a pressure distribution chart with original and optimized data."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(280)
        self.setStyleSheet(f"""
            PressureChartWidget {{
                background-color: {Theme.BG_SECONDARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 8px;
            }}
        """)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        # Title label
        title_label = QLabel("Pressure Distribution")
        title_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; border: none; background: transparent;")
        layout.addWidget(title_label)

        # Chart canvas
        self._canvas = self._PressureCanvas(self)
        layout.addWidget(self._canvas, 1)

    def set_data(self, original_vpis: list, optimized_vpis: list = None):
        """Set pressure data on the chart.

        Args:
            original_vpis: List of VPI float values for the original toolpath.
            optimized_vpis: Optional list of VPI float values for the optimized toolpath.
        """
        self._canvas._original_data = list(original_vpis) if original_vpis else []
        self._canvas._optimized_data = list(optimized_vpis) if optimized_vpis else []
        self._canvas._hover_index = -1
        self._canvas.update()

    class _PressureCanvas(QWidget):
        """Inner canvas widget that renders the pressure chart."""

        def __init__(self, parent=None):
            super().__init__(parent)
            self.setMinimumHeight(220)
            self.setMouseTracking(True)

            self._original_data: list[float] = []
            self._optimized_data: list[float] = []
            self._hover_index: int = -1

            # Chart margins
            self._margin_left = 60
            self._margin_right = 20
            self._margin_top = 20
            self._margin_bottom = 35

            self.setStyleSheet("background: transparent; border: none;")

        def _chart_rect(self) -> QRect:
            """Return the drawable chart area within the widget."""
            return QRect(
                self._margin_left,
                self._margin_top,
                self.width() - self._margin_left - self._margin_right,
                self.height() - self._margin_top - self._margin_bottom
            )

        def _map_to_chart(self, index: int, vpi: float) -> tuple[float, float]:
            """Map data coordinates to pixel coordinates within the chart rect.

            Args:
                index: Move index (0-based).
                vpi: VPI value (0.0 to 1.0).

            Returns:
                Tuple of (x_pixel, y_pixel).
            """
            cr = self._chart_rect()
            n = max(len(self._original_data), 1)
            x = cr.x() + (index / max(n - 1, 1)) * cr.width()
            y = cr.y() + cr.height() - (vpi * cr.height())
            return (x, y)

        def paintEvent(self, event):
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            cr = self._chart_rect()

            # If no data, show placeholder message
            if not self._original_data:
                painter.setPen(QColor(Theme.TEXT_MUTED))
                painter.setFont(QFont("Segoe UI", 11))
                painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No pressure data available")
                painter.end()
                return

            # Draw chart background
            painter.fillRect(cr, QColor(Theme.BG_TERTIARY))

            n = len(self._original_data)

            # --- Draw grid lines ---
            grid_color = QColor(Theme.TEXT_MUTED)
            grid_color.setAlpha(40)
            grid_pen = QPen(grid_color, 1, Qt.PenStyle.SolidLine)
            painter.setPen(grid_pen)

            y_values = [0.0, 0.25, 0.5, 0.75, 1.0]
            for yv in y_values:
                _, py = self._map_to_chart(0, yv)
                painter.drawLine(
                    QPoint(cr.x(), int(py)),
                    QPoint(cr.x() + cr.width(), int(py))
                )

            # --- Draw Y-axis labels ---
            label_font = QFont("Segoe UI", 9)
            painter.setFont(label_font)
            painter.setPen(QColor(Theme.TEXT_MUTED))
            fm = QFontMetrics(label_font)

            for yv in y_values:
                _, py = self._map_to_chart(0, yv)
                label_text = f"{yv:.2f}" if yv not in (0.0, 1.0) else f"{yv:.1f}"
                text_rect = QRect(
                    0,
                    int(py) - fm.height() // 2,
                    self._margin_left - 8,
                    fm.height()
                )
                painter.drawText(text_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, label_text)

            # --- Draw X-axis tick marks ---
            if n > 1:
                # Calculate a reasonable tick interval
                tick_interval = max(1, n // 8)
                # Round to a nice number
                for nice in [1, 2, 5, 10, 20, 25, 50, 100, 200, 500, 1000, 2000, 5000]:
                    if nice >= tick_interval:
                        tick_interval = nice
                        break

                painter.setPen(QColor(Theme.TEXT_MUTED))
                painter.setFont(label_font)

                for i in range(0, n, tick_interval):
                    px, _ = self._map_to_chart(i, 0.0)
                    # Tick mark
                    painter.drawLine(
                        QPoint(int(px), cr.y() + cr.height()),
                        QPoint(int(px), cr.y() + cr.height() + 4)
                    )
                    # Label
                    tick_text = str(i)
                    tw = fm.horizontalAdvance(tick_text)
                    painter.drawText(
                        QPoint(int(px) - tw // 2, cr.y() + cr.height() + 4 + fm.height()),
                        tick_text
                    )

            # --- Draw threshold line at y=0.7 ---
            _, threshold_y = self._map_to_chart(0, 0.7)
            threshold_pen = QPen(QColor(Theme.DANGER), 1, Qt.PenStyle.DashLine)
            threshold_pen.setDashPattern([4, 4])
            painter.setPen(threshold_pen)
            painter.drawLine(
                QPoint(cr.x(), int(threshold_y)),
                QPoint(cr.x() + cr.width(), int(threshold_y))
            )
            # Threshold label on right
            painter.setPen(QColor(Theme.DANGER))
            painter.setFont(QFont("Segoe UI", 8))
            painter.drawText(
                QPoint(cr.x() + cr.width() + 3, int(threshold_y) + 4),
                "0.7"
            )

            # --- Draw hotspot regions (VPI > 0.7) ---
            hotspot_color = QColor(Theme.DANGER)
            hotspot_color.setAlpha(30)
            i = 0
            while i < n:
                if self._original_data[i] > 0.7:
                    start_i = i
                    while i < n and self._original_data[i] > 0.7:
                        i += 1
                    end_i = i - 1
                    x_start, _ = self._map_to_chart(start_i, 1.0)
                    x_end, _ = self._map_to_chart(end_i, 1.0)
                    # Ensure at least 1px wide
                    rect_width = max(x_end - x_start, 1.0)
                    painter.fillRect(
                        QRectF(x_start, cr.y(), rect_width, cr.height()),
                        hotspot_color
                    )
                else:
                    i += 1

            # --- Draw original data line ---
            if n > 1:
                original_color = QColor('#ef4444')
                original_color.setAlpha(180)
                original_pen = QPen(original_color, 2)
                painter.setPen(original_pen)
                painter.setBrush(Qt.BrushStyle.NoBrush)

                path = QPainterPath()
                px0, py0 = self._map_to_chart(0, max(0.0, min(1.0, self._original_data[0])))
                path.moveTo(px0, py0)
                
                step = max(1, n // 1500)
                for idx in range(1, n, step):
                    chunk = self._original_data[idx:idx+step]
                    vpi_clamped = max(0.0, min(1.0, max(chunk)))
                    px, py = self._map_to_chart(idx, vpi_clamped)
                    path.lineTo(px, py)
                painter.drawPath(path)

            # --- Draw optimized data line ---
            has_optimized = len(self._optimized_data) > 0
            if has_optimized:
                opt_n = len(self._optimized_data)
                optimized_pen = QPen(QColor(Theme.ACCENT_PRIMARY), 2)
                painter.setPen(optimized_pen)
                painter.setBrush(Qt.BrushStyle.NoBrush)

                opt_path = QPainterPath()
                px0, py0 = self._map_to_chart(0, max(0.0, min(1.0, self._optimized_data[0])))
                opt_path.moveTo(px0, py0)
                
                step = max(1, opt_n // 1500)
                for idx in range(1, opt_n, step):
                    chunk = self._optimized_data[idx:idx+step]
                    vpi_clamped = max(0.0, min(1.0, max(chunk)))
                    px, py = self._map_to_chart(idx, vpi_clamped)
                    opt_path.lineTo(px, py)
                painter.drawPath(opt_path)

            # --- Draw legend in top-right ---
            legend_font = QFont("Segoe UI", 9)
            painter.setFont(legend_font)
            lfm = QFontMetrics(legend_font)

            legend_items = []
            legend_items.append(("Original", QColor('#ef4444')))
            if has_optimized:
                legend_items.append(("Optimized", QColor(Theme.ACCENT_PRIMARY)))

            legend_padding = 8
            legend_line_width = 18
            legend_spacing = 6
            legend_item_height = lfm.height() + 4
            legend_total_height = len(legend_items) * legend_item_height + legend_padding * 2
            legend_max_text_width = max(lfm.horizontalAdvance(item[0]) for item in legend_items)
            legend_total_width = legend_padding * 2 + legend_line_width + legend_spacing + legend_max_text_width

            legend_x = cr.x() + cr.width() - legend_total_width - 8
            legend_y = cr.y() + 8

            # Legend background
            legend_bg = QColor(Theme.BG_ELEVATED)
            legend_bg.setAlpha(200)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(legend_bg)
            painter.drawRoundedRect(
                QRectF(legend_x, legend_y, legend_total_width, legend_total_height),
                4, 4
            )

            for li, (label, color) in enumerate(legend_items):
                item_y = legend_y + legend_padding + li * legend_item_height + legend_item_height // 2

                # Colored line
                painter.setPen(QPen(color, 2))
                painter.drawLine(
                    QPoint(int(legend_x + legend_padding), int(item_y)),
                    QPoint(int(legend_x + legend_padding + legend_line_width), int(item_y))
                )

                # Label text
                painter.setPen(QColor(Theme.TEXT_PRIMARY))
                painter.drawText(
                    QPoint(
                        int(legend_x + legend_padding + legend_line_width + legend_spacing),
                        int(item_y + lfm.ascent() // 2 - 1)
                    ),
                    label
                )

            # --- Draw hover indicator ---
            if 0 <= self._hover_index < n:
                hover_vpi = self._original_data[self._hover_index]
                hx, hy = self._map_to_chart(self._hover_index, max(0.0, min(1.0, hover_vpi)))

                # Vertical line
                hover_line_color = QColor(Theme.TEXT_SECONDARY)
                hover_line_color.setAlpha(120)
                painter.setPen(QPen(hover_line_color, 1, Qt.PenStyle.DashLine))
                painter.drawLine(
                    QPoint(int(hx), cr.y()),
                    QPoint(int(hx), cr.y() + cr.height())
                )

                # Dot on original line
                dot_color = QColor('#ef4444')
                painter.setPen(QPen(dot_color, 1))
                painter.setBrush(dot_color)
                painter.drawEllipse(QPoint(int(hx), int(hy)), 4, 4)

                # Dot on optimized line if present
                if has_optimized and self._hover_index < len(self._optimized_data):
                    opt_vpi = self._optimized_data[self._hover_index]
                    _, opt_hy = self._map_to_chart(self._hover_index, max(0.0, min(1.0, opt_vpi)))
                    opt_dot_color = QColor(Theme.ACCENT_PRIMARY)
                    painter.setPen(QPen(opt_dot_color, 1))
                    painter.setBrush(opt_dot_color)
                    painter.drawEllipse(QPoint(int(hx), int(opt_hy)), 4, 4)

                # Tooltip box
                tooltip_font = QFont("Segoe UI", 9)
                painter.setFont(tooltip_font)
                tfm = QFontMetrics(tooltip_font)

                lines = [f"Move: {self._hover_index}", f"VPI: {hover_vpi:.3f}"]
                if has_optimized and self._hover_index < len(self._optimized_data):
                    lines.append(f"Opt: {self._optimized_data[self._hover_index]:.3f}")

                max_line_w = max(tfm.horizontalAdvance(line) for line in lines)
                box_w = max_line_w + 16
                box_h = len(lines) * tfm.height() + 12

                # Position tooltip box near hover point, offset to avoid edges
                box_x = hx + 12
                box_y = hy - box_h - 8
                if box_x + box_w > cr.x() + cr.width():
                    box_x = hx - box_w - 12
                if box_y < cr.y():
                    box_y = hy + 12

                tooltip_bg = QColor(Theme.BG_ELEVATED)
                tooltip_bg.setAlpha(230)
                painter.setPen(QPen(QColor(Theme.BORDER_FOCUS), 1))
                painter.setBrush(tooltip_bg)
                painter.drawRoundedRect(QRectF(box_x, box_y, box_w, box_h), 4, 4)

                painter.setPen(QColor(Theme.TEXT_PRIMARY))
                for li, line_text in enumerate(lines):
                    painter.drawText(
                        QPoint(int(box_x + 8), int(box_y + 8 + (li + 1) * tfm.height() - tfm.descent())),
                        line_text
                    )

            painter.end()

        def mouseMoveEvent(self, event):
            cr = self._chart_rect()
            n = len(self._original_data)
            if n == 0:
                self._hover_index = -1
                self.update()
                return

            pos = event.position() if hasattr(event, 'position') else event.pos()
            mx = pos.x()

            if cr.x() <= mx <= cr.x() + cr.width():
                ratio = (mx - cr.x()) / max(cr.width(), 1)
                index = int(round(ratio * max(n - 1, 0)))
                index = max(0, min(n - 1, index))
                self._hover_index = index

                # Show tooltip
                vpi = self._original_data[index]
                tip = f"Move: {index}\nVPI: {vpi:.3f}"
                if self._optimized_data and index < len(self._optimized_data):
                    tip += f"\nOptimized: {self._optimized_data[index]:.3f}"
                QToolTip.showText(event.globalPosition().toPoint() if hasattr(event, 'globalPosition') else event.globalPos(), tip, self)
            else:
                self._hover_index = -1

            self.update()

        def leaveEvent(self, event):
            self._hover_index = -1
            self.update()

        def resizeEvent(self, event):
            self.update()
