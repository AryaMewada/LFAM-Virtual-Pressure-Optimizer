import re

with open("src/ui/main_window.py", "r") as f:
    content = f.read()

sidebar_orig = """        # ── Left Sidebar ─────────────────────────────────────────
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(320)
        self.sidebar.setStyleSheet(f\"\"\"
            QFrame {{
                background-color: {Theme.BG_SECONDARY};
                border-right: 1px solid {Theme.BORDER};
            }}
        \"\"\")

        sidebar_layout = QVBoxLayout(self.sidebar)"""

sidebar_new = """        # ── Left Sidebar ─────────────────────────────────────────
        self.sidebar = QScrollArea()
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

content = content.replace(sidebar_orig, sidebar_new)

add_widget_orig = """        sidebar_layout.addStretch()
        main_layout.addWidget(self.sidebar)"""

add_widget_new = """        sidebar_layout.addStretch()
        self.sidebar.setWidget(self.sidebar_content)
        main_layout.addWidget(self.sidebar)"""

content = content.replace(add_widget_orig, add_widget_new)

with open("src/ui/main_window.py", "w") as f:
    f.write(content)

print("Sidebar patched!")
