import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPixmap
from src.ui.widgets.profile_selector_widget import ProfileSelectorWidget

app = QApplication(sys.argv)
widget = ProfileSelectorWidget()
widget.show()
widget.adjustSize()
pixmap = widget.grab()
pixmap.save("profile_selector.png")
