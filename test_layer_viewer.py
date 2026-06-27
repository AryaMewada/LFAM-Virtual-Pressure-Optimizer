import sys
from PyQt6.QtWidgets import QApplication
from src.ui.widgets.layer_viewer_widget import LayerViewerWidget

app = QApplication(sys.argv)
viewer = LayerViewerWidget()
viewer.show()

moves = [
    {'type': 'print', 'x1': 0.0, 'y1': 0.0, 'x2': 10.0, 'y2': 10.0, 'vpi': 0.5},
    {'type': 'travel', 'x1': 10.0, 'y1': 10.0, 'x2': 20.0, 'y2': 20.0, 'vpi': 0.0}
]

try:
    viewer.set_moves([moves])
    viewer.repaint()
    print("set_moves and repaint succeeded!")
except Exception as e:
    print(f"LayerViewerWidget FAILED: {e}")

sys.exit(0)
