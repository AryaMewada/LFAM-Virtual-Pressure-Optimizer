from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QFrame, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QPainter, QColor, QFont
from src.ui.theme import Theme

class LoadingOverlay(QWidget):
    """Custom loading overlay with dimmed background to prevent native modal crashes."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        
        # Overlay layout
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Center card
        self.card = QFrame()
        self.card.setFixedSize(320, 140)
        self.card.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_SECONDARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 12px;
            }}
        """)
        
        # Add shadow to card
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 4)
        self.card.setGraphicsEffect(shadow)
        
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(24, 24, 24, 24)
        card_layout.setSpacing(16)
        
        self.title_label = QLabel("Processing...")
        self.title_label.setStyleSheet(f"""
            color: {Theme.TEXT_PRIMARY};
            font-size: 16px;
            font-weight: bold;
            border: none;
        """)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {Theme.BG_TERTIARY};
                border: none;
                border-radius: 4px;
                color: {Theme.TEXT_PRIMARY};
                text-align: center;
                font-weight: bold;
                height: 20px;
            }}
            QProgressBar::chunk {{
                background-color: {Theme.ACCENT_PRIMARY};
                border-radius: 4px;
            }}
        """)
        
        card_layout.addWidget(self.title_label)
        card_layout.addWidget(self.progress_bar)
        
        layout.addWidget(self.card)
        
        self.hide()
        
    def paintEvent(self, event):
        try:
            self._safe_paintEvent(event)
        except Exception as e:
            import traceback
            with open('paintevent_error.txt', 'a') as errf:
                errf.write(f'Error in src/ui/widgets/loading_overlay.py: {str(e)}\n{traceback.format_exc()}\n')

    def _safe_paintEvent(self, event):
        """Draw a semi-transparent dark background."""
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 160))
        
    def show_loading(self, title: str):
        self.title_label.setText(title)
        self.progress_bar.setValue(0)
        if self.parentWidget():
            self.resize(self.parentWidget().size())
        self.show()
        self.raise_()
        
    def set_progress(self, value: int):
        self.progress_bar.setValue(value)
        
    def hide_loading(self):
        self.hide()
