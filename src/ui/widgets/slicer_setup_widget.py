import os
import json
import glob
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, 
    QComboBox, QLineEdit, QStackedWidget, QRadioButton, QButtonGroup,
    QSpinBox, QFormLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDoubleValidator
from src.ui.theme import Theme

MACHINES_DIR = os.path.join("src", "profiles", "machines")

class SlicerSetupWidget(QWidget):
    """
    Setup wizard for the Slicer module.
    Allows selecting an existing machine profile or customizing a new one.
    """
    # Signal emitted when setup is complete. Passes (width, depth, height).
    setup_complete = pyqtSignal(float, float, float)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {Theme.BG_PRIMARY};")
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.stack = QStackedWidget()
        
        # --- Page 1: Select Machine ---
        self.select_page = QFrame()
        self._init_select_page()
        self.stack.addWidget(self.select_page)
        
        # --- Page 2: Customize Machine ---
        self.custom_page = QFrame()
        self._init_custom_page()
        self.stack.addWidget(self.custom_page)
        
        layout.addWidget(self.stack)
        self.refresh_profiles()

    def _init_select_page(self):
        layout = QVBoxLayout(self.select_page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)
        
        title = QLabel("Select 3D Printer")
        title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 28px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Dropdown
        self.machine_combo = QComboBox()
        self.machine_combo.setFixedSize(300, 40)
        self.machine_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {Theme.BG_TERTIARY};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
                padding: 5px 10px;
                font-size: 16px;
            }}
            QComboBox::drop-down {{ border: none; }}
        """)
        layout.addWidget(self.machine_combo, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        
        self.customize_btn = QPushButton("Customize New")
        self.customize_btn.setFixedSize(140, 40)
        self.customize_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.customize_btn.setStyleSheet(self._btn_style(primary=False))
        self.customize_btn.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        
        self.continue_btn = QPushButton("Continue")
        self.continue_btn.setFixedSize(140, 40)
        self.continue_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.continue_btn.setStyleSheet(self._btn_style(primary=True))
        self.continue_btn.clicked.connect(self._on_continue_clicked)
        
        btn_layout.addWidget(self.customize_btn)
        btn_layout.addWidget(self.continue_btn)
        layout.addLayout(btn_layout)

    def _init_custom_page(self):
        layout = QVBoxLayout(self.custom_page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)
        
        title = QLabel("Customize Machine")
        title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 24px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        form_frame = QFrame()
        form_frame.setFixedWidth(400)
        form_frame.setStyleSheet(f"background-color: {Theme.BG_SECONDARY}; border-radius: 8px; padding: 20px;")
        form_layout = QFormLayout(form_frame)
        form_layout.setSpacing(15)
        
        label_style = f"color: {Theme.TEXT_PRIMARY}; font-size: 14px;"
        input_style = f"""
            QLineEdit, QComboBox, QSpinBox {{
                background-color: {Theme.BG_TERTIARY};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 4px;
                padding: 6px;
                font-size: 14px;
                min-height: 26px;
            }}
        """
        
        # Machine Name
        self.name_input = QLineEdit()
        self.name_input.setStyleSheet(input_style)
        l_name = QLabel("Machine Name:")
        l_name.setStyleSheet(label_style)
        form_layout.addRow(l_name, self.name_input)
        
        # Bed Dimensions
        dim_layout = QHBoxLayout()
        self.x_input = QLineEdit("300")
        self.y_input = QLineEdit("300")
        self.z_input = QLineEdit("400")
        for inp in [self.x_input, self.y_input, self.z_input]:
            inp.setValidator(QDoubleValidator(1.0, 10000.0, 2))
            inp.setStyleSheet(input_style)
            dim_layout.addWidget(inp)
            
        l_dim = QLabel("Bed (X, Y, Z) mm:")
        l_dim.setStyleSheet(label_style)
        form_layout.addRow(l_dim, dim_layout)
        
        # Kinematics
        self.kinematics_combo = QComboBox()
        self.kinematics_combo.addItems(["Cartesian", "CoreXY", "Delta", "Robotic Arm"])
        self.kinematics_combo.setStyleSheet(input_style)
        l_kin = QLabel("Kinematics:")
        l_kin.setStyleSheet(label_style)
        form_layout.addRow(l_kin, self.kinematics_combo)
        
        # Extruder Type
        ext_layout = QHBoxLayout()
        self.rad_filament = QRadioButton("Filament")
        self.rad_pellet = QRadioButton("Pellet")
        self.rad_filament.setStyleSheet(label_style)
        self.rad_pellet.setStyleSheet(label_style)
        self.rad_filament.setChecked(True)
        ext_group = QButtonGroup(self)
        ext_group.addButton(self.rad_filament)
        ext_group.addButton(self.rad_pellet)
        ext_layout.addWidget(self.rad_filament)
        ext_layout.addWidget(self.rad_pellet)
        l_ext = QLabel("Extruder Type:")
        l_ext.setStyleSheet(label_style)
        form_layout.addRow(l_ext, ext_layout)
        
        # Heating Zones (Only for Pellet)
        self.zones_spin = QSpinBox()
        self.zones_spin.setRange(1, 10)
        self.zones_spin.setStyleSheet(input_style)
        self.l_zones = QLabel("Heating Zones:")
        self.l_zones.setStyleSheet(label_style)
        form_layout.addRow(self.l_zones, self.zones_spin)
        
        # Toggle zones visibility based on radio
        self.zones_spin.hide()
        self.l_zones.hide()
        self.rad_pellet.toggled.connect(self._on_extruder_toggled)
        
        layout.addWidget(form_frame, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setFixedSize(140, 40)
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.setStyleSheet(self._btn_style(primary=False))
        self.cancel_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        
        self.save_btn = QPushButton("Save Machine")
        self.save_btn.setFixedSize(140, 40)
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.setStyleSheet(self._btn_style(primary=True))
        self.save_btn.clicked.connect(self._save_machine)
        
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)

    def _btn_style(self, primary=True):
        if primary:
            return f"""
                QPushButton {{
                    background: qlineargradient(
                        x1:0, y1:0, x2:1, y2:0,
                        stop:0 {Theme.ACCENT_GRADIENT_START},
                        stop:1 {Theme.ACCENT_GRADIENT_END}
                    );
                    color: white; font-weight: bold; font-size: 14px;
                    border-radius: 6px; border: none;
                }}
                QPushButton:hover {{
                    background: qlineargradient(
                        x1:0, y1:0, x2:1, y2:0,
                        stop:0 #5b9af6, stop:1 #a57cf6
                    );
                }}
            """
        else:
            return f"""
                QPushButton {{
                    background-color: {Theme.BG_TERTIARY};
                    color: {Theme.TEXT_PRIMARY}; font-weight: bold; font-size: 14px;
                    border: 1px solid {Theme.BORDER}; border-radius: 6px;
                }}
                QPushButton:hover {{
                    background-color: {Theme.BG_ELEVATED};
                }}
            """

    def _on_extruder_toggled(self, is_pellet):
        if is_pellet:
            self.l_zones.show()
            self.zones_spin.show()
        else:
            self.l_zones.hide()
            self.zones_spin.hide()

    def refresh_profiles(self):
        self.machine_combo.clear()
        self.profiles = {}
        
        if not os.path.exists(MACHINES_DIR):
            os.makedirs(MACHINES_DIR, exist_ok=True)
            
        for filepath in glob.glob(os.path.join(MACHINES_DIR, "*.json")):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    name = data.get("name", "Unknown")
                    self.profiles[name] = data
                    self.machine_combo.addItem(name)
            except Exception:
                pass

    def _save_machine(self):
        name = self.name_input.text().strip()
        if not name:
            return
            
        try:
            x = float(self.x_input.text())
            y = float(self.y_input.text())
            z = float(self.z_input.text())
        except ValueError:
            return
            
        is_pellet = self.rad_pellet.isChecked()
        
        profile = {
            "name": name,
            "id": name.lower().replace(" ", "_"),
            "build_volume": {"x": x, "y": y, "z": z},
            "kinematics": self.kinematics_combo.currentText(),
            "extruder_type": "pellet" if is_pellet else "filament",
            "nozzle_diameter": 0.4,
            "layer_height": 0.2,
            "extrusion_width": 0.45
        }
        
        if is_pellet:
            profile["heating_zones"] = self.zones_spin.value()
            
        filename = f"{profile['id']}.json"
        filepath = os.path.join(MACHINES_DIR, filename)
        
        with open(filepath, 'w') as f:
            json.dump(profile, f, indent=2)
            
        self.refresh_profiles()
        
        # Select the newly created profile
        idx = self.machine_combo.findText(name)
        if idx >= 0:
            self.machine_combo.setCurrentIndex(idx)
            
        self.stack.setCurrentIndex(0)
        
    def _on_continue_clicked(self):
        name = self.machine_combo.currentText()
        if name in self.profiles:
            bv = self.profiles[name].get("build_volume", {"x": 300, "y": 300, "z": 400})
            self.setup_complete.emit(float(bv["x"]), float(bv["y"]), float(bv["z"]))
