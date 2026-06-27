import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPixmap
from src.ui.main_window import MainWindow

app = QApplication(sys.argv)
window = MainWindow()
window.show()
window.adjustSize()
pixmap = window.sidebar.grab()
pixmap.save("sidebar.png")
