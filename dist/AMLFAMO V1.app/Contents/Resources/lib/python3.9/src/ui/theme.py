"""
Theme module for LFAM Optimizer application.
Provides a comprehensive dark theme with color palette, QSS stylesheet,
pressure color interpolation, and gradient utilities.
"""

from PyQt6.QtGui import QColor, QLinearGradient


class Theme:
    """Comprehensive dark theme for the LFAM Optimizer application."""

    # ── Background Colors ──────────────────────────────────────────────
    BG_PRIMARY = '#0d1117'      # Deep rich space gray
    BG_SECONDARY = '#161b22'    # Slightly lighter for panels
    BG_TERTIARY = '#21262d'     # Elevated surfaces
    BG_ELEVATED = '#30363d'     # Borders and hovers

    # ── Accent Colors ──────────────────────────────────────────────────
    ACCENT_PRIMARY = '#58a6ff'    # Bright, legible blue
    ACCENT_SECONDARY = '#79c0ff'  # Lighter hover state
    ACCENT_GRADIENT_START = '#58a6ff'
    ACCENT_GRADIENT_END = '#bc8cff' # Purple for a premium gradient

    # ── Semantic Colors ────────────────────────────────────────────────
    SUCCESS = '#238636'
    WARNING = '#d29922'
    DANGER = '#da3633'

    # ── Text Colors ────────────────────────────────────────────────────
    TEXT_PRIMARY = '#f0f6fc'
    TEXT_SECONDARY = '#8b949e'
    TEXT_MUTED = '#484f58'

    # ── Border Colors ──────────────────────────────────────────────────
    BORDER = '#30363d'
    BORDER_FOCUS = '#58a6ff'

    # ── Pressure Visualization Colors ──────────────────────────────────
    PRESSURE_LOW = '#10b981'
    PRESSURE_MED = '#f59e0b'
    PRESSURE_HIGH = '#ef4444'

    @staticmethod
    def get_stylesheet() -> str:
        """Return the complete QSS stylesheet for the entire application."""
        return f"""
        /* ── QMainWindow ─────────────────────────────────────────── */
        QMainWindow {{
            background-color: {Theme.BG_PRIMARY};
        }}

        /* ── QWidget (base) ──────────────────────────────────────── */
        QWidget {{
            background-color: {Theme.BG_PRIMARY};
            color: {Theme.TEXT_PRIMARY};
            font-family: 'Inter', 'Segoe UI', 'Roboto', 'Helvetica Neue', sans-serif;
            font-size: 14px;
        }}

        /* ── QPushButton ─────────────────────────────────────────── */
        QPushButton {{
            background-color: {Theme.BG_TERTIARY};
            color: {Theme.TEXT_PRIMARY};
            border: 1px solid {Theme.BORDER};
            border-radius: 8px;
            padding: 10px 18px;
            font-weight: 600;
        }}
        QPushButton:hover {{
            background-color: {Theme.BG_ELEVATED};
            border: 1px solid {Theme.TEXT_SECONDARY};
            color: #ffffff;
        }}
        QPushButton:pressed {{
            background-color: {Theme.BG_TERTIARY};
            border: 1px solid {Theme.ACCENT_PRIMARY};
        }}
        QPushButton:disabled {{
            background-color: {Theme.BG_TERTIARY};
            color: {Theme.TEXT_MUTED};
            border: 1px solid {Theme.BORDER};
            opacity: 0.5;
        }}

        /* ── QLabel ──────────────────────────────────────────────── */
        QLabel {{
            background-color: transparent;
            color: {Theme.TEXT_PRIMARY};
            border: none;
        }}

        /* ── QComboBox ───────────────────────────────────────────── */
        QComboBox {{
            background-color: {Theme.BG_TERTIARY};
            color: {Theme.TEXT_PRIMARY};
            border: 1px solid {Theme.BORDER};
            border-radius: 8px;
            padding: 8px 12px;
            min-height: 20px;
        }}
        QComboBox:hover {{
            border: 1px solid {Theme.BORDER_FOCUS};
        }}
        QComboBox::drop-down {{
            border-left: 1px solid {Theme.BORDER};
            width: 30px;
            subcontrol-origin: padding;
            subcontrol-position: top right;
        }}
        QComboBox::down-arrow {{
            width: 0;
            height: 0;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 6px solid {Theme.TEXT_SECONDARY};
        }}
        QComboBox QAbstractItemView {{
            background-color: {Theme.BG_SECONDARY};
            color: {Theme.TEXT_PRIMARY};
            border: 1px solid {Theme.BORDER};
            border-radius: 4px;
            selection-background-color: {Theme.BG_TERTIARY};
            selection-color: {Theme.TEXT_PRIMARY};
            outline: none;
        }}
        QComboBox QAbstractItemView::item {{
            min-height: 30px;
            padding: 4px 12px;
        }}
        QComboBox QAbstractItemView::item:selected {{
            background-color: {Theme.BG_TERTIARY};
            color: {Theme.TEXT_PRIMARY};
        }}

        /* ── QSlider ─────────────────────────────────────────────── */
        QSlider::groove:horizontal {{
            height: 4px;
            background-color: {Theme.BG_TERTIARY};
            border-radius: 2px;
        }}
        QSlider::handle:horizontal {{
            width: 16px;
            height: 16px;
            margin-top: -6px;
            margin-bottom: -6px;
            background-color: {Theme.ACCENT_PRIMARY};
            border-radius: 8px;
        }}
        QSlider::handle:horizontal:hover {{
            background-color: {Theme.ACCENT_SECONDARY};
        }}
        QSlider::sub-page:horizontal {{
            background-color: {Theme.ACCENT_PRIMARY};
            border-radius: 2px;
        }}

        /* ── QProgressBar ────────────────────────────────────────── */
        QProgressBar {{
            height: 8px;
            background-color: {Theme.BG_TERTIARY};
            border-radius: 4px;
            text-align: center;
            color: {Theme.TEXT_MUTED};
            border: none;
        }}
        QProgressBar::chunk {{
            border-radius: 4px;
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 {Theme.ACCENT_PRIMARY},
                stop:1 {Theme.ACCENT_SECONDARY}
            );
        }}

        /* ── QGroupBox ───────────────────────────────────────────── */
        QGroupBox {{
            background-color: {Theme.BG_SECONDARY};
            border: 1px solid {Theme.BORDER};
            border-radius: 12px;
            margin-top: 20px;
            padding-top: 16px;
            font-weight: bold;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 4px 12px;
            color: {Theme.ACCENT_PRIMARY};
            font-weight: bold;
        }}

        /* ── QScrollArea ─────────────────────────────────────────── */
        QScrollArea {{
            background-color: transparent;
            border: none;
        }}
        QScrollArea > QWidget > QWidget {{
            background-color: transparent;
        }}

        /* ── QScrollBar (Vertical) ───────────────────────────────── */
        QScrollBar:vertical {{
            width: 8px;
            background-color: {Theme.BG_SECONDARY};
            border-radius: 4px;
            margin: 0;
        }}
        QScrollBar::handle:vertical {{
            background-color: {Theme.BG_ELEVATED};
            border-radius: 4px;
            min-height: 30px;
        }}
        QScrollBar::handle:vertical:hover {{
            background-color: {Theme.TEXT_MUTED};
        }}
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {{
            height: 0;
            background: none;
        }}
        QScrollBar::add-page:vertical,
        QScrollBar::sub-page:vertical {{
            background: none;
        }}

        /* ── QScrollBar (Horizontal) ─────────────────────────────── */
        QScrollBar:horizontal {{
            height: 8px;
            background-color: {Theme.BG_SECONDARY};
            border-radius: 4px;
            margin: 0;
        }}
        QScrollBar::handle:horizontal {{
            background-color: {Theme.BG_ELEVATED};
            border-radius: 4px;
            min-width: 30px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background-color: {Theme.TEXT_MUTED};
        }}
        QScrollBar::add-line:horizontal,
        QScrollBar::sub-line:horizontal {{
            width: 0;
            background: none;
        }}
        QScrollBar::add-page:horizontal,
        QScrollBar::sub-page:horizontal {{
            background: none;
        }}

        /* ── QFrame ──────────────────────────────────────────────── */
        QFrame {{
            background-color: transparent;
            border: none;
        }}

        /* ── QStatusBar ──────────────────────────────────────────── */
        QStatusBar {{
            background-color: {Theme.BG_SECONDARY};
            border-top: 1px solid {Theme.BORDER};
            color: {Theme.TEXT_SECONDARY};
            padding: 4px;
            font-size: 12px;
        }}
        QStatusBar::item {{
            border: none;
        }}

        /* ── QMenuBar ────────────────────────────────────────────── */
        QMenuBar {{
            background-color: {Theme.BG_SECONDARY};
            color: {Theme.TEXT_SECONDARY};
            padding: 6px 12px;
            border-bottom: 1px solid {Theme.BORDER};
        }}
        QMenuBar::item {{
            background-color: transparent;
            padding: 4px 10px;
            border-radius: 4px;
        }}
        QMenuBar::item:selected {{
            background-color: {Theme.BG_TERTIARY};
            color: {Theme.TEXT_PRIMARY};
        }}

        /* ── QMenu ───────────────────────────────────────────────── */
        QMenu {{
            background-color: {Theme.BG_SECONDARY};
            border: 1px solid {Theme.BORDER};
            border-radius: 8px;
            padding: 4px;
        }}
        QMenu::item {{
            min-height: 30px;
            padding: 12px 24px;
            color: {Theme.TEXT_SECONDARY};
            border-radius: 4px;
        }}
        QMenu::item:selected {{
            background-color: {Theme.BG_TERTIARY};
            color: {Theme.TEXT_PRIMARY};
        }}
        QMenu::separator {{
            height: 1px;
            background-color: {Theme.BG_TERTIARY};
            margin: 4px 8px;
        }}

        /* ── QSplitter ───────────────────────────────────────────── */
        QSplitter::handle {{
            background-color: {Theme.BG_TERTIARY};
            width: 2px;
        }}
        QSplitter::handle:horizontal {{
            width: 2px;
        }}
        QSplitter::handle:vertical {{
            height: 2px;
        }}

        /* ── QTabWidget ──────────────────────────────────────────── */
        QTabWidget::pane {{
            background-color: {Theme.BG_SECONDARY};
            border: 1px solid {Theme.BORDER};
            border-radius: 8px;
        }}
        QTabBar::tab {{
            background-color: {Theme.BG_PRIMARY};
            color: {Theme.TEXT_SECONDARY};
            padding: 10px 20px;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
            margin-right: 4px;
            font-weight: 500;
        }}
        QTabBar::tab:selected {{
            background-color: {Theme.BG_SECONDARY};
            color: {Theme.ACCENT_PRIMARY};
            border-top: 2px solid {Theme.ACCENT_PRIMARY};
            border-left: 1px solid {Theme.BORDER};
            border-right: 1px solid {Theme.BORDER};
        }}
        QTabBar::tab:hover:!selected {{
            background-color: {Theme.BG_TERTIARY};
            color: {Theme.TEXT_PRIMARY};
        }}

        /* ── QFileDialog ─────────────────────────────────────────── */
        QFileDialog {{
            background-color: {Theme.BG_PRIMARY};
            color: {Theme.TEXT_PRIMARY};
        }}
        QFileDialog QLabel {{
            color: {Theme.TEXT_PRIMARY};
        }}
        QFileDialog QLineEdit {{
            background-color: {Theme.BG_TERTIARY};
            color: {Theme.TEXT_PRIMARY};
            border: 1px solid {Theme.BORDER};
            border-radius: 6px;
            padding: 6px 10px;
        }}
        QFileDialog QListView {{
            background-color: {Theme.BG_SECONDARY};
            color: {Theme.TEXT_PRIMARY};
            border: 1px solid {Theme.BORDER};
            border-radius: 6px;
        }}
        QFileDialog QTreeView {{
            background-color: {Theme.BG_SECONDARY};
            color: {Theme.TEXT_PRIMARY};
            border: 1px solid {Theme.BORDER};
            border-radius: 6px;
        }}

        /* ── QCheckBox ───────────────────────────────────────────── */
        QCheckBox {{
            color: {Theme.TEXT_PRIMARY};
            spacing: 8px;
        }}
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            background-color: {Theme.BG_TERTIARY};
            border: 1px solid {Theme.BORDER};
            border-radius: 4px;
        }}
        QCheckBox::indicator:hover {{
            border: 1px solid {Theme.BORDER_FOCUS};
        }}
        QCheckBox::indicator:checked {{
            background-color: {Theme.ACCENT_PRIMARY};
            border: 1px solid {Theme.ACCENT_PRIMARY};
        }}

        /* ── QLineEdit ───────────────────────────────────────────── */
        QLineEdit {{
            background-color: {Theme.BG_TERTIARY};
            color: {Theme.TEXT_PRIMARY};
            border: 1px solid {Theme.BORDER};
            border-radius: 8px;
            padding: 8px 12px;
        }}
        QLineEdit:focus {{
            border: 1px solid {Theme.BORDER_FOCUS};
        }}

        /* ── QSpinBox / QDoubleSpinBox ───────────────────────────── */
        QSpinBox, QDoubleSpinBox {{
            background-color: {Theme.BG_TERTIARY};
            color: {Theme.TEXT_PRIMARY};
            border: 1px solid {Theme.BORDER};
            border-radius: 8px;
            padding: 6px 10px;
        }}
        QSpinBox:focus, QDoubleSpinBox:focus {{
            border: 1px solid {Theme.BORDER_FOCUS};
        }}
        QSpinBox::up-button, QDoubleSpinBox::up-button {{
            subcontrol-origin: border;
            subcontrol-position: top right;
            width: 20px;
            border-left: 1px solid {Theme.BORDER};
            border-bottom: 1px solid {Theme.BORDER};
            border-top-right-radius: 8px;
            background-color: {Theme.BG_TERTIARY};
        }}
        QSpinBox::down-button, QDoubleSpinBox::down-button {{
            subcontrol-origin: border;
            subcontrol-position: bottom right;
            width: 20px;
            border-left: 1px solid {Theme.BORDER};
            border-bottom-right-radius: 8px;
            background-color: {Theme.BG_TERTIARY};
        }}
        QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{
            width: 0;
            height: 0;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-bottom: 5px solid {Theme.TEXT_SECONDARY};
        }}
        QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
            width: 0;
            height: 0;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 5px solid {Theme.TEXT_SECONDARY};
        }}

        /* ── QToolTip ────────────────────────────────────────────── */
        QToolTip {{
            background-color: {Theme.BG_ELEVATED};
            color: {Theme.TEXT_PRIMARY};
            border: 1px solid {Theme.BORDER};
            border-radius: 6px;
            padding: 6px 10px;
            font-size: 12px;
        }}

        /* ── QMessageBox ─────────────────────────────────────────── */
        QMessageBox {{
            background-color: {Theme.BG_PRIMARY};
        }}
        QMessageBox QLabel {{
            color: {Theme.TEXT_PRIMARY};
        }}
        """

    @staticmethod
    def pressure_color(vpi: float) -> QColor:
        """
        Return an interpolated QColor based on a normalized pressure index (0-1).

        0.0 = green (#10b981), 0.5 = yellow (#f59e0b), 1.0 = red (#ef4444).
        Values between are linearly interpolated.

        Args:
            vpi: Volumetric pressure index, clamped to [0, 1].

        Returns:
            QColor representing the pressure level.
        """
        vpi = max(0.0, min(1.0, vpi))

        green = QColor('#10b981')
        yellow = QColor('#f59e0b')
        red = QColor('#ef4444')

        if vpi < 0.5:
            t = vpi * 2.0
            r = int(green.red() + (yellow.red() - green.red()) * t)
            g = int(green.green() + (yellow.green() - green.green()) * t)
            b = int(green.blue() + (yellow.blue() - green.blue()) * t)
        else:
            t = (vpi - 0.5) * 2.0
            r = int(yellow.red() + (red.red() - yellow.red()) * t)
            g = int(yellow.green() + (red.green() - yellow.green()) * t)
            b = int(yellow.blue() + (red.blue() - yellow.blue()) * t)

        return QColor(
            max(0, min(255, r)),
            max(0, min(255, g)),
            max(0, min(255, b)),
        )

    @staticmethod
    def speed_color(normalized_speed: float) -> QColor:
        """
        Return an interpolated QColor for speed.
        0.0 = blue (#3b82f6), 0.5 = purple (#a855f7), 1.0 = hot pink (#ec4899)
        """
        val = max(0.0, min(1.0, normalized_speed))
        c1 = QColor('#3b82f6')
        c2 = QColor('#a855f7')
        c3 = QColor('#ec4899')
        if val < 0.5:
            t = val * 2.0
            return QColor(
                int(c1.red() + (c2.red() - c1.red()) * t),
                int(c1.green() + (c2.green() - c1.green()) * t),
                int(c1.blue() + (c2.blue() - c1.blue()) * t)
            )
        else:
            t = (val - 0.5) * 2.0
            return QColor(
                int(c2.red() + (c3.red() - c2.red()) * t),
                int(c2.green() + (c3.green() - c2.green()) * t),
                int(c2.blue() + (c3.blue() - c2.blue()) * t)
            )

    @staticmethod
    def flow_color(normalized_flow: float) -> QColor:
        """
        Return an interpolated QColor for extrusion flow.
        0.0 = dark blue (#1e3a8a), 0.5 = teal (#14b8a6), 1.0 = bright yellow (#fde047)
        """
        val = max(0.0, min(1.0, normalized_flow))
        c1 = QColor('#1e3a8a')
        c2 = QColor('#14b8a6')
        c3 = QColor('#fde047')
        if val < 0.5:
            t = val * 2.0
            return QColor(
                int(c1.red() + (c2.red() - c1.red()) * t),
                int(c1.green() + (c2.green() - c1.green()) * t),
                int(c1.blue() + (c2.blue() - c1.blue()) * t)
            )
        else:
            t = (val - 0.5) * 2.0
            return QColor(
                int(c2.red() + (c3.red() - c2.red()) * t),
                int(c2.green() + (c3.green() - c2.green()) * t),
                int(c2.blue() + (c3.blue() - c2.blue()) * t)
            )

    @staticmethod
    def create_gradient(start_color: str, end_color: str) -> QLinearGradient:
        """
        Create a horizontal QLinearGradient from start_color to end_color.

        Args:
            start_color: Hex color string for the gradient start (position 0).
            end_color: Hex color string for the gradient end (position 1).

        Returns:
            QLinearGradient configured from (0,0) to (1,0) with the given color stops.
        """
        gradient = QLinearGradient(0, 0, 1, 0)
        gradient.setColorAt(0, QColor(start_color))
        gradient.setColorAt(1, QColor(end_color))
        return gradient
