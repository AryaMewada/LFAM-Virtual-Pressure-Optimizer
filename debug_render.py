import sys
from PyQt6.QtWidgets import QApplication
from src.ui.main_window import MainWindow

app = QApplication(sys.argv)
mw = MainWindow()
mw.show()

test_gcode = """
G28
G92 E0
G1 F1500 X10 Y10 Z0.2 E1.0
G1 X20 Y20 E2.0
G1 X10 Y20 E3.0
G1 X10 Y10 E4.0
M82
"""
with open('test_anim.gcode', 'w') as f:
    f.write(test_gcode)

mw._parsed_data = None
mw._start_worker('parse', {'filepath': 'test_anim.gcode'})

while mw._worker is not None and mw._worker.isRunning():
    app.processEvents()

viewer = mw.layer_viewer

print("Starting simulation test...")
viewer._toggle_playback()
for _ in range(50):
    viewer._on_sim_tick()
    app.processEvents()
    print(f"Time: {viewer._sim_time_sec:.4f} / {viewer._current_layer_total_time:.4f}")

sys.exit(0)
