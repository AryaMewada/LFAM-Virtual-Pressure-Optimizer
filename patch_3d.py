with open("src/ui/widgets/layer_viewer_widget.py", "r") as f:
    content = f.read()

import re

# We will replace the entire _LayerCanvas3D class.
# Let's find where it starts.
start_idx = content.find("class _LayerCanvas3D(gl.GLViewWidget):")
if start_idx == -1:
    print("Could not find _LayerCanvas3D")
    exit(1)

new_class = """class _LayerCanvas3D(gl.GLViewWidget):
        \"\"\"Inner canvas widget that renders the toolpath visualization in 3D.\"\"\"
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setMinimumHeight(250)
            # Set background to match theme
            bg_color = QColor(Theme.BG_SECONDARY)
            self.setBackgroundColor(bg_color)
            
            self._all_moves = []
            self._current_layer = 0
            
            self._print_item = gl.GLLinePlotItem(mode='lines', width=2)
            self.addItem(self._print_item)
            
            self._travel_item = gl.GLLinePlotItem(mode='lines', width=1)
            self.addItem(self._travel_item)
            
            # Pre-computed arrays
            self._full_print_pos = np.zeros((0, 3), dtype=np.float32)
            self._full_print_color = np.zeros((0, 4), dtype=np.float32)
            self._full_travel_pos = np.zeros((0, 3), dtype=np.float32)
            self._full_travel_color = np.zeros((0, 4), dtype=np.float32)
            
            # Layer indices
            self._print_layer_indices = []
            self._travel_layer_indices = []
            
        def set_all_moves(self, all_moves):
            self._all_moves = all_moves
            self._current_layer = 0
            self._precompute_arrays()
            self._update_geometry()
            
        def _precompute_arrays(self):
            print_pos = []
            print_color = []
            travel_pos = []
            
            self._print_layer_indices = []
            self._travel_layer_indices = []
            
            for layer in self._all_moves:
                for m in layer:
                    x1, y1, z1 = m.get('x1',0), m.get('y1',0), m.get('z1',0)
                    x2, y2, z2 = m.get('x2',0), m.get('y2',0), m.get('z2',0)
                    
                    if m.get('type') == 'travel':
                        travel_pos.extend([[x1, y1, z1], [x2, y2, z2]])
                    else:
                        print_pos.extend([[x1, y1, z1], [x2, y2, z2]])
                        vpi = m.get('vpi', 0.0)
                        qcolor = Theme.pressure_color(vpi)
                        r, g, b, a = qcolor.redF(), qcolor.greenF(), qcolor.blueF(), qcolor.alphaF()
                        print_color.extend([[r, g, b, a], [r, g, b, a]])
                        
                self._print_layer_indices.append(len(print_pos))
                self._travel_layer_indices.append(len(travel_pos))
                
            self._full_print_pos = np.array(print_pos, dtype=np.float32)
            self._full_print_color = np.array(print_color, dtype=np.float32)
            self._full_travel_pos = np.array(travel_pos, dtype=np.float32)
            
            if travel_pos:
                travel_c = QColor(Theme.TEXT_MUTED)
                tc = [travel_c.redF(), travel_c.greenF(), travel_c.blueF(), 0.5]
                self._full_travel_color = np.tile(tc, (len(travel_pos), 1)).astype(np.float32)
            else:
                self._full_travel_color = np.zeros((0, 4), dtype=np.float32)

        def set_layer(self, layer_number: int):
            self._current_layer = layer_number
            self._update_geometry()
            
        def fit_to_view(self):
            if len(self._full_print_pos) == 0:
                return
            
            min_x = np.min(self._full_print_pos[:, 0])
            max_x = np.max(self._full_print_pos[:, 0])
            min_y = np.min(self._full_print_pos[:, 1])
            max_y = np.max(self._full_print_pos[:, 1])
            min_z = np.min(self._full_print_pos[:, 2])
            max_z = np.max(self._full_print_pos[:, 2])
            
            cx = (min_x + max_x) / 2
            cy = (min_y + max_y) / 2
            cz = (min_z + max_z) / 2
            self.opts['center'] = pg.Vector(cx, cy, cz)
            distance = max(max_x - min_x, max_y - min_y, max_z - min_z) * 1.5
            self.opts['distance'] = max(distance, 10.0)
            self.update()

        def _update_geometry(self):
            if not self._all_moves or self._current_layer < 0 or self._current_layer >= len(self._print_layer_indices):
                self._print_item.setData(pos=np.zeros((0,3), dtype=np.float32), color=np.zeros((0,4), dtype=np.float32))
                self._travel_item.setData(pos=np.zeros((0,3), dtype=np.float32), color=np.zeros((0,4), dtype=np.float32))
                return
                
            p_idx = self._print_layer_indices[self._current_layer]
            t_idx = self._travel_layer_indices[self._current_layer]
            
            if p_idx > 0:
                self._print_item.setData(pos=self._full_print_pos[:p_idx], color=self._full_print_color[:p_idx])
            else:
                self._print_item.setData(pos=np.zeros((0,3), dtype=np.float32), color=np.zeros((0,4), dtype=np.float32))
                
            if t_idx > 0:
                self._travel_item.setData(pos=self._full_travel_pos[:t_idx], color=self._full_travel_color[:t_idx])
            else:
                self._travel_item.setData(pos=np.zeros((0,3), dtype=np.float32), color=np.zeros((0,4), dtype=np.float32))
"""

content = content[:start_idx] + new_class

with open("src/ui/widgets/layer_viewer_widget.py", "w") as f:
    f.write(content)

print("Patched 3D optimization")
