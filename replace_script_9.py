import re

with open('src/ui/widgets/slice_widget.py', 'r') as f:
    content = f.read()

restored_methods = """
    def _on_layer_slider_changed(self, value=None):
        if not hasattr(self, '_cached_layer_lines') or not self._cached_layer_lines:
            return
            
        import numpy as np
        
        # Guard against recursive event loops
        if getattr(self, '_updating_sliders', False):
            return
            
        self._updating_sliders = True
        
        min_idx = self.min_layer_slider.value()
        max_idx = self.max_layer_slider.value()
        
        # Enforce min <= max constraint
        sender = self.sender()
        if sender == self.min_layer_slider and min_idx > max_idx:
            self.max_layer_slider.setValue(min_idx)
            max_idx = min_idx
        elif sender == self.max_layer_slider and max_idx < min_idx:
            self.min_layer_slider.setValue(max_idx)
            min_idx = max_idx
            
        self._updating_sliders = False
        
        # Guard indices
        min_idx = max(0, min_idx)
        max_idx = min(len(self._cached_layer_lines) - 1, max_idx)
        
        visible_lines = [self._cached_layer_lines[i][1] for i in range(min_idx, max_idx + 1)]
        visible_colors = [self._cached_layer_lines[i][2] for i in range(min_idx, max_idx + 1)]
        
        if visible_lines:
            self._anim_visible_lines = np.vstack(visible_lines)
            self._anim_visible_colors = np.vstack(visible_colors)
        else:
            self._anim_visible_lines = None
            self._anim_visible_colors = None
            
        if min_idx > max_idx:
            # Hide completely
            if hasattr(self, 'slice_preview_item') and self.slice_preview_item:
                self.slice_preview_item.setData(pos=np.empty((0, 3)), color=np.empty((0, 4)))
            return
            
        if hasattr(self, 'slice_preview_item') and self.slice_preview_item:
            if visible_lines:
                final_lines = np.vstack(visible_lines)
                self.anim_slider.setRange(0, len(final_lines) // 2)
                self.anim_slider.setValue(len(final_lines) // 2)
                if not self.anim_slider.isEnabled():
                    self.anim_slider.setEnabled(True)
                    
        # Update everything based on the anim slider
        self._on_anim_slider_changed(self.anim_slider.value())

    def _on_3d_bead_toggled(self, checked):
        if hasattr(self, 'slice_preview_item') and self.slice_preview_item:
            # Re-trigger animation slider to apply color masks
            self._on_anim_slider_changed(self.anim_slider.value())
            
        if hasattr(self, 'volumetric_mesh_item') and self.volumetric_mesh_item:
            self.volumetric_mesh_item.setVisible(checked)
            self._update_volumetric_mesh()

    def _toggle_animation(self):
        if not self._is_animating:
            self._is_animating = True
            self.btn_anim_play.setText("⏸")
            # If at the end, restart
            if self.anim_slider.value() == self.anim_slider.maximum():
                self.anim_slider.setValue(0)
            self.anim_timer.start()
        else:
            self._is_animating = False
            self.btn_anim_play.setText("▶")
            self.anim_timer.stop()

    def _on_anim_slider_changed(self, value):
        if getattr(self, '_anim_visible_lines', None) is None:
            return
            
        import numpy as np
        num_points = value * 2
        
        if num_points <= 0:
            self.slice_preview_item.setData(pos=np.empty((0, 3)), color=np.empty((0, 4)))
            if hasattr(self, 'nozzle_cursor') and self.nozzle_cursor:
                self.nozzle_cursor.hide()
        elif num_points >= len(self._anim_visible_lines):
            colors = self._anim_visible_colors
            if self.btn_3d_bead.isChecked():
                colors = colors.copy()
                colors[:, 3] = 0.05
            self.slice_preview_item.setData(pos=self._anim_visible_lines, color=colors)
            if hasattr(self, 'nozzle_cursor') and self.nozzle_cursor:
                self.nozzle_cursor.show()
                pos = self._anim_visible_lines[-1]
                self.nozzle_cursor.resetTransform()
                self.nozzle_cursor.translate(pos[0], pos[1], pos[2])
        else:
            colors = self._anim_visible_colors[:num_points]
            if self.btn_3d_bead.isChecked():
                colors = colors.copy()
                colors[:, 3] = 0.05
            self.slice_preview_item.setData(pos=self._anim_visible_lines[:num_points], color=colors)
            if hasattr(self, 'nozzle_cursor') and self.nozzle_cursor:
                self.nozzle_cursor.show()
                pos = self._anim_visible_lines[num_points-1]
                self.nozzle_cursor.resetTransform()
                self.nozzle_cursor.translate(pos[0], pos[1], pos[2])
                
        # Also dim the CAD model further when in 3D bead view
        models = getattr(self.gl_viewer, 'active_models', [])
        for model in models:
            if getattr(model, '_is_sliced', False):
                if self.btn_3d_bead.isChecked():
                    model.setColor((0.3, 0.3, 0.3, 0.02)) # Even more transparent
                else:
                    model.setColor((0.3, 0.3, 0.3, 0.15))
                    
        self._update_volumetric_mesh()

    def _on_anim_tick(self):
"""

pattern = re.compile(r'    def _on_anim_tick\(self\):', re.DOTALL)
new_content = pattern.sub(restored_methods.strip('\n') + '\n', content)

with open('src/ui/widgets/slice_widget.py', 'w') as f:
    f.write(new_content)
print("Restored methods.")
