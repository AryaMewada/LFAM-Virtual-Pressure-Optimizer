import re

with open('src/ui/widgets/slice_widget.py', 'r') as f:
    content = f.read()

replacement = """
        try:
            layer_height = float(self.input_layer_height.text())
            initial_height = float(self.input_initial_height.text())
            extrusion_width = float(self.input_extrusion_width.text())
            wall_count = int(self.input_wall_count.text())
            infill_density = float(self.input_infill_density.text()) / 100.0
            infill_pattern = self.input_infill_pattern.currentText()
            
            # Enforce reasonable LFAM bounds to prevent UI freezes
            layer_height = max(0.2, layer_height)
            initial_height = max(0.2, initial_height)
            extrusion_width = max(0.4, extrusion_width)
            wall_count = max(0, min(10, wall_count))
            infill_density = max(0.0, min(0.50, infill_density)) # Max 50% infill for LFAM
            
            # Update UI to reflect clamped values
            self.input_layer_height.setText(str(layer_height))
            self.input_initial_height.setText(str(initial_height))
            self.input_extrusion_width.setText(str(extrusion_width))
            self.input_wall_count.setText(str(wall_count))
            self.input_infill_density.setText(str(int(infill_density * 100)))
            
        except ValueError:
            self.slice_status.setText("Invalid slice settings. Must be numbers.")
            return
"""

pattern = re.compile(r'        try:\n            layer_height = float\(self.input_layer_height.text\(\)\)\n.*?        except ValueError:\n            self.slice_status.setText\("Invalid slice settings. Must be numbers."\)\n            return', re.DOTALL)
new_content = pattern.sub(replacement.strip('\n'), content)

with open('src/ui/widgets/slice_widget.py', 'w') as f:
    f.write(new_content)
print("Updated parsing with limits.")
