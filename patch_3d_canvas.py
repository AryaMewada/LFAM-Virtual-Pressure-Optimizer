import re

with open("src/ui/widgets/layer_viewer_widget.py", "r") as f:
    content = f.read()

# Add _sim_index and nozzle scatter plot to _LayerCanvas3D
init_old = """            self._travel_item = gl.GLLinePlotItem(mode='lines', width=1)
            self.addItem(self._travel_item)
            
            # Pre-computed arrays"""
init_new = """            self._travel_item = gl.GLLinePlotItem(mode='lines', width=1)
            self.addItem(self._travel_item)
            
            self._nozzle_item = gl.GLScatterPlotItem(size=10, pxMode=True)
            self.addItem(self._nozzle_item)
            
            self._sim_index = -1
            
            # Pre-computed arrays"""
if "self._sim_index = -1" not in content.split("class _LayerCanvas3D")[1]:
    content = content.replace(init_old, init_new, 1)

# Modify _update_geometry in _LayerCanvas3D
update_old = """            if p_idx > 0:
                self._print_item.setData(pos=self._full_print_pos[:p_idx], color=self._full_print_color[:p_idx])
            else:
                self._print_item.setData(pos=np.zeros((0,3), dtype=np.float32), color=np.zeros((0,4), dtype=np.float32))
                
            if t_idx > 0:
                self._travel_item.setData(pos=self._full_travel_pos[:t_idx], color=self._full_travel_color[:t_idx])
            else:
                self._travel_item.setData(pos=np.zeros((0,3), dtype=np.float32), color=np.zeros((0,4), dtype=np.float32))"""

update_new = """            # Support simulation slicing
            if self._sim_index != -1 and self._current_layer < len(self._all_moves):
                # The total index is the index of previous layers + the current layer's sim index
                prev_p_idx = self._print_layer_indices[self._current_layer - 1] if self._current_layer > 0 else 0
                prev_t_idx = self._travel_layer_indices[self._current_layer - 1] if self._current_layer > 0 else 0
                
                # We need to figure out how many print/travel moves are in the current layer up to _sim_index
                # We can just count them.
                layer_moves = self._all_moves[self._current_layer]
                sim_moves = layer_moves[:self._sim_index + 1]
                
                p_count = sum(2 for m in sim_moves if m.get('type') != 'travel')
                t_count = sum(2 for m in sim_moves if m.get('type') == 'travel')
                
                p_idx = prev_p_idx + p_count
                t_idx = prev_t_idx + t_count
                
                # Update nozzle marker
                if sim_moves:
                    last_m = sim_moves[-1]
                    nx, ny, nz = last_m.get('x2',0), last_m.get('y2',0), last_m.get('z2',0)
                    nc = QColor(Theme.SUCCESS)
                    self._nozzle_item.setData(pos=np.array([[nx, ny, nz]], dtype=np.float32), 
                                              color=np.array([[nc.redF(), nc.greenF(), nc.blueF(), 1.0]], dtype=np.float32))
                else:
                    self._nozzle_item.setData(pos=np.zeros((0,3), dtype=np.float32))
            else:
                self._nozzle_item.setData(pos=np.zeros((0,3), dtype=np.float32))

            if p_idx > 0:
                self._print_item.setData(pos=self._full_print_pos[:p_idx], color=self._full_print_color[:p_idx])
            else:
                self._print_item.setData(pos=np.zeros((0,3), dtype=np.float32), color=np.zeros((0,4), dtype=np.float32))
                
            if t_idx > 0:
                self._travel_item.setData(pos=self._full_travel_pos[:t_idx], color=self._full_travel_color[:t_idx])
            else:
                self._travel_item.setData(pos=np.zeros((0,3), dtype=np.float32), color=np.zeros((0,4), dtype=np.float32))"""
if "layer_moves = self._all_moves[self._current_layer]" not in content:
    content = content.replace(update_old, update_new, 1)

with open("src/ui/widgets/layer_viewer_widget.py", "w") as f:
    f.write(content)
print("Patched 3D canvas")
