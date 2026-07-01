import re

with open('src/ui/widgets/slice_widget.py', 'r') as f:
    content = f.read()

replacement = """
    def _update_volumetric_mesh(self):
        import numpy as np
        import pyqtgraph.opengl as gl
        if not hasattr(self, '_anim_visible_lines') or self._anim_visible_lines is None:
            if hasattr(self, 'volumetric_mesh_item') and self.volumetric_mesh_item:
                md_volumetric = gl.MeshData(vertexes=np.empty((0,3)), faces=np.empty((0,3), dtype=np.uint32))
                self.volumetric_mesh_item.setMeshData(meshdata=md_volumetric)
            return
            
        if not hasattr(self, '_full_volumetric_faces') or not self.btn_3d_bead.isChecked():
            return
            
        value = self.anim_slider.value()
        final_lines = self._anim_visible_lines
        final_colors = self._anim_visible_colors
        
        # Calculate skipped extrusions from min_layer_slider
        min_idx = self.min_layer_slider.value() if hasattr(self, 'min_layer_slider') else 0
        skipped_colors = []
        for i in range(min_idx):
            skipped_colors.append(self._cached_layer_lines[i][2])
            
        skipped_extrusions = 0
        if skipped_colors:
            all_skipped_colors = np.vstack(skipped_colors)
            skipped_extrusions = np.count_nonzero(all_skipped_colors[0::2, 3] > 0.5)
            
        start_face = skipped_extrusions * 8
        
        # We need to know exactly how many extrusions we've drawn up to `value`
        drawn_colors = final_colors[:value*2]
        is_extrusion = (drawn_colors[0::2, 3] > 0.5)
        num_visible_extrusions = np.count_nonzero(is_extrusion)
        
        num_faces = num_visible_extrusions * 8
        
        if num_faces <= 0:
            md_volumetric = gl.MeshData(vertexes=np.empty((0,3)), faces=np.empty((0,3), dtype=np.uint32))
            self.volumetric_mesh_item.setMeshData(meshdata=md_volumetric)
            return
            
        end_face = start_face + num_faces
        if end_face > len(self._full_volumetric_faces):
            end_face = len(self._full_volumetric_faces)
            
        visible_faces = self._full_volumetric_faces[start_face:end_face]
        visible_colors = self._full_volumetric_colors[start_face:end_face].copy()
        
        # Re-apply fading (ambient occlusion based on distance to nozzle Z)
        if value > 0 and len(final_lines) > 0:
            num_points = min(value*2, len(final_lines))
            current_z = final_lines[num_points - 1, 2]
            
            # Since visible_faces corresponds to self._full_volumetric_verts, 
            # we check the Z height of the first vertex of each face
            vertex_indices = visible_faces[:, 0]
            face_z = self._full_volumetric_verts[vertex_indices, 2]
            dz = current_z - face_z
            
            fade_dist = 150.0
            fade_factor = np.clip(1.0 - (dz / fade_dist) * 0.85, 0.15, 1.0)
            
            visible_colors[:, :3] *= fade_factor[:, None]
            
        md_volumetric = gl.MeshData(
            vertexes=self._full_volumetric_verts, 
            faces=visible_faces, 
            faceColors=visible_colors
        )
        self.volumetric_mesh_item.setMeshData(meshdata=md_volumetric)
"""

pattern = re.compile(r'    def _update_volumetric_mesh\(self\):.*?    def _on_anim_tick\(self\):', re.DOTALL)
new_content = pattern.sub(replacement.strip('\n') + '\n\n    def _on_anim_tick(self):', content)

with open('src/ui/widgets/slice_widget.py', 'w') as f:
    f.write(new_content)
print("Updated volumetric mesh logic.")
