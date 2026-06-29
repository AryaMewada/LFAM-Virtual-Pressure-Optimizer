"""
Profile selector widget for material and machine profiles.
Provides combo boxes with detailed info cards for the selected profiles.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QGridLayout, QSizePolicy
)

from src.ui.theme import Theme


from src.profiles.profile_manager import ProfileManager

# ─── Shared Styles ──────────────────────────────────────────────────

COMBO_STYLE = f"""
    QComboBox {{
        background-color: {Theme.BG_TERTIARY};
        color: {Theme.TEXT_PRIMARY};
        border: 1px solid {Theme.BORDER};
        border-radius: 6px;
        padding: 8px 12px;
        font-size: 12px;
        min-height: 20px;
    }}
    QComboBox:hover {{
        border-color: {Theme.ACCENT_PRIMARY};
    }}
    QComboBox:focus {{
        border-color: {Theme.BORDER_FOCUS};
    }}
    QComboBox::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 28px;
        border-left: 1px solid {Theme.BORDER};
        border-top-right-radius: 6px;
        border-bottom-right-radius: 6px;
    }}
    QComboBox::down-arrow {{
        image: none;
        border: none;
        width: 0;
        height: 0;
    }}
    QComboBox QAbstractItemView {{
        background-color: {Theme.BG_TERTIARY};
        color: {Theme.TEXT_PRIMARY};
        border: 1px solid {Theme.BORDER};
        border-radius: 4px;
        selection-background-color: {Theme.ACCENT_PRIMARY};
        selection-color: {Theme.TEXT_PRIMARY};
        padding: 4px;
        outline: 0;
    }}
"""

class ProfileSelectorWidget(QFrame):
    """
    Widget for selecting material and machine profiles.

    Displays two combo boxes with corresponding info cards that show
    detailed profile specifications. Emits signals when selections change.

    Signals:
        material_changed(dict): Emitted with the selected material dict.
        machine_changed(dict): Emitted with the selected machine dict.
    """

    material_changed = pyqtSignal(dict)
    machine_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('ProfileSelectorWidget')
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.setStyleSheet(f"""
            #ProfileSelectorWidget {{
                background-color: {Theme.BG_SECONDARY};
                border-radius: 12px;
                padding: 4px;
            }}
        """)

        # Load real profiles using ProfileManager
        self.profile_manager = ProfileManager()
        self._materials_map = {m['name']: m for m in self.profile_manager.load_materials()}
        self._machines_map = {m['name']: m for m in self.profile_manager.load_machines()}

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # ── Title ────────────────────────────────────────────────────
        title_label = QLabel('Profile Settings', self)
        title_label.setStyleSheet(
            f'color: {Theme.TEXT_PRIMARY}; font-size: 14pt; font-weight: bold; background: transparent;'
        )
        main_layout.addWidget(title_label)

        # ── Material Section ─────────────────────────────────────────
        material_container = self._create_section_container()
        material_layout = QVBoxLayout(material_container)
        material_layout.setContentsMargins(16, 16, 16, 16)
        material_layout.setSpacing(10)

        material_label = QLabel('Material Profile', material_container)
        material_label.setStyleSheet(
            f'color: {Theme.TEXT_SECONDARY}; font-size: 12px; font-weight: 500; background: transparent;'
        )
        material_layout.addWidget(material_label)

        self._material_combo = QComboBox(material_container)
        self._material_combo.setStyleSheet(COMBO_STYLE)
        self._material_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        for key in self._materials_map:
            self._material_combo.addItem(key)
        material_layout.addWidget(self._material_combo)

        self._material_info_card = self._create_info_card(material_container)
        material_layout.addWidget(self._material_info_card)

        main_layout.addWidget(material_container)

        # ── Machine Section ──────────────────────────────────────────
        machine_container = self._create_section_container()
        machine_layout = QVBoxLayout(machine_container)
        machine_layout.setContentsMargins(16, 16, 16, 16)
        machine_layout.setSpacing(10)

        machine_label = QLabel('Machine Profile', machine_container)
        machine_label.setStyleSheet(
            f'color: {Theme.TEXT_SECONDARY}; font-size: 12px; font-weight: 500; background: transparent;'
        )
        machine_layout.addWidget(machine_label)

        self._machine_combo = QComboBox(machine_container)
        self._machine_combo.setStyleSheet(COMBO_STYLE)
        self._machine_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        for key in self._machines_map:
            self._machine_combo.addItem(key)
        machine_layout.addWidget(self._machine_combo)

        self._machine_info_card = self._create_info_card(machine_container)
        machine_layout.addWidget(self._machine_info_card)

        main_layout.addWidget(machine_container)

        main_layout.addStretch()

        # ── Connect signals ──────────────────────────────────────────
        self._material_combo.currentTextChanged.connect(self._on_material_changed)
        self._machine_combo.currentTextChanged.connect(self._on_machine_changed)

        # ── Initialize info cards and emit signals with first items ───
        if self._material_combo.count() > 0:
            self._on_material_changed(self._material_combo.currentText())
        if self._machine_combo.count() > 0:
            self._on_machine_changed(self._machine_combo.currentText())

    def refresh_profiles(self, select_material: str = None, select_machine: str = None):
        """Reload profiles from disk and update combo boxes."""
        self.profile_manager._load_all_profiles()
        self._materials_map = {m['name']: m for m in self.profile_manager.load_materials()}
        self._machines_map = {m['name']: m for m in self.profile_manager.load_machines()}
        
        self._material_combo.blockSignals(True)
        self._material_combo.clear()
        for key in self._materials_map:
            self._material_combo.addItem(key)
        if select_material:
            idx = self._material_combo.findText(select_material)
            if idx >= 0:
                self._material_combo.setCurrentIndex(idx)
        self._material_combo.blockSignals(False)
        
        self._machine_combo.blockSignals(True)
        self._machine_combo.clear()
        for key in self._machines_map:
            self._machine_combo.addItem(key)
        if select_machine:
            idx = self._machine_combo.findText(select_machine)
            if idx >= 0:
                self._machine_combo.setCurrentIndex(idx)
        self._machine_combo.blockSignals(False)
        
        # Trigger updates
        if self._material_combo.count() > 0:
            self._on_material_changed(self._material_combo.currentText())
        if self._machine_combo.count() > 0:
            self._on_machine_changed(self._machine_combo.currentText())

    # ─── Factory Helpers ─────────────────────────────────────────────

    def _create_section_container(self) -> QFrame:
        """Create a styled section container frame."""
        container = QFrame(self)
        container.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_TERTIARY};
                border-radius: 10px;
                border: 1px solid {Theme.BORDER};
            }}
        """)
        return container

    def _create_info_card(self, parent) -> QFrame:
        """Create a styled info card frame with a grid layout for properties."""
        card = QFrame(parent)
        card.setObjectName('InfoCard')
        card.setStyleSheet(f"""
            #InfoCard {{
                background-color: {Theme.BG_ELEVATED};
                border-radius: 8px;
                border: none;
                padding: 8px;
            }}
        """)
        layout = QGridLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setHorizontalSpacing(16)
        layout.setVerticalSpacing(6)
        return card

    def _clear_grid_layout(self, layout: QGridLayout):
        """Remove all items from a grid layout."""
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def _populate_info_card(self, card: QFrame, properties: list[tuple[str, str]]):
        """
        Populate an info card with property name-value pairs.

        Args:
            card: The info card QFrame with a QGridLayout.
            properties: List of (property_name, property_value) tuples.
        """
        layout = card.layout()
        self._clear_grid_layout(layout)

        for row, (prop_name, prop_value) in enumerate(properties):
            name_label = QLabel(prop_name, card)
            name_label.setStyleSheet(
                f'color: {Theme.TEXT_MUTED}; font-size: 11px; background: transparent; border: none;'
            )
            name_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

            value_label = QLabel(prop_value, card)
            value_label.setStyleSheet(
                f'color: {Theme.TEXT_PRIMARY}; font-size: 11px; font-weight: 500; background: transparent; border: none;'
            )
            value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            layout.addWidget(name_label, row, 0)
            layout.addWidget(value_label, row, 1)

    # ─── Info Card Updaters ──────────────────────────────────────────

    def _update_material_info(self, material_key: str):
        """Update the material info card with the selected material's data."""
        data = self._materials_map.get(material_key)
        if not data:
            return
        properties = [
            ('Name', data.get('name', 'N/A')),
            ('Category', data.get('category', 'N/A')),
            ('Pressure Sensitivity', str(data.get('pressure_sensitivity', 'N/A'))),
            ('Viscosity', str(data.get('flow_characteristics', {}).get('viscosity_index', 'N/A'))),
        ]
        self._populate_info_card(self._material_info_card, properties)

    def _update_machine_info(self, machine_key: str):
        """Update the machine info card with the selected machine's data."""
        data = self._machines_map.get(machine_key)
        if not data:
            return
        properties = [
            ('Name', data.get('name', 'N/A')),
            ('Nozzle', f"{data.get('nozzle_diameter', 'N/A')} mm"),
            ('Layer', f"{data.get('layer_height', 'N/A')} mm"),
            ('Max Feedrate', f"{data.get('max_feedrate', 'N/A')} mm/min"),
        ]
        self._populate_info_card(self._machine_info_card, properties)

    # ─── Signal Handlers ─────────────────────────────────────────────

    def _on_material_changed(self, text: str):
        """Handle material combo box selection change."""
        self._update_material_info(text)
        data = self._materials_map.get(text)
        if data:
            self.material_changed.emit(data)

    def _on_machine_changed(self, text: str):
        """Handle machine combo box selection change."""
        self._update_machine_info(text)
        data = self._machines_map.get(text)
        if data:
            self.machine_changed.emit(data)
