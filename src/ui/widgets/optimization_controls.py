"""
Optimization Controls panel widget for LFAM Optimizer.
Provides slider-based parameter controls, optimize button, and progress bar.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QSpinBox, QCheckBox, QPushButton, QProgressBar,
)

from src.ui.theme import Theme


class OptimizationControls(QFrame):
    """Panel with optimization parameter sliders and action controls."""

    optimize_clicked = pyqtSignal()
    settings_changed = pyqtSignal(dict)

    # slider definitions: (display_name, key, default_value)
    _SLIDER_DEFS = [
        ('Corner Slowdown',  'corner_slowdown',  70),
        ('Curve Adaptation',  'curve_adaptation',  60),
        ('Start Ramp',        'start_ramp',        50),
        ('End Taper',          'end_taper',          50),
        ('Flow Smoothing',    'flow_smoothing',    40),
        ('Speed Smoothing',  'speed_smoothing',  40),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEnabled(False)

        self.setStyleSheet(f"""
            OptimizationControls {{
                background-color: {Theme.BG_SECONDARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 12px;
                padding: 16px;
            }}
            QLabel {{
                background: transparent;
                border: none;
            }}
            QCheckBox {{
                background: transparent;
                border: none;
                spacing: 0px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 2px solid {Theme.BORDER};
                border-radius: 4px;
                background: {Theme.BG_TERTIARY};
            }}
            QCheckBox::indicator:checked {{
                background: {Theme.ACCENT_PRIMARY};
                border-color: {Theme.ACCENT_PRIMARY};
            }}
            QSpinBox {{
                background: {Theme.BG_TERTIARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 4px;
                color: {Theme.TEXT_PRIMARY};
                padding: 4px;
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                background: {Theme.BG_SECONDARY};
                border-radius: 2px;
                margin: 1px;
            }}
            QSpinBox::up-arrow, QSpinBox::down-arrow {{
                width: 8px;
                height: 8px;
            }}
            QProgressBar {{
                background: {Theme.BG_TERTIARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
                text-align: center;
                color: {Theme.TEXT_PRIMARY};
                font-size: 11px;
                height: 22px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Theme.ACCENT_GRADIENT_START},
                    stop:1 {Theme.ACCENT_GRADIENT_END}
                );
                border-radius: 5px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # --- title ---
        title_label = QLabel('Optimization Settings')
        title_label.setStyleSheet(f"""
            font-size: 14pt;
            font-weight: bold;
            color: {Theme.TEXT_PRIMARY};
            padding: 0px;
        """)
        layout.addWidget(title_label)

        # --- slider rows ---
        self._spinboxes: dict[str, QSpinBox] = {}
        self._checkboxes: dict[str, QCheckBox] = {}
        self._value_labels: dict[str, QLabel] = {}

        for display_name, key, default_val in self._SLIDER_DEFS:
            row_layout = QHBoxLayout()
            row_layout.setSpacing(8)

            # checkbox
            cb = QCheckBox()
            cb.setChecked(True)
            cb.setFixedWidth(20)
            row_layout.addWidget(cb)
            self._checkboxes[key] = cb

            # name label
            name_lbl = QLabel(display_name)
            name_lbl.setFixedWidth(130)
            name_lbl.setStyleSheet(f'color: {Theme.TEXT_SECONDARY}; font-size: 12px;')
            row_layout.addWidget(name_lbl)

            # spinbox
            spinbox = QSpinBox()
            spinbox.setRange(0, 100)
            spinbox.setValue(default_val)
            spinbox.setSuffix('%%')
            spinbox.setAlignment(Qt.AlignmentFlag.AlignRight)
            row_layout.addWidget(spinbox)
            self._spinboxes[key] = spinbox



            layout.addLayout(row_layout)

            # --- connections ---
            # Use default argument in lambda to capture the current key
            spinbox.valueChanged.connect(
                lambda v, k=key: self._on_spinbox_changed(k, v)
            )
            cb.toggled.connect(
                lambda checked, k=key: self._on_checkbox_toggled(k, checked)
            )

        # --- separator ---
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFixedHeight(1)
        separator.setStyleSheet(f'background-color: {Theme.BORDER}; border: none;')
        layout.addWidget(separator)

        # --- optimize button ---
        self._optimize_btn = QPushButton('⚡ OPTIMIZE')
        self._optimize_btn.setObjectName('optimizeButton')
        self._optimize_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._optimize_btn.setStyleSheet(f"""
            QPushButton#optimizeButton {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Theme.ACCENT_GRADIENT_START},
                    stop:1 {Theme.ACCENT_GRADIENT_END}
                );
                color: white;
                font-size: 14pt;
                font-weight: bold;
                height: 50px;
                border-radius: 12px;
                border: none;
            }}
            QPushButton#optimizeButton:hover {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5b9af6,
                    stop:1 #a57cf6
                );
            }}
            QPushButton#optimizeButton:pressed {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2b62c6,
                    stop:1 #6b3cb6
                );
            }}
            QPushButton#optimizeButton:disabled {{
                background: {Theme.BG_TERTIARY};
                color: {Theme.TEXT_MUTED};
            }}
        """)
        self._optimize_btn.clicked.connect(self.optimize_clicked.emit)
        layout.addWidget(self._optimize_btn)

        # --- progress bar ---
        self._progress_bar = QProgressBar()
        self._progress_bar.setVisible(False)
        self._progress_bar.setTextVisible(True)
        self._progress_bar.setRange(0, 100)
        layout.addWidget(self._progress_bar)

        layout.addStretch()

    # --------------------------------------------------------- private slots
    def _on_spinbox_changed(self, key: str, value: int):
        self.settings_changed.emit(self.get_settings())

    def _on_checkbox_toggled(self, key: str, checked: bool):
        self._spinboxes[key].setEnabled(checked)
        self.settings_changed.emit(self.get_settings())

    # --------------------------------------------------------- public methods
    def get_settings(self) -> dict:
        """Return current optimization settings as a dictionary."""
        settings = {}
        for key, spinbox in self._spinboxes.items():
            settings[key] = {
                'value': spinbox.value(),
                'enabled': self._checkboxes[key].isChecked(),
            }
        return settings

    def set_defaults(self, material_defaults: dict):
        """Set spinbox values from a dictionary of defaults.

        Expects keys matching slider keys with int values (0-100).
        """
        for key, value in material_defaults.items():
            spinbox = self._spinboxes.get(key)
            if spinbox is not None and isinstance(value, (int, float)):
                spinbox.setValue(int(value))

    def enable_controls(self):
        """Enable the panel and update button styling."""
        self.setEnabled(True)

    def disable_controls(self):
        """Disable the entire panel."""
        self.setEnabled(False)

    def show_progress(self):
        """Show progress bar and disable the optimize button."""
        self._progress_bar.setValue(0)
        self._progress_bar.setVisible(True)
        self._optimize_btn.setEnabled(False)

    def hide_progress(self):
        """Hide progress bar and re-enable the optimize button."""
        self._progress_bar.setVisible(False)
        self._optimize_btn.setEnabled(True)

    def set_progress(self, value: int):
        """Update the progress bar value."""
        self._progress_bar.setValue(value)
