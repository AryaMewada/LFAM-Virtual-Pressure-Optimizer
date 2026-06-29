"""
Dialog for editing material profiles.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QLineEdit, QDoubleSpinBox, QSpinBox, QPushButton,
    QFormLayout, QMessageBox
)
from PyQt6.QtCore import Qt

from src.ui.theme import Theme

class MaterialEditorDialog(QDialog):
    def __init__(self, parent=None, profile_data=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Material Profile" if profile_data else "New Material Profile")
        self.setMinimumSize(500, 600)
        self.setStyleSheet(Theme.get_stylesheet())

        self.profile_data = profile_data or {}
        
        # Build UI
        layout = QVBoxLayout(self)
        
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Tabs
        self._build_general_tab()
        self._build_thermal_tab()
        self._build_flow_tab()
        self._build_weights_tab()
        self._build_defaults_tab()
        
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
            
        self.f_category = QLineEdit()
        self.f_description = QLineEdit()
        
        form.addRow("Name:", self.f_name)
        form.addRow("ID:", self.f_id)
        form.addRow("Category:", self.f_category)
        form.addRow("Description:", self.f_description)
        
        self.tabs.addTab(tab, "General")

    def _build_thermal_tab(self):
        tab = QWidget()
        form = QFormLayout(tab)
        
        self.f_temp_nozzle = QSpinBox()
        self.f_temp_nozzle.setRange(0, 500)
        self.f_temp_bed = QSpinBox()
        self.f_temp_bed.setRange(0, 200)
        
        self.f_pressure_sens = QDoubleSpinBox()
        self.f_pressure_sens.setRange(0.0, 5.0)
        self.f_pressure_sens.setSingleStep(0.1)
        
        self.f_corner_sens = QDoubleSpinBox()
        self.f_corner_sens.setRange(0.0, 5.0)
        self.f_corner_sens.setSingleStep(0.1)
        
        self.f_curve_sens = QDoubleSpinBox()
        self.f_curve_sens.setRange(0.0, 5.0)
        self.f_curve_sens.setSingleStep(0.1)
        
        self.f_pressure_decay = QDoubleSpinBox()
        self.f_pressure_decay.setRange(0.0, 1.0)
        self.f_pressure_decay.setSingleStep(0.05)
        
        form.addRow("Nozzle Temp (°C):", self.f_temp_nozzle)
        form.addRow("Bed Temp (°C):", self.f_temp_bed)
        form.addRow("Pressure Sensitivity:", self.f_pressure_sens)
        form.addRow("Corner Sensitivity:", self.f_corner_sens)
        form.addRow("Curve Sensitivity:", self.f_curve_sens)
        form.addRow("Pressure Decay:", self.f_pressure_decay)
        
        self.tabs.addTab(tab, "Thermal & Pressure")
        
    def _build_flow_tab(self):
        tab = QWidget()
        form = QFormLayout(tab)
        
        self.f_opt_flow = QDoubleSpinBox()
        self.f_opt_flow.setRange(0.0, 1000.0)
        self.f_max_flow = QDoubleSpinBox()
        self.f_max_flow.setRange(0.0, 1000.0)
        self.f_visc_idx = QDoubleSpinBox()
        self.f_visc_idx.setRange(0.0, 10.0)
        self.f_melt_idx = QDoubleSpinBox()
        self.f_melt_idx.setRange(0.0, 100.0)
        
        form.addRow("Optimal Flow Rate:", self.f_opt_flow)
        form.addRow("Max Flow Rate:", self.f_max_flow)
        form.addRow("Viscosity Index:", self.f_visc_idx)
        form.addRow("Melt Flow Index:", self.f_melt_idx)
        
        self.tabs.addTab(tab, "Flow Characteristics")
        
    def _build_weights_tab(self):
        tab = QWidget()
        form = QFormLayout(tab)
        
        self.f_w_flow = QDoubleSpinBox()
        self.f_w_speed = QDoubleSpinBox()
        self.f_w_corner = QDoubleSpinBox()
        self.f_w_curve = QDoubleSpinBox()
        self.f_w_history = QDoubleSpinBox()
        self.f_w_accel = QDoubleSpinBox()
        self.f_w_startstop = QDoubleSpinBox()
        self.f_w_density = QDoubleSpinBox()
        
        for w in [self.f_w_flow, self.f_w_speed, self.f_w_corner, self.f_w_curve, 
                 self.f_w_history, self.f_w_accel, self.f_w_startstop, self.f_w_density]:
            w.setRange(0.0, 1.0)
            w.setSingleStep(0.05)
            
        form.addRow("Flow Weight:", self.f_w_flow)
        form.addRow("Speed Weight:", self.f_w_speed)
        form.addRow("Corner Weight:", self.f_w_corner)
        form.addRow("Curve Weight:", self.f_w_curve)
        form.addRow("History Weight:", self.f_w_history)
        form.addRow("Accel Weight:", self.f_w_accel)
        form.addRow("Start/Stop Weight:", self.f_w_startstop)
        form.addRow("Density Weight:", self.f_w_density)
        
        self.tabs.addTab(tab, "VPI Weights")
        
    def _build_defaults_tab(self):
        tab = QWidget()
        form = QFormLayout(tab)
        
        self.f_d_corner = QSpinBox()
        self.f_d_curve = QSpinBox()
        self.f_d_start = QSpinBox()
        self.f_d_end = QSpinBox()
        self.f_d_flow = QSpinBox()
        self.f_d_speed = QSpinBox()
        
        for d in [self.f_d_corner, self.f_d_curve, self.f_d_start, 
                 self.f_d_end, self.f_d_flow, self.f_d_speed]:
            d.setRange(0, 100)
            
        form.addRow("Corner Slowdown:", self.f_d_corner)
        form.addRow("Curve Adaptation:", self.f_d_curve)
        form.addRow("Start Ramp:", self.f_d_start)
        form.addRow("End Taper:", self.f_d_end)
        form.addRow("Flow Smoothing:", self.f_d_flow)
        form.addRow("Speed Smoothing:", self.f_d_speed)
        
        self.tabs.addTab(tab, "Optimization Defaults")
        
    def _populate_fields(self):
        d = self.profile_data
        if not d:
            return
            
        self.f_name.setText(d.get('name', ''))
        self.f_id.setText(d.get('id', ''))
        self.f_category.setText(d.get('category', ''))
        self.f_description.setText(d.get('description', ''))
        
        temp = d.get('temperature', {})
        self.f_temp_nozzle.setValue(temp.get('nozzle', 200))
        self.f_temp_bed.setValue(temp.get('bed', 60))
        
        self.f_pressure_sens.setValue(d.get('pressure_sensitivity', 0.5))
        self.f_corner_sens.setValue(d.get('corner_sensitivity', 0.5))
        self.f_curve_sens.setValue(d.get('curve_sensitivity', 0.5))
        self.f_pressure_decay.setValue(d.get('pressure_decay', 0.85))
        
        flow = d.get('flow_characteristics', {})
        self.f_opt_flow.setValue(flow.get('optimal_flow_rate', 50.0))
        self.f_max_flow.setValue(flow.get('max_flow_rate', 100.0))
        self.f_visc_idx.setValue(flow.get('viscosity_index', 1.0))
        self.f_melt_idx.setValue(flow.get('melt_flow_index', 10.0))
        
        weights = d.get('vpi_weights', {})
        self.f_w_flow.setValue(weights.get('flow', 0.2))
        self.f_w_speed.setValue(weights.get('speed', 0.15))
        self.f_w_corner.setValue(weights.get('corner', 0.2))
        self.f_w_curve.setValue(weights.get('curve', 0.1))
        self.f_w_history.setValue(weights.get('history', 0.1))
        self.f_w_accel.setValue(weights.get('acceleration', 0.1))
        self.f_w_startstop.setValue(weights.get('start_stop', 0.1))
        self.f_w_density.setValue(weights.get('density', 0.05))
        
        defaults = d.get('optimization_defaults', {})
        self.f_d_corner.setValue(defaults.get('corner_slowdown', 50))
        self.f_d_curve.setValue(defaults.get('curve_adaptation', 50))
        self.f_d_start.setValue(defaults.get('start_ramp', 50))
        self.f_d_end.setValue(defaults.get('end_taper', 50))
        self.f_d_flow.setValue(defaults.get('flow_smoothing', 50))
        self.f_d_speed.setValue(defaults.get('speed_smoothing', 50))

    def get_data(self) -> dict:
        """Construct the material dict from form fields."""
        return {
            "name": self.f_name.text(),
            "id": self.f_id.text(),
            "category": self.f_category.text(),
            "description": self.f_description.text(),
            "temperature": {
                "nozzle": self.f_temp_nozzle.value(),
                "bed": self.f_temp_bed.value()
            },
            "pressure_sensitivity": self.f_pressure_sens.value(),
            "corner_sensitivity": self.f_corner_sens.value(),
            "curve_sensitivity": self.f_curve_sens.value(),
            "pressure_decay": self.f_pressure_decay.value(),
            "flow_characteristics": {
                "optimal_flow_rate": self.f_opt_flow.value(),
                "max_flow_rate": self.f_max_flow.value(),
                "viscosity_index": self.f_visc_idx.value(),
                "melt_flow_index": self.f_melt_idx.value()
            },
            "vpi_weights": {
                "flow": self.f_w_flow.value(),
                "speed": self.f_w_speed.value(),
                "corner": self.f_w_corner.value(),
                "curve": self.f_w_curve.value(),
                "history": self.f_w_history.value(),
                "acceleration": self.f_w_accel.value(),
                "start_stop": self.f_w_startstop.value(),
                "density": self.f_w_density.value()
            },
            "optimization_defaults": {
                "corner_slowdown": self.f_d_corner.value(),
                "curve_adaptation": self.f_d_curve.value(),
                "start_ramp": self.f_d_start.value(),
                "end_taper": self.f_d_end.value(),
                "flow_smoothing": self.f_d_flow.value(),
                "speed_smoothing": self.f_d_speed.value()
            }
        }
