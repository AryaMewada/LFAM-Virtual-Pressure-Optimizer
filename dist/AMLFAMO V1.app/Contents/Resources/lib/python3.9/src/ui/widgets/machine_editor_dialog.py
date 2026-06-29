"""
Dialog for editing machine profiles.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QLineEdit, QDoubleSpinBox, QSpinBox, QPushButton,
    QFormLayout, QMessageBox
)
from PyQt6.QtCore import Qt

from src.ui.theme import Theme

class MachineEditorDialog(QDialog):
    def __init__(self, parent=None, profile_data=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Machine Profile" if profile_data else "New Machine Profile")
        self.setMinimumSize(400, 500)
        self.setStyleSheet(Theme.get_stylesheet())

        self.profile_data = profile_data or {}
        
        # Build UI
        layout = QVBoxLayout(self)
        
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Tabs
        self._build_general_tab()
        self._build_kinematics_tab()
        self._build_extruder_tab()
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_save = QPushButton("Save")
        self.btn_save.setDefault(True)
        self.btn_save.clicked.connect(self.accept)
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)
        
        layout.addLayout(btn_layout)
        
        self._populate_fields()

    def _build_general_tab(self):
        tab = QWidget()
        form = QFormLayout(tab)
        
        self.f_name = QLineEdit()
        self.f_id = QLineEdit()
        if self.profile_data:
            self.f_id.setEnabled(False) # Don't allow changing ID of existing
            
        self.f_description = QLineEdit()
        
        self.f_vol_x = QSpinBox()
        self.f_vol_x.setRange(0, 10000)
        self.f_vol_y = QSpinBox()
        self.f_vol_y.setRange(0, 10000)
        self.f_vol_z = QSpinBox()
        self.f_vol_z.setRange(0, 10000)
        
        self.f_controller = QLineEdit()
        self.f_firmware = QLineEdit()
        
        form.addRow("Name:", self.f_name)
        form.addRow("ID:", self.f_id)
        form.addRow("Description:", self.f_description)
        form.addRow("Build Volume X (mm):", self.f_vol_x)
        form.addRow("Build Volume Y (mm):", self.f_vol_y)
        form.addRow("Build Volume Z (mm):", self.f_vol_z)
        form.addRow("Controller:", self.f_controller)
        form.addRow("Firmware:", self.f_firmware)
        
        self.tabs.addTab(tab, "General")

    def _build_kinematics_tab(self):
        tab = QWidget()
        form = QFormLayout(tab)
        
        self.f_max_feedrate = QDoubleSpinBox()
        self.f_max_feedrate.setRange(0.0, 100000.0)
        
        self.f_max_accel = QDoubleSpinBox()
        self.f_max_accel.setRange(0.0, 10000.0)
        
        form.addRow("Max Feedrate (mm/min):", self.f_max_feedrate)
        form.addRow("Max Acceleration (mm/s²):", self.f_max_accel)
        
        self.tabs.addTab(tab, "Kinematics")
        
    def _build_extruder_tab(self):
        tab = QWidget()
        form = QFormLayout(tab)
        
        self.f_extruder_type = QLineEdit()
        
        self.f_nozzle = QDoubleSpinBox()
        self.f_nozzle.setRange(0.1, 50.0)
        self.f_nozzle.setSingleStep(0.1)
        
        self.f_layer = QDoubleSpinBox()
        self.f_layer.setRange(0.1, 50.0)
        self.f_layer.setSingleStep(0.1)
        
        self.f_ext_width = QDoubleSpinBox()
        self.f_ext_width.setRange(0.1, 50.0)
        self.f_ext_width.setSingleStep(0.1)
        
        self.f_screw_dia = QDoubleSpinBox()
        self.f_screw_dia.setRange(0.0, 100.0)
        
        self.f_rpm_min = QDoubleSpinBox()
        self.f_rpm_min.setRange(0.0, 1000.0)
        self.f_rpm_max = QDoubleSpinBox()
        self.f_rpm_max.setRange(0.0, 1000.0)
        
        form.addRow("Extruder Type:", self.f_extruder_type)
        form.addRow("Nozzle Diameter (mm):", self.f_nozzle)
        form.addRow("Layer Height (mm):", self.f_layer)
        form.addRow("Extrusion Width (mm):", self.f_ext_width)
        form.addRow("Screw Diameter (mm):", self.f_screw_dia)
        form.addRow("Screw RPM Min:", self.f_rpm_min)
        form.addRow("Screw RPM Max:", self.f_rpm_max)
        
        self.tabs.addTab(tab, "Extruder")
        
    def _populate_fields(self):
        d = self.profile_data
        if not d:
            return
            
        self.f_name.setText(d.get('name', ''))
        self.f_id.setText(d.get('id', ''))
        self.f_description.setText(d.get('description', ''))
        
        vol = d.get('build_volume', {})
        self.f_vol_x.setValue(vol.get('x', 1000))
        self.f_vol_y.setValue(vol.get('y', 1000))
        self.f_vol_z.setValue(vol.get('z', 1000))
        
        self.f_controller.setText(d.get('motion_controller', ''))
        self.f_firmware.setText(d.get('firmware', ''))
        
        self.f_max_feedrate.setValue(d.get('max_feedrate', 6000.0))
        self.f_max_accel.setValue(d.get('max_acceleration', 500.0))
        
        self.f_extruder_type.setText(d.get('extruder_type', ''))
        self.f_nozzle.setValue(d.get('nozzle_diameter', 1.0))
        self.f_layer.setValue(d.get('layer_height', 0.5))
        self.f_ext_width.setValue(d.get('extrusion_width', 1.2))
        self.f_screw_dia.setValue(d.get('screw_diameter', 10.0))
        
        rpm = d.get('screw_rpm_limits', {})
        self.f_rpm_min.setValue(rpm.get('min', 0.0))
        self.f_rpm_max.setValue(rpm.get('max', 100.0))

    def get_data(self) -> dict:
        """Construct the machine dict from form fields."""
        return {
            "name": self.f_name.text(),
            "id": self.f_id.text(),
            "description": self.f_description.text(),
            "nozzle_diameter": self.f_nozzle.value(),
            "layer_height": self.f_layer.value(),
            "extrusion_width": self.f_ext_width.value(),
            "screw_diameter": self.f_screw_dia.value(),
            "screw_rpm_limits": {
                "min": self.f_rpm_min.value(),
                "max": self.f_rpm_max.value()
            },
            "max_feedrate": self.f_max_feedrate.value(),
            "max_acceleration": self.f_max_accel.value(),
            "build_volume": {
                "x": self.f_vol_x.value(),
                "y": self.f_vol_y.value(),
                "z": self.f_vol_z.value()
            },
            "motion_controller": self.f_controller.text(),
            "extruder_type": self.f_extruder_type.text(),
            "firmware": self.f_firmware.text()
        }
