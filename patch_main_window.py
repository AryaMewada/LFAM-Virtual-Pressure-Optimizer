import re

with open("src/ui/main_window.py", "r") as f:
    content = f.read()

# 1. Revert sidebar from QScrollArea back to QFrame
scroll_area_str = """        self.sidebar = QScrollArea()
        self.sidebar.setFixedWidth(320)
        self.sidebar.setWidgetResizable(True)
        self.sidebar.setFrameShape(QFrame.Shape.NoFrame)
        self.sidebar.setStyleSheet(f\"\"\"
            QScrollArea {{
                background-color: {Theme.BG_SECONDARY};
                border-right: 1px solid {Theme.BORDER};
            }}
            QScrollBar:vertical {{
                background: {Theme.BG_SECONDARY};
                width: 8px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {Theme.TEXT_MUTED};
                min-height: 20px;
                border-radius: 4px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        \"\"\")

        self.sidebar_content = QFrame()
        self.sidebar_content.setStyleSheet("background: transparent; border: none;")
        sidebar_layout = QVBoxLayout(self.sidebar_content)"""

frame_str = """        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(320)
        self.sidebar.setStyleSheet(f\"\"\"
            QFrame {{
                background-color: {Theme.BG_SECONDARY};
                border-right: 1px solid {Theme.BORDER};
            }}
        \"\"\")

        sidebar_layout = QVBoxLayout(self.sidebar)"""

content = content.replace(scroll_area_str, frame_str)

content = content.replace("""        sidebar_layout.addStretch()
        self.sidebar.setWidget(self.sidebar_content)
        main_layout.addWidget(self.sidebar)""", """        sidebar_layout.addStretch()
        main_layout.addWidget(self.sidebar)""")

# 2. Add buttons to navbar
placeholder_btns = """        # Placeholder buttons
        btn1 = QPushButton("Projects")
        btn2 = QPushButton("Machine Setup")
        btn3 = QPushButton("Settings")
        
        for btn in (btn1, btn2, btn3):
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f\"\"\"
                QPushButton {{
                    color: {Theme.TEXT_SECONDARY};
                    background: transparent;
                    border: none;
                    font-size: 11px;
                    font-weight: 500;
                    padding: 8px 12px;
                }}
                QPushButton:hover {{
                    color: {Theme.TEXT_PRIMARY};
                    background: {Theme.BG_TERTIARY};
                    border-radius: 6px;
                }}
            \"\"\")
            navbar_layout.addWidget(btn)"""

nav_btns = """        # Action Buttons in Navbar
        self.optimize_btn = QPushButton("OPTIMIZE")
        self.optimize_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.optimize_btn.setStyleSheet(f\"\"\"
            QPushButton {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Theme.ACCENT_GRADIENT_START},
                    stop:1 {Theme.ACCENT_GRADIENT_END}
                );
                color: white;
                font-size: 13px;
                font-weight: bold;
                padding: 8px 24px;
                border-radius: 6px;
                border: none;
            }}
            QPushButton:hover {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5b9af6,
                    stop:1 #a57cf6
                );
            }}
            QPushButton:disabled {{
                background: {Theme.BG_TERTIARY};
                color: {Theme.TEXT_MUTED};
            }}
        \"\"\")
        self.optimize_btn.setEnabled(False)
        navbar_layout.addWidget(self.optimize_btn)

        self.export_btn = QPushButton("EXPORT G-CODE")
        self.export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.export_btn.setStyleSheet(f\"\"\"
            QPushButton {{
                background-color: {Theme.BG_TERTIARY};
                color: {Theme.TEXT_PRIMARY};
                font-size: 13px;
                font-weight: bold;
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
                padding: 8px 16px;
                margin-left: 12px;
            }}
            QPushButton:hover {{
                background-color: {Theme.BG_ELEVATED};
                border-color: {Theme.TEXT_MUTED};
            }}
            QPushButton:disabled {{
                background-color: transparent;
                color: {Theme.TEXT_MUTED};
                border: 1px dashed {Theme.BORDER};
            }}
        \"\"\")
        self.export_btn.setEnabled(False)
        navbar_layout.addWidget(self.export_btn)"""

content = content.replace(placeholder_btns, nav_btns)

# 3. Connect signals
old_signals = """        if self.optimization_controls is not None and hasattr(self.optimization_controls, 'optimize_clicked'):
            self.optimization_controls.optimize_clicked.connect(self._on_optimize_clicked)
            if hasattr(self.optimization_controls, 'export_clicked'):
                self.optimization_controls.export_clicked.connect(self._on_save_requested)"""

new_signals = """        self.optimize_btn.clicked.connect(self._on_optimize_clicked)
        self.export_btn.clicked.connect(self._on_save_requested)"""

content = content.replace(old_signals, new_signals)

# 4. Handle state in _on_file_loaded
old_enable = """        if self.optimization_controls is not None:
            self.optimization_controls.enable_controls()"""

new_enable = """        if self.optimization_controls is not None:
            self.optimization_controls.enable_controls()
        self.optimize_btn.setEnabled(True)"""
content = content.replace(old_enable, new_enable)

# 5. Handle state in _on_optimization_finished
old_finish = """        if self.optimization_controls is not None:
            self.optimization_controls.hide_progress()"""
new_finish = """        if self.optimization_controls is not None:
            self.optimization_controls.hide_progress()
        self.optimize_btn.setEnabled(True)
        self.export_btn.setEnabled(True)"""
content = content.replace(old_finish, new_finish)

# 6. Handle state in _on_optimization_error
old_err = """        if self.optimization_controls is not None:
            self.optimization_controls.hide_progress()"""
new_err = """        if self.optimization_controls is not None:
            self.optimization_controls.hide_progress()
        self.optimize_btn.setEnabled(True)"""
# Only replace the first occurrence (which is _on_optimization_error if it comes after finish, wait, let's just use regex)
content = re.sub(r'(def _on_optimization_error.*?)if self\.optimization_controls is not None:\s*self\.optimization_controls\.hide_progress\(\)', 
                 r'\1if self.optimization_controls is not None:\n            self.optimization_controls.hide_progress()\n        self.optimize_btn.setEnabled(True)', 
                 content, flags=re.DOTALL)

# Update optimize clicked
content = content.replace("        if self.optimization_controls is not None:\n            self.optimization_controls.show_progress()", 
                          "        if self.optimization_controls is not None:\n            self.optimization_controls.show_progress()\n        self.optimize_btn.setEnabled(False)\n        self.export_btn.setEnabled(False)")

with open("src/ui/main_window.py", "w") as f:
    f.write(content)

print("MainWindow patched!")
