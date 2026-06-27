import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPaintEvent
from PyQt6.QtCore import QRect, QTimer

from src.ui.widgets.layer_viewer_widget import LayerViewerWidget

app = QApplication(sys.argv)
w = LayerViewerWidget()

# dummy moves
moves = [[
    {'type': 'print', 'x1': 10, 'y1': 10, 'x2': 20, 'y2': 20, 'vpi': 0.5},
    {'type': 'travel', 'x1': 20, 'y1': 20, 'x2': 50, 'y2': 50, 'vpi': 0.0}
]]
w.set_moves(moves)

w.show()
QTimer.singleShot(1000, app.quit)
app.exec()
