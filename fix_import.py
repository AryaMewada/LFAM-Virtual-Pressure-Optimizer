with open("src/ui/widgets/layer_viewer_widget.py", "r") as f:
    content = f.read()

bad_str = "import pyqtgraph as pg\\nimport pyqtgraph.opengl as gl"
good_str = "import pyqtgraph as pg\nimport pyqtgraph.opengl as gl"

if bad_str in content:
    content = content.replace(bad_str, good_str)
    with open("src/ui/widgets/layer_viewer_widget.py", "w") as f:
        f.write(content)
    print("Fixed imports!")
else:
    print("Could not find bad import.")
