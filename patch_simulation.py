import re

with open("src/ui/widgets/layer_viewer_widget.py", "r") as f:
    content = f.read()

# 1. Imports
if "from PyQt6.QtWidgets import (" in content and "QComboBox" not in content:
    content = content.replace("QSlider, QPushButton", "QSlider, QPushButton, QComboBox")
if "from PyQt6.QtCore import Qt, QPointF, QRectF" in content and "QTimer" not in content:
    content = content.replace("from PyQt6.QtCore import Qt, QPointF, QRectF", "from PyQt6.QtCore import Qt, QPointF, QRectF, QTimer")

# 2. Add Timer and Simulation state to __init__
init_old = """        self._all_moves: list[list[dict]] = []
        self._all_pressure: list = []

        self._setup_ui()"""
init_new = """        self._all_moves: list[list[dict]] = []
        self._all_pressure: list = []
        
        self._sim_index = -1
        self._is_playing = False
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_sim_tick)

        self._setup_ui()"""
if "self._timer = QTimer(self)" not in content:
    content = content.replace(init_old, init_new)

# 3. Default to 3D View
setup_ui_old = """        self._stack.addWidget(self._canvas)
        self._stack.addWidget(self._canvas_3d)

        # Controls bar"""
setup_ui_new = """        self._stack.addWidget(self._canvas)
        self._stack.addWidget(self._canvas_3d)
        
        # Default to 3D
        self._stack.setCurrentWidget(self._canvas_3d)

        # Controls bar"""
if "self._stack.setCurrentWidget(self._canvas_3d)" not in content:
    content = content.replace(setup_ui_old, setup_ui_new)

toggle_old = """        self._toggle_3d_btn.setCheckable(True)"""
toggle_new = """        self._toggle_3d_btn.setCheckable(True)
        self._toggle_3d_btn.setChecked(True)
        self._toggle_3d_btn.setText("2D View")"""
if "self._toggle_3d_btn.setChecked(True)" not in content:
    content = content.replace(toggle_old, toggle_new)

# 4. Add Playback Controls
btn_old = """        fit_btn.setStyleSheet(f\"\"\"
            QPushButton {{
                background-color: {Theme.BG_TERTIARY};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 4px;
                padding: 4px 12px;
            }}
            QPushButton:hover {{
                background-color: {Theme.BG_ELEVATED};
                border-color: {Theme.ACCENT_PRIMARY};
            }}
            QPushButton:pressed {{
                background-color: {Theme.ACCENT_PRIMARY};
            }}
        \"\"\")
        controls_layout.addWidget(fit_btn)

        layout.addLayout(controls_layout)"""

btn_new = """        fit_btn.setStyleSheet(f\"\"\"
            QPushButton {{
                background-color: {Theme.BG_TERTIARY};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 4px;
                padding: 4px 12px;
            }}
            QPushButton:hover {{
                background-color: {Theme.BG_ELEVATED};
                border-color: {Theme.ACCENT_PRIMARY};
            }}
            QPushButton:pressed {{
                background-color: {Theme.ACCENT_PRIMARY};
            }}
        \"\"\")
        controls_layout.addWidget(fit_btn)
        layout.addLayout(controls_layout)
        
        # Simulation controls
        sim_layout = QHBoxLayout()
        sim_layout.setContentsMargins(0, 0, 0, 0)
        sim_layout.setSpacing(10)
        
        self._play_btn = QPushButton("▶ Play")
        self._play_btn.setFixedWidth(80)
        self._play_btn.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self._play_btn.setStyleSheet(fit_btn.styleSheet())
        sim_layout.addWidget(self._play_btn)
        
        self._sim_slider = QSlider(Qt.Orientation.Horizontal)
        self._sim_slider.setRange(0, 0)
        self._sim_slider.setStyleSheet(self._layer_slider.styleSheet().replace(Theme.ACCENT_PRIMARY, Theme.SUCCESS))
        sim_layout.addWidget(self._sim_slider, 1)
        
        self._speed_combo = QComboBox()
        self._speed_combo.addItems(["1x", "2x", "5x", "10x", "Max"])
        self._speed_combo.setCurrentIndex(2) # Default 5x
        self._speed_combo.setStyleSheet(f\"\"\"
            QComboBox {{
                background-color: {Theme.BG_TERTIARY};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 4px;
                padding: 4px 8px;
            }}
        \"\"\")
        sim_layout.addWidget(self._speed_combo)
        
        layout.addLayout(sim_layout)
"""
if "self._play_btn = QPushButton" not in content:
    content = content.replace(btn_old, btn_new)


# 5. Hook up signals for playback
signals_old = """        self._toggle_3d_btn.toggled.connect(self._on_toggle_3d)"""
signals_new = """        self._toggle_3d_btn.toggled.connect(self._on_toggle_3d)
        self._play_btn.clicked.connect(self._toggle_playback)
        self._sim_slider.valueChanged.connect(self._on_sim_scrub)
        self._speed_combo.currentIndexChanged.connect(self._update_timer_speed)"""
if "self._play_btn.clicked.connect" not in content:
    content = content.replace(signals_old, signals_new)


# 6. Add Playback logic methods
methods_new = """
    def _toggle_playback(self):
        if not self._all_moves:
            return
            
        layer_moves = self._all_moves[self._layer_slider.value()]
        if not layer_moves:
            return
            
        self._is_playing = not self._is_playing
        if self._is_playing:
            self._play_btn.setText("⏸ Pause")
            if self._sim_index >= len(layer_moves) - 1:
                self._sim_index = 0
            self._update_timer_speed()
            self._timer.start()
        else:
            self._play_btn.setText("▶ Play")
            self._timer.stop()
            
    def _update_timer_speed(self):
        idx = self._speed_combo.currentIndex()
        speeds = [100, 50, 20, 10, 1] # milliseconds per tick
        if self._is_playing:
            self._timer.setInterval(speeds[idx])
            
    def _on_sim_tick(self):
        layer_moves = self._all_moves[self._layer_slider.value()]
        if self._sim_index < len(layer_moves) - 1:
            self._sim_index += 1
            self._sim_slider.blockSignals(True)
            self._sim_slider.setValue(self._sim_index)
            self._sim_slider.blockSignals(False)
            self._update_canvases_sim()
        else:
            self._toggle_playback() # auto pause at end
            
    def _on_sim_scrub(self, value: int):
        self._sim_index = value
        self._update_canvases_sim()
        
    def _update_canvases_sim(self):
        self._canvas._sim_index = self._sim_index
        self._canvas_3d._sim_index = self._sim_index
        self._canvas._needs_redraw = True
        self._canvas.update()
        self._canvas_3d._update_geometry()
"""
if "def _toggle_playback" not in content:
    content = content.replace("    def _on_toggle_3d(self, checked: bool):", methods_new + "\n    def _on_toggle_3d(self, checked: bool):")


# 7. Update set_layer to reset simulation
set_layer_old = """        if 0 <= layer_number < len(self._all_moves):
            self._canvas._moves = self._all_moves[layer_number]
        else:
            self._canvas._moves = []

        self._canvas._bounds_cache = None
        self._canvas._needs_redraw = True
        self._canvas_3d.set_layer(layer_number)
        
        total = max(len(self._all_moves), 1)
        self._layer_label.setText(f"Layer: {layer_number + 1} / {total}")
        self._canvas.update()"""

set_layer_new = """        if 0 <= layer_number < len(self._all_moves):
            self._canvas._moves = self._all_moves[layer_number]
            num_moves = len(self._canvas._moves)
        else:
            self._canvas._moves = []
            num_moves = 0
            
        # Reset simulation state
        self._sim_index = num_moves - 1
        self._sim_slider.blockSignals(True)
        self._sim_slider.setRange(0, max(0, num_moves - 1))
        self._sim_slider.setValue(self._sim_index)
        self._sim_slider.blockSignals(False)
        self._is_playing = False
        self._play_btn.setText("▶ Play")
        self._timer.stop()
        
        self._canvas._sim_index = self._sim_index
        self._canvas_3d._sim_index = self._sim_index

        self._canvas._bounds_cache = None
        self._canvas._needs_redraw = True
        self._canvas_3d.set_layer(layer_number)
        
        total = max(len(self._all_moves), 1)
        self._layer_label.setText(f"Layer: {layer_number + 1} / {total}")
        self._canvas.update()"""

if "self._sim_slider.blockSignals(True)" not in content:
    content = content.replace(set_layer_old, set_layer_new)


with open("src/ui/widgets/layer_viewer_widget.py", "w") as f:
    f.write(content)
print("Patched UI controls and state")
