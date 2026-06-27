import re

with open("src/ui/widgets/layer_viewer_widget.py", "r") as f:
    content = f.read()

# 1. Remove QStackedWidget and _LayerCanvas initialization in _setup_ui
stack_old = """        # Canvas Stack
        self._stack = QStackedWidget()
        layout.addWidget(self._stack, 1)
        
        self._canvas = self._LayerCanvas(self)
        self._canvas_3d = self._LayerCanvas3D(self)
        
        self._stack.addWidget(self._canvas)
        self._stack.addWidget(self._canvas_3d)
        
        # Default to 3D
        self._stack.setCurrentWidget(self._canvas_3d)"""

stack_new = """        # Canvas 3D
        self._canvas_3d = self._LayerCanvas3D(self)
        layout.addWidget(self._canvas_3d, 1)"""

content = content.replace(stack_old, stack_new)

# 2. Remove toggle button
toggle_btn_pattern = r'# Toggle 3D Button.*?\}\"\"\"\)\n'
content = re.sub(toggle_btn_pattern, '', content, flags=re.DOTALL)
content = re.sub(r'controls_layout\.addWidget\(self\._toggle_3d_btn\)\s*', '', content)
content = re.sub(r'self\._toggle_3d_btn\.clicked\.connect\(self\._on_toggle_3d\)\s*', '', content)

# 3. Remove _on_toggle_3d method
toggle_method_pattern = r'def _on_toggle_3d\(self\):.*?self\._toggle_3d_btn\.setText\("Switch to 2D View"\)\n'
content = re.sub(toggle_method_pattern, '', content, flags=re.DOTALL)

# 4. Remove _LayerCanvas class completely
canvas_class_pattern = r'class _LayerCanvas\(QWidget\):.*?class _LayerCanvas3D\(gl\.GLViewWidget\):'
content = re.sub(canvas_class_pattern, 'class _LayerCanvas3D(gl.GLViewWidget):', content, flags=re.DOTALL)

# 5. Remove _canvas updates from set_layer, set_moves, _update_canvases_sim
content = content.replace("self._canvas._moves = self._all_moves[layer_number]", "")
content = content.replace("self._canvas._moves = []", "")
content = content.replace("self._canvas._sim_index = self._sim_index\n", "")
content = content.replace("self._canvas._bounds_cache = None\n", "")
content = content.replace("self._canvas._needs_redraw = True\n", "")
content = content.replace("self._canvas.update()\n", "")
content = content.replace("fit_btn.clicked.connect(self._canvas.fit_to_view)\n", "")

with open("src/ui/widgets/layer_viewer_widget.py", "w") as f:
    f.write(content)

print("Removed 2D canvas")
