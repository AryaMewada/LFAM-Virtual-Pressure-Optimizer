from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPainter, QPixmap
from PyQt6.QtCore import QLineF, QPointF
app = QApplication([])
pixmap = QPixmap(100, 100)
painter = QPainter(pixmap)
lines = [QLineF(QPointF(0,0), QPointF(10,10))] * 100000
try:
    painter.drawLines(lines)
    print("drawLines list works with 100k lines!")
except Exception as e:
    print(f"Error: {e}")
