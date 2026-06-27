import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from src.ui.theme import Theme
from src.ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(Theme.get_stylesheet())
    font = QFont('Inter', 10)
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    app.setFont(font)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
