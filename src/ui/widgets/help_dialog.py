"""
Help Dialog with a carousel for explaining software parameters.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QLabel, QPushButton, QWidget, QFrame
)
from PyQt6.QtCore import Qt
from src.ui.theme import Theme

class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("LFAM Optimizer - Help & Documentation")
        self.setFixedSize(600, 450)
        self.setStyleSheet(f"""
            QDialog {{ background-color: {Theme.BG_PRIMARY}; }}
            QLabel {{ color: {Theme.TEXT_PRIMARY}; }}
        """)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(20)
        
        # Carousel
        self.carousel = QStackedWidget()
        self.layout.addWidget(self.carousel)
        
        # Slides
        self.slides = [
            {
                "title": "Welcome to LFAM Optimizer",
                "content": "This software analyzes and optimizes G-code specifically for Large Format Additive Manufacturing (LFAM) pellet extruders.\n\nBecause pellet extruders have a massive melt pool, they suffer from residual pressure, oozing, and corner bulging. This software uses a Virtual Pressure Engine to simulate pressure buildup and automatically adjust feedrates and extrusion to compensate."
            },
            {
                "title": "Virtual Pressure Index (VPI)",
                "content": "The VPI is a simulated metric (0.0 to 1.0) representing the internal pressure of the extruder barrel.\n\n1.0 means critical pressure (risk of blobbing or jamming).\n0.0 means depleted pressure (risk of under-extrusion).\n\nThe optimizer aims to keep pressure stable across the entire print."
            },
            {
                "title": "Optimization: Corner Slowdown",
                "content": "Sharp corners cause sudden changes in machine velocity. In LFAM, this causes a massive pressure spike, resulting in bulging corners.\n\nCorner Slowdown automatically detects sharp angles and dynamically reduces the feedrate (while keeping extrusion volume constant) to allow the pressure to normalize."
            },
            {
                "title": "Optimization: Curve Adaptation",
                "content": "Tight curves force the machine to decelerate. Because the screw keeps turning at the same rate, this causes over-extrusion on the inside of the curve.\n\nCurve Adaptation detects tight radii and adjusts the flow to maintain a perfect line width, regardless of the machine's turning speed."
            },
            {
                "title": "Optimization: Start Ramp (Pressure Primer)",
                "content": "When a travel move ends, the nozzle is depleted of pressure.\n\nThe Start Ramp acts as a 'Pressure Primer'. It temporarily commands an over-extrusion (e.g., 150%) for the first few millimeters of a new line to instantly build pressure back up, preventing under-extrusion."
            },
            {
                "title": "Optimization: End Taper (Coasting)",
                "content": "When the nozzle pauses at the end of a layer, residual pressure causes plastic to keep oozing.\n\nThe End Taper ('Coasting') gradually shuts off the screw rotation before the line finishes. The residual pressure is used to push out the remaining plastic, leaving zero pressure when the nozzle finally pauses."
            },
            {
                "title": "Optimization: Smoothing",
                "content": "Flow Smoothing and Speed Smoothing apply a moving average to the G-code commands.\n\nThis prevents sudden, violent changes in screw RPM or machine velocity, protecting the extruder hardware and resulting in a much smoother surface finish."
            }
        ]
        
        for slide in self.slides:
            page = QWidget()
            page_layout = QVBoxLayout(page)
            page_layout.setContentsMargins(0, 0, 0, 0)
            
            title = QLabel(slide["title"])
            title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {Theme.ACCENT_PRIMARY};")
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            content = QLabel(slide["content"])
            content.setStyleSheet("font-size: 14px; line-height: 1.5;")
            content.setWordWrap(True)
            content.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            
            page_layout.addWidget(title)
            page_layout.addWidget(content, stretch=1)
            self.carousel.addWidget(page)
            
        # Controls
        controls_layout = QHBoxLayout()
        
        self.prev_btn = QPushButton("Previous")
        self.prev_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.prev_btn.clicked.connect(self._prev_slide)
        self._style_button(self.prev_btn)
        
        self.page_label = QLabel("1 / 7")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.next_btn = QPushButton("Next")
        self.next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.next_btn.clicked.connect(self._next_slide)
        self._style_button(self.next_btn)
        
        controls_layout.addWidget(self.prev_btn)
        controls_layout.addStretch()
        controls_layout.addWidget(self.page_label)
        controls_layout.addStretch()
        controls_layout.addWidget(self.next_btn)
        
        self.layout.addLayout(controls_layout)
        self._update_controls()
        
    def _style_button(self, btn):
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.BG_TERTIARY};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 4px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {Theme.BG_ELEVATED};
            }}
            QPushButton:disabled {{
                background-color: transparent;
                color: {Theme.TEXT_MUTED};
            }}
        """)
        
    def _prev_slide(self):
        idx = self.carousel.currentIndex()
        if idx > 0:
            self.carousel.setCurrentIndex(idx - 1)
            self._update_controls()
            
    def _next_slide(self):
        idx = self.carousel.currentIndex()
        if idx < self.carousel.count() - 1:
            self.carousel.setCurrentIndex(idx + 1)
            self._update_controls()
        else:
            self.accept() # Close on last next
            
    def _update_controls(self):
        idx = self.carousel.currentIndex()
        self.page_label.setText(f"{idx + 1} / {self.carousel.count()}")
        self.prev_btn.setEnabled(idx > 0)
        if idx == self.carousel.count() - 1:
            self.next_btn.setText("Close")
        else:
            self.next_btn.setText("Next")
