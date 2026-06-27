with open("src/ui/widgets/layer_viewer_widget.py", "r") as f:
    content = f.read()

canvas_3d_code = """
    class _LayerCanvas3D(gl.GLViewWidget):
        \"\"\"Inner canvas widget that renders the toolpath visualization in 3D.\"\"\"
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setMinimumHeight(250)
            # Set background to match theme
            bg_color = QColor(Theme.BG_SECONDARY)
            self.setBackgroundColor(bg_color)
            
            self._all_moves = []
            self._current_layer = 0
            
            self._print_item = None
            self._travel_item = None
            
        def set_all_moves(self, all_moves):
            self._all_moves = all_moves
            self._current_layer = 0
            self._update_geometry()
            
        def set_layer(self, layer_number: int):
            self._current_layer = layer_number
            self._update_geometry()
            
        def fit_to_view(self):
            # Try to center the camera on the data
            if not self._all_moves:
                return
            min_x, max_x = float('inf'), float('-inf')
            min_y, max_y = float('inf'), float('-inf')
            min_z, max_z = float('inf'), float('-inf')
            
            for layer in self._all_moves:
                for m in layer:
                    x1, y1, z1 = m.get('x1',0), m.get('y1',0), m.get('z1',0)
                    x2, y2, z2 = m.get('x2',0), m.get('y2',0), m.get('z2',0)
                    min_x = min(min_x, x1, x2)
                    max_x = max(max_x, x1, x2)
                    min_y = min(min_y, y1, y2)
                    max_y = max(max_y, y1, y2)
                    min_z = min(min_z, z1, z2)
                    max_z = max(max_z, z1, z2)
            
            if min_x != float('inf'):
                cx = (min_x + max_x) / 2
                cy = (min_y + max_y) / 2
                cz = (min_z + max_z) / 2
                self.opts['center'] = pg.Vector(cx, cy, cz)
                distance = max(max_x - min_x, max_y - min_y, max_z - min_z) * 1.5
                self.opts['distance'] = max(distance, 10.0)
                self.update()

        def _update_geometry(self):
            # Remove old items
            if self._print_item is not None:
                self.removeItem(self._print_item)
                self._print_item = None
            if self._travel_item is not None:
                self.removeItem(self._travel_item)
                self._travel_item = None
                
            if not self._all_moves or self._current_layer < 0:
                return
                
            print_pos = []
            print_color = []
            travel_pos = []
            
            # Up to the current layer
            for i in range(min(self._current_layer + 1, len(self._all_moves))):
                for m in self._all_moves[i]:
                    x1, y1, z1 = m.get('x1',0), m.get('y1',0), m.get('z1',0)
                    x2, y2, z2 = m.get('x2',0), m.get('y2',0), m.get('z2',0)
                    
                    if m.get('type') == 'travel':
                        travel_pos.append([x1, y1, z1])
                        travel_pos.append([x2, y2, z2])
                    else:
                        print_pos.append([x1, y1, z1])
                        print_pos.append([x2, y2, z2])
                        vpi = m.get('vpi', 0.0)
                        qcolor = Theme.pressure_color(vpi)
                        r, g, b, a = qcolor.redF(), qcolor.greenF(), qcolor.blueF(), qcolor.alphaF()
                        print_color.append([r, g, b, a])
                        print_color.append([r, g, b, a])
                        
            if print_pos:
                self._print_item = gl.GLLinePlotItem(pos=np.array(print_pos, dtype=np.float32), 
                                                     color=np.array(print_color, dtype=np.float32), 
                                                     mode='lines', width=2)
                self.addItem(self._print_item)
                
            if travel_pos:
                travel_c = QColor(Theme.TEXT_MUTED)
                tc = [travel_c.redF(), travel_c.greenF(), travel_c.blueF(), 0.5]
                t_color = np.tile(tc, (len(travel_pos), 1))
                self._travel_item = gl.GLLinePlotItem(pos=np.array(travel_pos, dtype=np.float32),
                                                      color=np.array(t_color, dtype=np.float32),
                                                      mode='lines', width=1)
                self.addItem(self._travel_item)
"""

if "import pyqtgraph as pg" not in content:
    content = content.replace("import pyqtgraph.opengl as gl", "import pyqtgraph as pg\\nimport pyqtgraph.opengl as gl")

if "class _LayerCanvas3D" not in content:
    content += canvas_3d_code

with open("src/ui/widgets/layer_viewer_widget.py", "w") as f:
    f.write(content)
print("Added 3D Canvas class!")
