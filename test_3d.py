import sys
import numpy as np
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
import pyqtgraph.opengl as gl

app = QApplication(sys.argv)
w = QMainWindow()
cw = QWidget()
l = QVBoxLayout(cw)
w.setCentralWidget(cw)

v = gl.GLViewWidget()
l.addWidget(v)

# Generate disjoint lines
pos = np.array([
    [0, 0, 0], [10, 10, 10],
    [10, 10, 10], [20, 0, 20]
], dtype=np.float32)

color = np.array([
    [1, 0, 0, 1], [1, 0, 0, 1],
    [0, 1, 0, 1], [0, 1, 0, 1]
], dtype=np.float32)

line = gl.GLLinePlotItem(pos=pos, color=color, width=2, mode='lines')
v.addItem(line)

from PyQt6.QtCore import QTimer
w.show()
QTimer.singleShot(1000, app.quit)
app.exec()
print("Success!")
