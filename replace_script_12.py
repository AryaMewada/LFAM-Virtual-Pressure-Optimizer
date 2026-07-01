import re

with open('src/ui/widgets/slice_widget.py', 'r') as f:
    content = f.read()

export_method_code = """
    def _on_export_clicked(self):
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        
        if not hasattr(self, '_latest_slice_results') or not self._latest_slice_results:
            return
            
        filepath, _ = QFileDialog.getSaveFileName(self, "Export G-Code", "", "G-Code Files (*.gcode);;All Files (*)")
        if not filepath:
            return
            
        try:
            self.slice_status.setText("Exporting G-Code...")
            self.slice_status.repaint()
            
            from src.slicer.gcode_generator import GCodeGenerator
            
            # Read settings
            layer_height = float(self.input_layer_height.text())
            extrusion_width = float(self.input_extrusion_width.text())
            
            generator = GCodeGenerator(
                layer_height=layer_height,
                extrusion_width=extrusion_width
            )
            
            generator.begin()
            for island_idx, model_idx, result in self._latest_slice_results:
                generator.add_result(result, island_idx, model_idx)
            gcode = generator.end()
            
            with open(filepath, 'w') as f:
                f.write(gcode)
                
            self.slice_status.setText(f"Exported successfully to {filepath.split('/')[-1]}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export G-Code:\\n{str(e)}")
            self.slice_status.setText("Export failed.")
"""

# Remove from end
content = content.replace(export_method_code, "")
# Remove trailing newlines
content = content.rstrip() + "\n"

# Insert inside SliceWidget before class TransformGizmo
pattern = re.compile(r'    def _on_anim_tick\(self\):[\s\S]*?(?=class SlicerCanvas3D\(gl.GLViewWidget\):)')
match = pattern.search(content)

if match:
    insert_pos = match.end()
    content = content[:insert_pos] + export_method_code + "\n\n" + content[insert_pos:]
    with open('src/ui/widgets/slice_widget.py', 'w') as f:
        f.write(content)
    print("Moved _on_export_clicked successfully.")
else:
    print("Could not find insertion point!")

