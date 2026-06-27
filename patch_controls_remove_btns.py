import re

with open("src/ui/widgets/optimization_controls.py", "r") as f:
    content = f.read()

# Remove signals
content = content.replace("    optimize_clicked = pyqtSignal()\n", "")
content = content.replace("    export_clicked = pyqtSignal()\n", "")

# Remove buttons from init (lines 163 to 236 roughly)
btn_pattern = re.compile(r'# --- optimize button ---.*?layout\.addWidget\(self\._progress_bar\)', re.DOTALL)
content = btn_pattern.sub('        # --- progress bar ---\n        self._progress_bar = QProgressBar()\n        self._progress_bar.setVisible(False)\n        self._progress_bar.setTextVisible(True)\n        self._progress_bar.setRange(0, 100)\n        layout.addWidget(self._progress_bar)', content)

export_pattern = re.compile(r'# --- export button ---.*?layout\.addWidget\(self\._export_btn\)', re.DOTALL)
content = export_pattern.sub('', content)

# Update show_progress and hide_progress
content = content.replace("self._optimize_btn.setEnabled(False)", "")
content = content.replace("self._optimize_btn.setEnabled(True)", "")
content = content.replace("""        if hasattr(self, '_export_btn'):
            self._export_btn.setEnabled(True)""", "")

with open("src/ui/widgets/optimization_controls.py", "w") as f:
    f.write(content)

print("Controls patched!")
