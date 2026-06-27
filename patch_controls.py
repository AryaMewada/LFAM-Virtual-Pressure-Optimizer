import sys

with open("src/ui/widgets/optimization_controls.py", "r") as f:
    content = f.read()

# Add signal
content = content.replace("optimize_clicked = pyqtSignal()", "optimize_clicked = pyqtSignal()\n    export_clicked = pyqtSignal()")

# Find the end of optimize button
btn_end = """        )
        self._optimize_btn.clicked.connect(self.optimize_clicked.emit)
        layout.addWidget(self._optimize_btn)"""

export_btn = """        )
        self._optimize_btn.clicked.connect(self.optimize_clicked.emit)
        layout.addWidget(self._optimize_btn)

        # --- export button ---
        self._export_btn = QPushButton('EXPORT G-CODE')
        self._export_btn.setObjectName('exportButton')
        self._export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._export_btn.setStyleSheet(f\"\"\"
            QPushButton#exportButton {{
                background-color: {Theme.BG_TERTIARY};
                color: {Theme.TEXT_SECONDARY};
                font-size: 14px;
                font-weight: bold;
                border: 1px solid {Theme.BORDER};
                border-radius: 8px;
                padding: 12px;
                margin-top: 5px;
            }}
            QPushButton#exportButton:hover {{
                background-color: {Theme.BG_ELEVATED};
                color: {Theme.TEXT_PRIMARY};
                border-color: {Theme.TEXT_MUTED};
            }}
        \"\"\")
        self._export_btn.clicked.connect(self.export_clicked.emit)
        self._export_btn.setEnabled(False) # Enabled by main window on success
        layout.addWidget(self._export_btn)
"""
content = content.replace(btn_end, export_btn)

with open("src/ui/widgets/optimization_controls.py", "w") as f:
    f.write(content)

print("Patched!")
