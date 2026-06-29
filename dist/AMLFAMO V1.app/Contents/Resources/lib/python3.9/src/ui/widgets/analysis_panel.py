"""
Toolpath Analysis Panel widget for LFAM Optimizer.
Displays a grid of 8 stat cards with custom-painted icons and values.
"""

from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QPointF
from PyQt6.QtGui import (
    QPainter, QPen, QColor, QFont, QBrush,
    QLinearGradient, QPainterPath, QRadialGradient,
)
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QGridLayout, QLabel

from src.ui.theme import Theme


class StatCard(QFrame):
    """A single stat card with a custom-painted icon, value, and title."""

    def __init__(self, title: str, icon_type: str, parent=None):
        super().__init__(parent)
        self._value = '—'
        self._title = title
        self._icon_type = icon_type
        self._highlight_color = None

        self.setFixedHeight(110)
        self.setMinimumWidth(140)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet('background: transparent; border: none;')

    def set_value(self, value: str, highlight_color: str = None):
        """Update the displayed value and optional highlight color."""
        self._value = value
        self._highlight_color = highlight_color
        self.update()

    # ------------------------------------------------------------------ paint
    def paintEvent(self, event):
        try:
            self._safe_paintEvent(event)
        except Exception as e:
            import traceback
            with open('paintevent_error.txt', 'a') as errf:
                errf.write(f'Error in src/ui/widgets/analysis_panel.py: {str(e)}\n{traceback.format_exc()}\n')

    def _safe_paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect().adjusted(0, 0, -1, -1)
        rf = QRectF(rect)

        # --- background gradient ---
        grad = QLinearGradient(0, 0, 0, rf.height())
        grad.setColorAt(0.0, QColor(Theme.BG_TERTIARY))
        grad.setColorAt(1.0, QColor(Theme.BG_ELEVATED))
        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(rf, 12, 12)

        # --- border ---
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor(Theme.BORDER), 1))
        painter.drawRoundedRect(rf, 12, 12)

        # --- icon ---
        icon_color = QColor(self._highlight_color if self._highlight_color else Theme.ACCENT_PRIMARY)
        self._draw_icon(painter, icon_color)

        # --- value text ---
        value_color = QColor(self._highlight_color if self._highlight_color else Theme.TEXT_PRIMARY)
        font_value = QFont('Segoe UI', 22, QFont.Weight.Bold)
        painter.setFont(font_value)
        painter.setPen(value_color)
        painter.drawText(56, 45, self._value)

        # --- title text ---
        font_title = QFont('Segoe UI', 10)
        painter.setFont(font_title)
        painter.setPen(QColor(Theme.TEXT_SECONDARY))
        painter.drawText(56, 72, self._title)

        painter.end()

    # ----------------------------------------------------------- icon drawing
    def _draw_icon(self, painter: QPainter, color: QColor):
        pen = QPen(color, 2.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        cx = 16.0
        cy = self.height() / 2.0

        if self._icon_type == 'layers':
            # 3 stacked horizontal lines
            for i in range(3):
                y = cy - 10 + i * 10
                painter.drawLine(QPointF(cx - 8, y), QPointF(cx + 12, y))

        elif self._icon_type == 'print':
            # zigzag path
            path = QPainterPath()
            path.moveTo(cx - 8, cy + 8)
            path.lineTo(cx - 2, cy - 8)
            path.lineTo(cx + 4, cy + 8)
            path.lineTo(cx + 12, cy - 8)
            painter.drawPath(path)

        elif self._icon_type == 'travel':
            # dashed diagonal line
            dash_pen = QPen(color, 2.5, Qt.PenStyle.DashLine, Qt.PenCapStyle.RoundCap)
            painter.setPen(dash_pen)
            painter.drawLine(QPointF(cx - 8, cy + 10), QPointF(cx + 12, cy - 10))
            painter.setPen(pen)

        elif self._icon_type == 'corner':
            # angle / corner shape
            path = QPainterPath()
            path.moveTo(cx - 6, cy - 10)
            path.lineTo(cx - 6, cy + 8)
            path.lineTo(cx + 12, cy + 8)
            painter.drawPath(path)

        elif self._icon_type == 'curve':
            # small arc
            arc_rect = QRectF(cx - 10, cy - 10, 24, 20)
            painter.drawArc(arc_rect, 30 * 16, 120 * 16)

        elif self._icon_type == 'hotspot':
            # filled circle with glow
            glow = QRadialGradient(QPointF(cx + 2, cy), 14)
            glow.setColorAt(0.0, QColor(color.red(), color.green(), color.blue(), 90))
            glow.setColorAt(1.0, QColor(color.red(), color.green(), color.blue(), 0))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(glow))
            painter.drawEllipse(QPointF(cx + 2, cy), 14, 14)
            painter.setBrush(QBrush(color))
            painter.drawEllipse(QPointF(cx + 2, cy), 5, 5)
            painter.setPen(pen)

        elif self._icon_type == 'time':
            # clock face
            painter.drawEllipse(QPointF(cx + 2, cy), 10, 10)
            # hour hand
            painter.drawLine(QPointF(cx + 2, cy), QPointF(cx + 2, cy - 7))
            # minute hand
            painter.drawLine(QPointF(cx + 2, cy), QPointF(cx + 8, cy + 2))

        elif self._icon_type == 'flow':
            # wave
            path = QPainterPath()
            path.moveTo(cx - 8, cy)
            path.cubicTo(cx - 4, cy - 10, cx + 0, cy + 10, cx + 4, cy)
            path.cubicTo(cx + 8, cy - 10, cx + 10, cy + 10, cx + 14, cy)
            painter.drawPath(path)


class AnalysisPanel(QFrame):
    """Panel displaying toolpath analysis results in a grid of stat cards."""

    analysis_complete = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setVisible(False)

        self.setStyleSheet(f"""
            AnalysisPanel {{
                background-color: {Theme.BG_SECONDARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 12px;
                padding: 16px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # --- title ---
        title_label = QLabel('Toolpath Analysis')
        title_label.setStyleSheet(f"""
            font-size: 14pt;
            font-weight: bold;
            color: {Theme.TEXT_PRIMARY};
            background: transparent;
            border: none;
            padding: 0px;
        """)
        layout.addWidget(title_label)

        # --- stat card grid ---
        grid = QGridLayout()
        grid.setSpacing(12)

        self._cards: dict[str, StatCard] = {}

        card_defs = [
            ('layers',            'Layers',             'layers'),
            ('print_moves',       'Print Moves',        'print'),
            ('travel_moves',      'Travel Moves',       'travel'),
            ('sharp_corners',     'Sharp Corners',      'corner'),
            ('tight_curves',      'Tight Curves',       'curve'),
            ('pressure_hotspots', 'Pressure Hotspots',  'hotspot'),
            ('est_print_time',    'Est. Print Time',    'time'),
            ('avg_flow_rate',     'Avg Flow Rate',      'flow'),
        ]

        for idx, (key, title, icon) in enumerate(card_defs):
            card = StatCard(title, icon)
            row = idx // 4
            col = idx % 4
            grid.addWidget(card, row, col)
            self._cards[key] = card

        layout.addLayout(grid)
        layout.addStretch()

    # --------------------------------------------------------------- public
    def update_stats(self, report: dict):
        """Update all stat cards from a report dictionary."""
        key_list = [
            'layers', 'print_moves', 'travel_moves', 'sharp_corners',
            'tight_curves', 'pressure_hotspots', 'est_print_time', 'avg_flow_rate',
        ]

        for key in key_list:
            value = report.get(key, '—')
            card = self._cards.get(key)
            if card is None:
                continue
            card.set_value(str(value))

        # conditional highlighting
        sharp = report.get('sharp_corners', 0)
        if isinstance(sharp, (int, float)) and sharp > 50:
            self._cards['sharp_corners'].set_value(str(sharp), Theme.WARNING)

        hotspots = report.get('pressure_hotspots', 0)
        if isinstance(hotspots, (int, float)) and hotspots > 20:
            self._cards['pressure_hotspots'].set_value(str(hotspots), Theme.DANGER)

        self.setVisible(True)
        self.analysis_complete.emit()
