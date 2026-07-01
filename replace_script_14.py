import re

with open('src/ui/widgets/slice_widget.py', 'r') as f:
    content = f.read()

# 1. Add temp UI inputs
temp_ui_code = """
        # Nozzle Temp
        nt_layout = QHBoxLayout()
        nt_layout.addWidget(QLabel("Nozzle Temp (C):"))
        self.input_nozzle_temp = QLineEdit("235")
        self.input_nozzle_temp.setFixedWidth(60)
        self.input_nozzle_temp.setStyleSheet(f"background-color: {Theme.BG_TERTIARY}; color: {Theme.TEXT_PRIMARY}; border: 1px solid {Theme.BORDER}; padding: 4px;")
        nt_layout.addWidget(self.input_nozzle_temp)
        settings_layout.addLayout(nt_layout)
        
        # Bed Temp
        bt_layout = QHBoxLayout()
        bt_layout.addWidget(QLabel("Bed Temp (C):"))
        self.input_bed_temp = QLineEdit("110")
        self.input_bed_temp.setFixedWidth(60)
        self.input_bed_temp.setStyleSheet(f"background-color: {Theme.BG_TERTIARY}; color: {Theme.TEXT_PRIMARY}; border: 1px solid {Theme.BORDER}; padding: 4px;")
        bt_layout.addWidget(self.input_bed_temp)
        settings_layout.addLayout(bt_layout)
        
        # Infill Density
"""

content = content.replace("        # Infill Density\n", temp_ui_code)

# 2. Add temp passing to Export
export_temp_code = """
            # Read settings
            layer_height = float(self.input_layer_height.text())
            extrusion_width = float(self.input_extrusion_width.text())
            nozzle_temp = int(self.input_nozzle_temp.text())
            bed_temp = int(self.input_bed_temp.text())
            
            generator = GCodeGenerator(
                layer_height=layer_height,
                extrusion_width=extrusion_width
            )
            
            generator.begin(bed_temp=bed_temp, nozzle_temp=nozzle_temp)
"""

pattern_export = re.compile(r'            # Read settings.*?generator\.begin\(\)', re.DOTALL)
content = pattern_export.sub(export_temp_code.strip('\n'), content)

with open('src/ui/widgets/slice_widget.py', 'w') as f:
    f.write(content)
print("Updated UI with temperature fields.")
