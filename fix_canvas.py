import re

with open("src/ui/widgets/layer_viewer_widget.py", "r") as f:
    content = f.read()

replacement = """    class _LayerCanvas3D(gl.GLViewWidget):
        \"\"\"Inner canvas widget that renders the toolpath visualization in 3D.\"\"\"
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setMinimumHeight(250)
            
            # Store mouse pos for inversion
            self._last_mouse_pos = None

            # Set background to match theme
            bg_color = QColor(Theme.BG_SECONDARY)
            self.setBackgroundColor(bg_color)
            
            self._all_moves = []
            self._current_layer = 0
            
            self._print_item = gl.GLLinePlotItem(mode='lines', width=2)
            self.addItem(self._print_item)
            
            self._travel_item = gl.GLLinePlotItem(mode='lines', width=1)
            self.addItem(self._travel_item)
            
            self._nozzle_item = gl.GLScatterPlotItem(size=10, pxMode=True)
            self.addItem(self._nozzle_item)
            
            self._sim_time_sec = -1.0
            
            # Pre-computed arrays
            self._full_print_pos = np.zeros((0, 3), dtype=np.float32)
            self._full_print_color = np.zeros((0, 4), dtype=np.float32)
            self._full_travel_pos = np.zeros((0, 3), dtype=np.float32)
            self._full_travel_color = np.zeros((0, 4), dtype=np.float32)
            
            # Layer indices
            self._print_layer_indices = []
            self._travel_layer_indices = []
            
            # Physics time arrays
            self._layer_durations = []
            self._move_cum_times = [] # List of numpy arrays, one per layer
            self._print_cum_times = [] # same
            self._travel_cum_times = [] # same

        def mouseMoveEvent(self, ev):
            # Invert the default PyQtGraph orbit movement for standard CAD feel
            lpos = ev.position() if hasattr(ev, 'position') else ev.localPos()
            if self._last_mouse_pos is None:
                self._last_mouse_pos = lpos
            diff = lpos - self._last_mouse_pos
            self._last_mouse_pos = lpos
            
            # Use Qt.MouseButton.LeftButton for PyQt6
            import PyQt6.QtCore as QtCore
            if ev.buttons() == QtCore.Qt.MouseButton.LeftButton:
                if (ev.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier):
                    self.pan(diff.x(), diff.y(), 0, relative='view')
                else:
                    # Inverted from PyQtGraph default (-diff.x, diff.y)
                    self.orbit(diff.x(), -diff.y())
            elif ev.buttons() == QtCore.Qt.MouseButton.MiddleButton:
                if (ev.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier):
                    self.pan(diff.x(), 0, diff.y(), relative='view-upright')
                else:
                    self.pan(diff.x(), diff.y(), 0, relative='view-upright')

        def mouseReleaseEvent(self, ev):
            super().mouseReleaseEvent(ev)
            self._last_mouse_pos = None

        def get_current_layer_duration(self):"""

# Use regex to replace from class _LayerCanvas3D to def get_current_layer_duration
content = re.sub(r'    class _LayerCanvas3D.*?def get_current_layer_duration\(self\):', replacement, content, flags=re.DOTALL)

with open("src/ui/widgets/layer_viewer_widget.py", "w") as f:
    f.write(content)
