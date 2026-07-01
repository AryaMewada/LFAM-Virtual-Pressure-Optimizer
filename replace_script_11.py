import re

with open('src/ui/widgets/slice_widget.py', 'r') as f:
    content = f.read()

# 1. Add Export G-Code button below Slice button
export_btn_code = """
        # Slice Button
        self.btn_slice = QPushButton("Slice")
        self.btn_slice.setFixedHeight(40)
        self.btn_slice.setStyleSheet(f\"\"\"
            QPushButton {{
                background-color: {Theme.ACCENT_PRIMARY};
                color: {Theme.TEXT_PRIMARY};
                font-size: 16px;
                font-weight: bold;
                border: none;
                border-radius: 4px;
            }}
            QPushButton:hover {{ background-color: {Theme.ACCENT_HOVER}; }}
        \"\"\")
        self.btn_slice.clicked.connect(self._on_slice_clicked)
        left_layout.addWidget(self.btn_slice)
        
        # Export G-Code Button
        self.btn_export = QPushButton("Export G-Code")
        self.btn_export.setFixedHeight(40)
        self.btn_export.setEnabled(False) # Disabled until sliced
        self.btn_export.setStyleSheet(f\"\"\"
            QPushButton {{
                background-color: {Theme.BG_TERTIARY};
                color: {Theme.TEXT_PRIMARY};
                font-size: 16px;
                font-weight: bold;
                border: 1px solid {Theme.BORDER};
                border-radius: 4px;
            }}
            QPushButton:hover:enabled {{ background-color: {Theme.BG_HOVER}; }}
            QPushButton:disabled {{ color: {Theme.TEXT_SECONDARY}; }}
        \"\"\")
        self.btn_export.clicked.connect(self._on_export_clicked)
        left_layout.addWidget(self.btn_export)
"""
pattern_btn = re.compile(r'        # Slice Button.*?left_layout.addWidget\(self.btn_slice\)', re.DOTALL)
content = pattern_btn.sub(export_btn_code.strip('\n'), content)

# 2. Add self._latest_slice_results in _on_slice_clicked
slice_init_code = """
        self.slice_status.setText("Slicing...")
        self.slice_status.repaint() # Force UI update before blocking thread
        
        self._latest_slice_results = []
"""
content = content.replace('        self.slice_status.setText("Slicing...")\n        self.slice_status.repaint() # Force UI update before blocking thread', slice_init_code.strip('\n'))

# 3. Store result in _latest_slice_results
store_result_code = """
                result = engine.slice_model(
                    model.raw_vertices,
                    model.pos,
                    model.rot_matrix,
                    model.scale_vec
                )
                
                self._latest_slice_results.append((island_idx, len(self._latest_slice_results), result))
"""
pattern_store = re.compile(r'                result = engine.slice_model\([\s\S]*?scale_vec\n                \)', re.DOTALL)
content = pattern_store.sub(store_result_code.strip('\n'), content)

# 4. Enable button after slicing
enable_btn_code = """
            if hasattr(self, 'layer_slider_container'):
                self.layer_slider_container.hide()
            self.anim_overlay.hide()
            
        self.btn_export.setEnabled(True)
"""
content = content.replace("            if hasattr(self, 'layer_slider_container'):\n                self.layer_slider_container.hide()\n            self.anim_overlay.hide()", enable_btn_code.strip('\n'))

# 5. Disable export button when slicing is cleared
clear_slice_code = """
        self.slice_status.setText("Ready to slice.")
        self.btn_export.setEnabled(False)
"""
content = content.replace('        self.slice_status.setText("Ready to slice.")', clear_slice_code.strip('\n'))

# 6. Add _on_export_clicked method at the very end
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
            QMessageBox.critical(self, "Export Error", f"Failed to export G-Code:\n{str(e)}")
            self.slice_status.setText("Export failed.")
"""
content += "\n" + export_method_code

with open('src/ui/widgets/slice_widget.py', 'w') as f:
    f.write(content)

print("Added Export G-Code button.")
