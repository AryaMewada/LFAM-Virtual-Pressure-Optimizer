from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QEvent
from PyQt6.QtGui import QCursor

from src.ui.theme import Theme

class CardButton(QFrame):
    clicked = pyqtSignal()
    
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setFixedSize(400, 400)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_SECONDARY};
                border: 2px solid {Theme.BORDER};
                border-radius: 16px;
            }}
            QFrame:hover {{
                border: 2px solid {Theme.ACCENT_PRIMARY};
                background-color: {Theme.BG_ELEVATED};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Placeholder Image Area (Dark grey box)
        self.image_placeholder = QLabel()
        self.image_placeholder.setStyleSheet(f"""
            background-color: {Theme.BG_TERTIARY};
            border-radius: 8px;
            border: none;
        """)
        self.image_placeholder.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Title
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(f"""
            color: {Theme.TEXT_PRIMARY};
            font-size: 24px;
            font-weight: bold;
            border: none;
            background: transparent;
        """)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(self.image_placeholder, stretch=1)
        layout.addWidget(self.title_label)
        
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mouseReleaseEvent(event)


class HomeWidget(QWidget):
    """
    Landing page containing the Welcome message and modular feature cards (Slice / Optimize).
    """
    
    slice_requested = pyqtSignal()
    optimize_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(60)
        
        # Welcome Title
        welcome_label = QLabel("Welcome to AMLFAMO")
        welcome_label.setStyleSheet(f"""
            color: {Theme.TEXT_PRIMARY};
            font-size: 36px;
            font-weight: 900;
            letter-spacing: 2px;
        """)
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(welcome_label)
        
        # Cards Layout
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(40)
        cards_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Slice Card
        self.slice_card = CardButton("Slice")
        self.slice_card.clicked.connect(self.slice_requested.emit)
        cards_layout.addWidget(self.slice_card)
        
        # Optimize Card
        self.optimize_card = CardButton("Optimize")
        self.optimize_card.clicked.connect(self.optimize_requested.emit)
        cards_layout.addWidget(self.optimize_card)
        
        layout.addLayout(cards_layout)
