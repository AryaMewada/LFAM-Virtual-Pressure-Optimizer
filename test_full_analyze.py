import sys
import os
from PyQt6.QtWidgets import QApplication
from src.ui.main_window import MainWindow

app = QApplication(sys.argv)
mw = MainWindow()
mw.show()

# 1. Create a fake file
test_gcode = """
G28
G92 E0
G1 F1500 X10 Y10 Z0.2 E1.0
G1 X20 Y20 E2.0
G1 X10 Y20 E3.0
G1 X10 Y10 E4.0
M82
"""
with open('test_crash.gcode', 'w') as f:
    f.write(test_gcode)

# 2. Simulate what MainWindow does
print("Starting parse...")
mw._parsed_data = None
mw._start_worker('parse', {'filepath': 'test_crash.gcode'})

# 3. Wait for workers to finish
while mw._worker is not None and mw._worker.isRunning():
    app.processEvents()

print("Workers finished! Checking if it crashed.")
sys.exit(0)
