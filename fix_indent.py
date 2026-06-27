import re

with open("src/ui/widgets/layer_viewer_widget.py", "r") as f:
    content = f.read()

content = content.replace("                def _update_geometry(self):", "        def _update_geometry(self):")

with open("src/ui/widgets/layer_viewer_widget.py", "w") as f:
    f.write(content)
