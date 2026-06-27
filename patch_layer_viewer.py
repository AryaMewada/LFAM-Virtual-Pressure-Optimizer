import re

with open("src/ui/widgets/layer_viewer_widget.py", "r") as f:
    content = f.read()

# 1. Add Imports
if "import pyqtgraph.opengl as gl" not in content:
    imports_new = """import math
import numpy as np
import pyqtgraph.opengl as gl"""
    content = content.replace("import math", imports_new)

if "QStackedWidget" not in content:
    content = content.replace("QSlider, QPushButton", "QSlider, QPushButton, QStackedWidget")

# 2. Modify _setup_ui to use QStackedWidget and add Toggle Button
setup_ui_old = """        # Canvas
        self._canvas = self._LayerCanvas(self)
        layout.addWidget(self._canvas, 1)

        # Controls bar"""
setup_ui_new = """        # Canvas Stack
        self._stack = QStackedWidget()
        layout.addWidget(self._stack, 1)
        
        self._canvas = self._LayerCanvas(self)
        self._canvas_3d = self._LayerCanvas3D(self)
        
        self._stack.addWidget(self._canvas)
        self._stack.addWidget(self._canvas_3d)

        # Controls bar"""
if "self._stack = QStackedWidget()" not in content:
    content = content.replace(setup_ui_old, setup_ui_new)

buttons_old = """        # Fit to View button
        fit_btn = QPushButton("Fit to View")"""
buttons_new = """        # Toggle 3D Button
        self._toggle_3d_btn = QPushButton("3D View")
        self._toggle_3d_btn.setFont(QFont("Segoe UI", 9))
        self._toggle_3d_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._toggle_3d_btn.setCheckable(True)
        self._toggle_3d_btn.setStyleSheet(f\"\"\"
            QPushButton {{
                background-color: {Theme.BG_TERTIARY};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 4px;
                padding: 4px 12px;
            }}
            QPushButton:hover {{
                background-color: {Theme.BG_ELEVATED};
                border-color: {Theme.ACCENT_PRIMARY};
            }}
            QPushButton:checked {{
                background-color: {Theme.ACCENT_PRIMARY};
                border-color: {Theme.ACCENT_PRIMARY};
            }}
        \"\"\")
        controls_layout.addWidget(self._toggle_3d_btn)

        # Fit to View button
        fit_btn = QPushButton("Fit to View")"""
if "self._toggle_3d_btn = QPushButton" not in content:
    content = content.replace(buttons_old, buttons_new)

signals_old = """        # Connect signals
        self._layer_slider.valueChanged.connect(self._on_layer_changed)
        fit_btn.clicked.connect(self._canvas.fit_to_view)"""
signals_new = """        # Connect signals
        self._layer_slider.valueChanged.connect(self._on_layer_changed)
        fit_btn.clicked.connect(self._canvas.fit_to_view)
        fit_btn.clicked.connect(self._canvas_3d.fit_to_view)
        self._toggle_3d_btn.toggled.connect(self._on_toggle_3d)"""
if "self._toggle_3d_btn.toggled.connect" not in content:
    content = content.replace(signals_old, signals_new)


# 3. Add _on_toggle_3d method
toggle_method = """    def _on_toggle_3d(self, checked: bool):
        if checked:
            self._stack.setCurrentWidget(self._canvas_3d)
            self._toggle_3d_btn.setText("2D View")
        else:
            self._stack.setCurrentWidget(self._canvas)
            self._toggle_3d_btn.setText("3D View")
            
"""
if "def _on_toggle_3d" not in content:
    content = content.replace("    def _on_layer_changed", toggle_method + "    def _on_layer_changed")


# 4. Route data to both canvases
set_moves_old = """        if self._all_moves:
            self.set_layer(0)
        else:
            self._canvas._moves = []
            self._canvas._bounds_cache = None
            self._layer_label.setText("Layer: 0 / 0")
            self._canvas.update()"""
set_moves_new = """        # Set all moves to 3D canvas
        self._canvas_3d.set_all_moves(self._all_moves)
        
        if self._all_moves:
            self.set_layer(0)
        else:
            self._canvas._moves = []
            self._canvas._bounds_cache = None
            self._canvas_3d.set_layer(0)
            self._layer_label.setText("Layer: 0 / 0")
            self._canvas.update()"""
if "self._canvas_3d.set_all_moves" not in content:
    content = content.replace(set_moves_old, set_moves_new)

set_layer_old = """        if 0 <= layer_number < len(self._all_moves):
            self._canvas._moves = self._all_moves[layer_number]
        else:
            self._canvas._moves = []

        self._canvas._bounds_cache = None
        self._canvas._needs_redraw = True
        total = max(len(self._all_moves), 1)
        self._layer_label.setText(f"Layer: {layer_number + 1} / {total}")
        self._canvas.update()"""
set_layer_new = """        if 0 <= layer_number < len(self._all_moves):
            self._canvas._moves = self._all_moves[layer_number]
        else:
            self._canvas._moves = []

        self._canvas._bounds_cache = None
        self._canvas._needs_redraw = True
        self._canvas_3d.set_layer(layer_number)
        
        total = max(len(self._all_moves), 1)
        self._layer_label.setText(f"Layer: {layer_number + 1} / {total}")
        self._canvas.update()"""
if "self._canvas_3d.set_layer(layer_number)" not in content:
    content = content.replace(set_layer_old, set_layer_new)


# 5. Add _LayerCanvas3D class at the end
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

if "_LayerCanvas3D" not in content:
    # Need to import pg for pg.Vector
    if "import pyqtgraph as pg" not in content:
        content = content.replace("import pyqtgraph.opengl as gl", "import pyqtgraph as pg\\nimport pyqtgraph.opengl as gl")
    content += canvas_3d_code

with open("src/ui/widgets/layer_viewer_widget.py", "w") as f:
    f.write(content)
print("Patched!")
