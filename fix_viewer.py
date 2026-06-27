import re

with open("src/ui/widgets/layer_viewer_widget.py", "r") as f:
    content = f.read()

# 1. Add Heatmap Combo
controls_old = """        fit_btn.setStyleSheet(f\"\"\"
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

controls_new = """        fit_btn.setStyleSheet(f\"\"\"
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
        
        self._heatmap_combo = QComboBox()
        self._heatmap_combo.addItems(["Pressure (VPI)", "Speed (Feedrate)", "Flow (Extrusion)"])
        self._heatmap_combo.setStyleSheet(f\"\"\"
            QComboBox {{
                background-color: {Theme.BG_TERTIARY};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 4px;
                padding: 4px 12px;
            }}
        \"\"\")
        controls_layout.addWidget(self._heatmap_combo)
        layout.addLayout(controls_layout)"""

content = content.replace(controls_old, controls_new)


# 2. Connect Heatmap Combo
connects_old = """        self._speed_combo.currentIndexChanged.connect(self._update_timer_speed)"""
connects_new = """        self._speed_combo.currentIndexChanged.connect(self._update_timer_speed)
        self._heatmap_combo.currentTextChanged.connect(self._on_heatmap_changed)"""
content = content.replace(connects_old, connects_new)


# 3. Add _on_heatmap_changed
on_heatmap = """    def _on_heatmap_changed(self, text: str):
        mode = "pressure"
        if "Speed" in text:
            mode = "speed"
        elif "Flow" in text:
            mode = "flow"
        self._canvas_3d.set_heatmap_mode(mode)

    def set_moves(self, moves: list, pressure_results: list = None):"""
content = content.replace("    def set_moves(self, moves: list, pressure_results: list = None):", on_heatmap)


# 4. Add heatmap_mode to _LayerCanvas3D init
canvas_init_old = """            self._sim_time_sec = -1.0"""
canvas_init_new = """            self._sim_time_sec = -1.0
            self._heatmap_mode = 'pressure'
            self._max_feedrate = 1.0
            self._max_extrusion = 1.0"""
content = content.replace(canvas_init_old, canvas_init_new)


# 5. Add set_heatmap_mode
canvas_meth_old = """        def get_current_layer_duration(self):"""
canvas_meth_new = """        def set_heatmap_mode(self, mode: str):
            self._heatmap_mode = mode
            self._recompute_colors()
            self._update_geometry()
            
        def get_current_layer_duration(self):"""
content = content.replace(canvas_meth_old, canvas_meth_new)


# 6. Change _precompute_arrays to compute max values and separate color logic
precomp_old = """            self._layer_durations = []
            self._move_cum_times = []
            self._print_cum_times = []
            self._travel_cum_times = []
            
            for layer in self._all_moves:
                layer_t = 0.0
                layer_times = []
                p_times = []
                t_times = []
                
                for m in layer:
                    dur = m.get('duration', 0.0)
                    layer_t += dur
                    layer_times.append(layer_t)
                    
                    x1, y1, z1 = m.get('x1',0), m.get('y1',0), m.get('z1',0)
                    x2, y2, z2 = m.get('x2',0), m.get('y2',0), m.get('z2',0)
                    
                    if m.get('type') == 'travel':
                        t_times.append(layer_t)
                        travel_pos.extend([[x1, y1, z1], [x2, y2, z2]])
                    else:
                        p_times.append(layer_t)
                        print_pos.extend([[x1, y1, z1], [x2, y2, z2]])
                        vpi = m.get('vpi', 0.0)
                        qcolor = Theme.pressure_color(vpi)
                        r, g, b, a = qcolor.redF(), qcolor.greenF(), qcolor.blueF(), qcolor.alphaF()
                        print_color.extend([[r, g, b, a], [r, g, b, a]])
                        
                self._print_layer_indices.append(len(print_pos))"""

precomp_new = """            self._layer_durations = []
            self._move_cum_times = []
            self._print_cum_times = []
            self._travel_cum_times = []
            
            # Find max values for normalization
            max_f = 1.0
            max_e = 1.0
            for layer in self._all_moves:
                for m in layer:
                    if not m.get('type') == 'travel':
                        f = m.get('feedrate', 0.0)
                        e = m.get('extrusion', 0.0)
                        if f > max_f: max_f = f
                        if e > max_e: max_e = e
            self._max_feedrate = max_f
            self._max_extrusion = max_e
            
            for layer in self._all_moves:
                layer_t = 0.0
                layer_times = []
                p_times = []
                t_times = []
                
                for m in layer:
                    dur = m.get('duration', 0.0)
                    layer_t += dur
                    layer_times.append(layer_t)
                    
                    x1, y1, z1 = m.get('x1',0), m.get('y1',0), m.get('z1',0)
                    x2, y2, z2 = m.get('x2',0), m.get('y2',0), m.get('z2',0)
                    
                    if m.get('type') == 'travel':
                        t_times.append(layer_t)
                        travel_pos.extend([[x1, y1, z1], [x2, y2, z2]])
                    else:
                        p_times.append(layer_t)
                        print_pos.extend([[x1, y1, z1], [x2, y2, z2]])
                        
                self._print_layer_indices.append(len(print_pos))"""
content = content.replace(precomp_old, precomp_new)


# 7. Recompute colors separately
recompute_code = """
        def _recompute_colors(self):
            print_color = []
            for layer in self._all_moves:
                for m in layer:
                    if m.get('type') != 'travel':
                        if self._heatmap_mode == 'speed':
                            val = m.get('feedrate', 0.0) / self._max_feedrate
                            qcolor = Theme.speed_color(val)
                        elif self._heatmap_mode == 'flow':
                            val = m.get('extrusion', 0.0) / self._max_extrusion
                            qcolor = Theme.flow_color(val)
                        else:
                            val = m.get('vpi', 0.0)
                            qcolor = Theme.pressure_color(val)
                            
                        r, g, b, a = qcolor.redF(), qcolor.greenF(), qcolor.blueF(), qcolor.alphaF()
                        print_color.extend([[r, g, b, a], [r, g, b, a]])
            self._full_print_color = np.array(print_color, dtype=np.float32)
"""
# insert before _update_geometry
content = content.replace("        def _update_geometry(self):", recompute_code + "        def _update_geometry(self):")


# 8. ensure _recompute_colors is called in set_all_moves
set_all = """        def set_all_moves(self, all_moves):
            self._all_moves = all_moves
            self._current_layer = 0
            self._precompute_arrays()
            self._update_geometry()"""
            
set_all_new = """        def set_all_moves(self, all_moves):
            self._all_moves = all_moves
            self._current_layer = 0
            self._precompute_arrays()
            self._recompute_colors()
            self._update_geometry()"""
content = content.replace(set_all, set_all_new)

with open("src/ui/widgets/layer_viewer_widget.py", "w") as f:
    f.write(content)

print("Applied viewer changes")
