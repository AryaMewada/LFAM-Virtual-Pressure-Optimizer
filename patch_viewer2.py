import re

with open("src/ui/widgets/layer_viewer_widget.py", "r") as f:
    content = f.read()

# Fix set_layer to set _needs_redraw = True
old_set_layer = """        self._canvas._bounds_cache = None
        total = max(len(self._all_moves), 1)
        self._layer_label.setText(f"Layer: {layer_number + 1} / {total}")
        self._canvas.update()"""

new_set_layer = """        self._canvas._bounds_cache = None
        self._canvas._needs_redraw = True
        total = max(len(self._all_moves), 1)
        self._layer_label.setText(f"Layer: {layer_number + 1} / {total}")
        self._canvas.update()"""

if old_set_layer in content:
    content = content.replace(old_set_layer, new_set_layer)
    print("Patched set_layer!")
else:
    print("Could not find set_layer code block.")

# Fix fit_to_view
old_fit = """        def fit_to_view(self):
            \"\"\"Reset pan and zoom to fit the entire layer in view.\"\"\"
            self._pan_start = QPoint()
            
            self._pixmap_cache = None
            self._needs_redraw = True"""

new_fit = """        def fit_to_view(self):
            \"\"\"Reset pan and zoom to fit the entire layer in view.\"\"\"
            self._pan_offset = QPointF(0, 0)
            self._zoom = 1.0
            self._pixmap_cache = None
            self._needs_redraw = True
            self.update()"""

if old_fit in content:
    content = content.replace(old_fit, new_fit)
    print("Patched fit_to_view!")
else:
    print("Could not find fit_to_view code block.")

with open("src/ui/widgets/layer_viewer_widget.py", "w") as f:
    f.write(content)
