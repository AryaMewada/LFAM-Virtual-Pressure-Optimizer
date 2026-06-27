import re

with open("src/ui/widgets/layer_viewer_widget.py", "r") as f:
    content = f.read()

# 1. Add grid to __init__
init_old = """            self._nozzle_item = gl.GLScatterPlotItem(size=10, pxMode=True)
            self.addItem(self._nozzle_item)"""
            
init_new = """            self._nozzle_item = gl.GLScatterPlotItem(size=10, pxMode=True)
            self.addItem(self._nozzle_item)
            
            self._grid_item = gl.GLGridItem()
            # Set grid color to be very subtle
            grid_c = QColor(Theme.TEXT_MUTED)
            self._grid_item.setColor((grid_c.redF(), grid_c.greenF(), grid_c.blueF(), 0.3))
            self.addItem(self._grid_item)"""

content = content.replace(init_old, init_new)

# 2. Update grid in _precompute_arrays
precomp_old = """        def _precompute_arrays(self):
            print_pos = []
            print_color = []"""
            
precomp_new = """        def _precompute_arrays(self):
            print_pos = []
            print_color = []"""

# Wait, instead of _precompute_arrays, I can update the grid position in set_all_moves
# right after _precompute_arrays() when we have bounds, OR at the end of _precompute_arrays.
# Let's put it at the end of _precompute_arrays.

end_precomp_old = """            if travel_pos:
                travel_c = QColor(Theme.TEXT_MUTED)
                tc = [travel_c.redF(), travel_c.greenF(), travel_c.blueF(), 0.5]
                self._full_travel_color = np.tile(tc, (len(travel_pos), 1)).astype(np.float32)
            else:
                self._full_travel_color = np.zeros((0, 4), dtype=np.float32)"""
                
end_precomp_new = """            if travel_pos:
                travel_c = QColor(Theme.TEXT_MUTED)
                tc = [travel_c.redF(), travel_c.greenF(), travel_c.blueF(), 0.5]
                self._full_travel_color = np.tile(tc, (len(travel_pos), 1)).astype(np.float32)
            else:
                self._full_travel_color = np.zeros((0, 4), dtype=np.float32)
                
            # Update grid to encompass the print bounds
            if len(self._full_print_pos) > 0:
                min_x = np.min(self._full_print_pos[:, 0])
                max_x = np.max(self._full_print_pos[:, 0])
                min_y = np.min(self._full_print_pos[:, 1])
                max_y = np.max(self._full_print_pos[:, 1])
                
                cx = (min_x + max_x) / 2
                cy = (min_y + max_y) / 2
                
                # Make the grid a multiple of 50, larger than the print
                size_x = max(int(max_x - min_x + 100), 200)
                size_y = max(int(max_y - min_y + 100), 200)
                
                import PyQt6.QtGui as QtGui
                # Size takes QtGui.QVector3D according to Pyqtgraph's GLGridItem, 
                # but older versions just take x,y,z or Vector.
                import pyqtgraph as pg
                self._grid_item.setSize(x=size_x, y=size_y, z=1)
                self._grid_item.setSpacing(x=10, y=10, z=1)
                
                self._grid_item.resetTransform()
                self._grid_item.translate(cx, cy, 0)
            else:
                self._grid_item.setSize(x=200, y=200, z=1)
                self._grid_item.setSpacing(x=10, y=10, z=1)
                self._grid_item.resetTransform()"""

content = content.replace(end_precomp_old, end_precomp_new)

with open("src/ui/widgets/layer_viewer_widget.py", "w") as f:
    f.write(content)

print("Grid added!")
