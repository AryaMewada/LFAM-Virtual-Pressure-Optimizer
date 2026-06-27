import re

with open("src/ui/widgets/layer_viewer_widget.py", "r") as f:
    content = f.read()

# 1. Height change
content = content.replace("self.setMinimumHeight(350)", "self.setMinimumHeight(650)")

# 2. Add "Play from Start" button
btn_old = """        self._play_btn = QPushButton("▶ Play")
        self._play_btn.setFixedWidth(80)
        self._play_btn.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self._play_btn.setStyleSheet(fit_btn.styleSheet())
        sim_layout.addWidget(self._play_btn)"""

btn_new = """        self._play_btn = QPushButton("▶ Play")
        self._play_btn.setFixedWidth(80)
        self._play_btn.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self._play_btn.setStyleSheet(fit_btn.styleSheet())
        sim_layout.addWidget(self._play_btn)
        
        self._play_start_btn = QPushButton("⏮ From Start")
        self._play_start_btn.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self._play_start_btn.setStyleSheet(fit_btn.styleSheet())
        sim_layout.addWidget(self._play_start_btn)"""

if "self._play_start_btn = QPushButton" not in content:
    content = content.replace(btn_old, btn_new)

# 3. Hook up Play from Start signal
sig_old = "self._play_btn.clicked.connect(self._toggle_playback)"
sig_new = "self._play_btn.clicked.connect(self._toggle_playback)\n        self._play_start_btn.clicked.connect(self._play_from_start)"
if "self._play_start_btn.clicked.connect" not in content:
    content = content.replace(sig_old, sig_new)

# 4. Modify 2D/3D toggle to be uncheckable
toggle_old = """        self._toggle_3d_btn = QPushButton("2D View")
        self._toggle_3d_btn.setFont(QFont("Segoe UI", 9))
        self._toggle_3d_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._toggle_3d_btn.setCheckable(True)
        self._toggle_3d_btn.setChecked(True)
        self._toggle_3d_btn.setText("2D View")
        self._toggle_3d_btn.setStyleSheet(f\"\"\"
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
            QPushButton:checked {{
                background-color: {Theme.ACCENT_PRIMARY};
                border-color: {Theme.ACCENT_PRIMARY};
            }}
        \"\"\")"""

toggle_new = """        self._toggle_3d_btn = QPushButton("Switch to 2D View")
        self._toggle_3d_btn.setFont(QFont("Segoe UI", 9))
        self._toggle_3d_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._toggle_3d_btn.setStyleSheet(f\"\"\"
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
        \"\"\")"""

if "Switch to 2D View" not in content:
    # We might have multiple toggle_old versions due to previous replacements. Let's just regex replace it.
    pass

import re
content = re.sub(r'self\._toggle_3d_btn = QPushButton\(.*?\n.*?\}""\"\)', toggle_new, content, flags=re.DOTALL)

# Also need to fix the toggled.connect to clicked.connect
content = content.replace("self._toggle_3d_btn.toggled.connect(self._on_toggle_3d)", "self._toggle_3d_btn.clicked.connect(self._on_toggle_3d)")

# Update _on_toggle_3d method
toggle_m_old = """    def _on_toggle_3d(self, checked: bool):
        if checked:
            self._stack.setCurrentWidget(self._canvas_3d)
            self._toggle_3d_btn.setText("2D View")
        else:
            self._stack.setCurrentWidget(self._canvas)
            self._toggle_3d_btn.setText("3D View")"""

toggle_m_new = """    def _on_toggle_3d(self):
        if self._stack.currentWidget() == self._canvas_3d:
            self._stack.setCurrentWidget(self._canvas)
            self._toggle_3d_btn.setText("Switch to 3D View")
        else:
            self._stack.setCurrentWidget(self._canvas_3d)
            self._toggle_3d_btn.setText("Switch to 2D View")"""
content = content.replace(toggle_m_old, toggle_m_new)


# 5. Update _on_sim_tick to play through layers
tick_old = """    def _on_sim_tick(self):
        layer_moves = self._all_moves[self._layer_slider.value()]
        if self._sim_index < len(layer_moves) - 1:
            self._sim_index += 1
            self._sim_slider.blockSignals(True)
            self._sim_slider.setValue(self._sim_index)
            self._sim_slider.blockSignals(False)
            self._update_canvases_sim()
        else:
            self._toggle_playback() # auto pause at end"""

tick_new = """    def _on_sim_tick(self):
        layer_moves = self._all_moves[self._layer_slider.value()]
        if self._sim_index < len(layer_moves) - 1:
            self._sim_index += 1
            self._sim_slider.blockSignals(True)
            self._sim_slider.setValue(self._sim_index)
            self._sim_slider.blockSignals(False)
            self._update_canvases_sim()
        else:
            # Reached end of layer
            current_layer = self._layer_slider.value()
            if current_layer < len(self._all_moves) - 1:
                # Need to update canvas before switching so we draw the final move
                self._update_canvases_sim() 
                self._layer_slider.setValue(current_layer + 1)
                self._sim_index = 0
            else:
                self._update_canvases_sim()
                self._toggle_playback() # auto pause at very end"""

content = content.replace(tick_old, tick_new)

# 6. Add _play_from_start method
play_start_method = """    def _play_from_start(self):
        if not self._all_moves:
            return
        self._layer_slider.setValue(0)
        self._sim_index = -1
        if not self._is_playing:
            self._toggle_playback()
"""

if "def _play_from_start" not in content:
    content = content.replace("    def _toggle_playback(self):", play_start_method + "\n    def _toggle_playback(self):")


# We need to make sure _sim_slider value ranges are set properly. 
# set_layer resets _sim_index to num_moves - 1 if we are not playing. BUT what if we are playing and we advanced the layer slider via code in _on_sim_tick?
# Actually, if we advance the layer slider, `_on_layer_changed` triggers `set_layer`.
# If `set_layer` sees we are playing? Wait, currently `set_layer` does:
# self._is_playing = False
# self._play_btn.setText("▶ Play")
# self._timer.stop()
# That breaks continuous playback!

# Let's fix set_layer
set_layer_old_code = """        # Reset simulation state
        self._sim_index = num_moves - 1
        self._sim_slider.blockSignals(True)
        self._sim_slider.setRange(0, max(0, num_moves - 1))
        self._sim_slider.setValue(self._sim_index)
        self._sim_slider.blockSignals(False)
        self._is_playing = False
        self._play_btn.setText("▶ Play")
        self._timer.stop()"""

set_layer_new_code = """        # Reset simulation state
        if not self._is_playing:
            self._sim_index = num_moves - 1
            
        self._sim_slider.blockSignals(True)
        self._sim_slider.setRange(0, max(0, num_moves - 1))
        self._sim_slider.setValue(max(0, self._sim_index))
        self._sim_slider.blockSignals(False)"""
content = content.replace(set_layer_old_code, set_layer_new_code)


with open("src/ui/widgets/layer_viewer_widget.py", "w") as f:
    f.write(content)
print("Patched Simulate from Start, heights, and toggle")
