import re

with open("src/ui/widgets/layer_viewer_widget.py", "r") as f:
    content = f.read()

# 1. Update Init variables
init_old = """        self._sim_index = -1
        self._is_playing = False
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_sim_tick)"""
init_new = """        self._sim_time_sec = -1.0
        self._current_layer_total_time = 0.0
        self._is_playing = False
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_sim_tick)"""
content = content.replace(init_old, init_new)

# 2. Update Playback toggle and timer speed
play_old = """    def _toggle_playback(self):
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
            self._timer.setInterval(speeds[idx])"""
play_new = """    def _toggle_playback(self):
        if not self._all_moves:
            return
            
        self._is_playing = not self._is_playing
        if self._is_playing:
            self._play_btn.setText("⏸ Pause")
            if self._sim_time_sec >= self._current_layer_total_time - 0.001:
                self._sim_time_sec = 0.0
            self._timer.setInterval(16) # 60fps
            self._timer.start()
        else:
            self._play_btn.setText("▶ Play")
            self._timer.stop()
            
    def _update_timer_speed(self):
        # We handle speed internally in _on_sim_tick via multiplier now
        pass"""
content = content.replace(play_old, play_new)


# 3. Update scrub and tick logic
tick_old = """    def _on_sim_tick(self):
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
                self._toggle_playback() # auto pause at very end

    def _on_sim_scrub(self, value: int):
        self._sim_index = value
        self._update_canvases_sim()
        
    def _update_canvases_sim(self):
        self._canvas_3d._sim_index = self._sim_index
        self._canvas_3d._update_geometry()"""

tick_new = """    def _on_sim_tick(self):
        dt = 0.016
        multipliers = [1.0, 2.0, 5.0, 10.0, 50.0]
        mult = multipliers[self._speed_combo.currentIndex()]
        
        self._sim_time_sec += dt * mult
        
        if self._sim_time_sec >= self._current_layer_total_time:
            # Reached end of layer
            current_layer = self._layer_slider.value()
            if current_layer < len(self._all_moves) - 1:
                self._sim_time_sec = self._current_layer_total_time
                self._update_canvases_sim() 
                self._layer_slider.setValue(current_layer + 1)
                self._sim_time_sec = 0.0
            else:
                self._sim_time_sec = self._current_layer_total_time
                self._update_canvases_sim()
                self._toggle_playback() # auto pause at very end
        else:
            self._sim_slider.blockSignals(True)
            if self._current_layer_total_time > 0:
                perc = int((self._sim_time_sec / self._current_layer_total_time) * 1000)
                self._sim_slider.setValue(perc)
            self._sim_slider.blockSignals(False)
            self._update_canvases_sim()

    def _on_sim_scrub(self, value: int):
        self._sim_time_sec = (value / 1000.0) * self._current_layer_total_time
        self._update_canvases_sim()
        
    def _update_canvases_sim(self):
        self._canvas_3d._sim_time_sec = self._sim_time_sec
        self._canvas_3d._update_geometry()"""

content = content.replace(tick_old, tick_new)


# 4. Update set_layer to use time
set_layer_old = """        num_moves = 0
        if 0 <= layer_number < len(self._all_moves):
            num_moves = len(self._all_moves[layer_number])
            
        # Reset simulation state
        if not self._is_playing:
            self._sim_index = num_moves - 1
            
        self._sim_slider.blockSignals(True)
        self._sim_slider.setRange(0, max(0, num_moves - 1))
        self._sim_slider.setValue(max(0, self._sim_index))
        self._sim_slider.blockSignals(False)

        self._canvas_3d._sim_index = self._sim_index
        self._canvas_3d.set_layer(layer_number)"""

set_layer_new = """        # Tell 3D canvas first so we can get layer duration
        self._canvas_3d.set_layer(layer_number)
        
        self._current_layer_total_time = self._canvas_3d.get_current_layer_duration()
            
        # Reset simulation state
        if not self._is_playing:
            self._sim_time_sec = self._current_layer_total_time
            
        self._sim_slider.blockSignals(True)
        self._sim_slider.setRange(0, 1000)
        perc = 1000
        if self._current_layer_total_time > 0 and self._sim_time_sec >= 0:
            perc = int((min(self._sim_time_sec, self._current_layer_total_time) / self._current_layer_total_time) * 1000)
        self._sim_slider.setValue(perc)
        self._sim_slider.blockSignals(False)

        self._canvas_3d._sim_time_sec = self._sim_time_sec
        self._canvas_3d._update_geometry()"""

content = content.replace(set_layer_old, set_layer_new)


# 5. Play from start update
start_old = """    def _play_from_start(self):
        if not self._all_moves:
            return
        self._layer_slider.setValue(0)
        self._sim_index = -1
        if not self._is_playing:
            self._toggle_playback()"""

start_new = """    def _play_from_start(self):
        if not self._all_moves:
            return
        self._layer_slider.setValue(0)
        self._sim_time_sec = 0.0
        if not self._is_playing:
            self._toggle_playback()"""

content = content.replace(start_old, start_new)

# 6. Update _LayerCanvas3D to track time and interpolate
canvas_old = """            self._sim_index = -1
            
            # Pre-computed arrays
            self._full_print_pos = np.zeros((0, 3), dtype=np.float32)
            self._full_print_color = np.zeros((0, 4), dtype=np.float32)
            self._full_travel_pos = np.zeros((0, 3), dtype=np.float32)
            self._full_travel_color = np.zeros((0, 4), dtype=np.float32)
            
            # Layer indices
            self._print_layer_indices = []
            self._travel_layer_indices = []
            
        def set_all_moves(self, all_moves):
            self._all_moves = all_moves
            self._current_layer = 0
            self._precompute_arrays()
            self._update_geometry()
            
        def _precompute_arrays(self):
            print_pos = []
            print_color = []
            travel_pos = []
            
            self._print_layer_indices = []
            self._travel_layer_indices = []
            
            for layer in self._all_moves:
                for m in layer:
                    x1, y1, z1 = m.get('x1',0), m.get('y1',0), m.get('z1',0)
                    x2, y2, z2 = m.get('x2',0), m.get('y2',0), m.get('z2',0)
                    
                    if m.get('type') == 'travel':
                        travel_pos.extend([[x1, y1, z1], [x2, y2, z2]])
                    else:
                        print_pos.extend([[x1, y1, z1], [x2, y2, z2]])
                        vpi = m.get('vpi', 0.0)
                        qcolor = Theme.pressure_color(vpi)
                        r, g, b, a = qcolor.redF(), qcolor.greenF(), qcolor.blueF(), qcolor.alphaF()
                        print_color.extend([[r, g, b, a], [r, g, b, a]])
                        
                self._print_layer_indices.append(len(print_pos))
                self._travel_layer_indices.append(len(travel_pos))
                
            self._full_print_pos = np.array(print_pos, dtype=np.float32)
            self._full_print_color = np.array(print_color, dtype=np.float32)
            self._full_travel_pos = np.array(travel_pos, dtype=np.float32)
            
            if travel_pos:
                travel_c = QColor(Theme.TEXT_MUTED)
                tc = [travel_c.redF(), travel_c.greenF(), travel_c.blueF(), 0.5]
                self._full_travel_color = np.tile(tc, (len(travel_pos), 1)).astype(np.float32)
            else:
                self._full_travel_color = np.zeros((0, 4), dtype=np.float32)

        def set_layer(self, layer_number: int):
            self._current_layer = layer_number
            # update geometry is called by parent"""

canvas_new = """            self._sim_time_sec = -1.0
            
            # Pre-computed arrays
            self._full_print_pos = np.zeros((0, 3), dtype=np.float32)
            self._full_print_color = np.zeros((0, 4), dtype=np.float32)
            self._full_travel_pos = np.zeros((0, 3), dtype=np.float32)
            self._full_travel_color = np.zeros((0, 4), dtype=np.float32)
            
            # Layer indices
            self._print_layer_indices = []
            self._travel_layer_indices = []
            
            # Physics time arrays
            self._layer_durations = []
            self._move_cum_times = [] # List of numpy arrays, one per layer
            self._print_cum_times = [] # same
            self._travel_cum_times = [] # same
            
        def get_current_layer_duration(self):
            if 0 <= self._current_layer < len(self._layer_durations):
                return self._layer_durations[self._current_layer]
            return 0.0
            
        def set_all_moves(self, all_moves):
            self._all_moves = all_moves
            self._current_layer = 0
            self._precompute_arrays()
            self._update_geometry()
            
        def _precompute_arrays(self):
            print_pos = []
            print_color = []
            travel_pos = []
            
            self._print_layer_indices = []
            self._travel_layer_indices = []
            
            self._layer_durations = []
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
                        
                self._print_layer_indices.append(len(print_pos))
                self._travel_layer_indices.append(len(travel_pos))
                
                self._layer_durations.append(layer_t)
                self._move_cum_times.append(np.array(layer_times, dtype=np.float32))
                self._print_cum_times.append(np.array(p_times, dtype=np.float32))
                self._travel_cum_times.append(np.array(t_times, dtype=np.float32))
                
            self._full_print_pos = np.array(print_pos, dtype=np.float32)
            self._full_print_color = np.array(print_color, dtype=np.float32)
            self._full_travel_pos = np.array(travel_pos, dtype=np.float32)
            
            if travel_pos:
                travel_c = QColor(Theme.TEXT_MUTED)
                tc = [travel_c.redF(), travel_c.greenF(), travel_c.blueF(), 0.5]
                self._full_travel_color = np.tile(tc, (len(travel_pos), 1)).astype(np.float32)
            else:
                self._full_travel_color = np.zeros((0, 4), dtype=np.float32)

        def set_layer(self, layer_number: int):
            self._current_layer = layer_number"""

content = content.replace(canvas_old, canvas_new)

# 7. Complete _update_geometry rewrite to use time interpolation
update_old = """        def _update_geometry(self):
            # Support simulation slicing
            if self._sim_index != -1 and self._current_layer < len(self._all_moves):
                # The total index is the index of previous layers + the current layer's sim index
                prev_p_idx = self._print_layer_indices[self._current_layer - 1] if self._current_layer > 0 else 0
                prev_t_idx = self._travel_layer_indices[self._current_layer - 1] if self._current_layer > 0 else 0
                
                # We need to figure out how many print/travel moves are in the current layer up to _sim_index
                # We can just count them.
                layer_moves = self._all_moves[self._current_layer]
                sim_moves = layer_moves[:self._sim_index + 1]
                
                p_count = sum(2 for m in sim_moves if m.get('type') != 'travel')
                t_count = sum(2 for m in sim_moves if m.get('type') == 'travel')
                
                p_idx = prev_p_idx + p_count
                t_idx = prev_t_idx + t_count
                
                # Update nozzle marker
                if sim_moves:
                    last_m = sim_moves[-1]
                    nx, ny, nz = last_m.get('x2',0), last_m.get('y2',0), last_m.get('z2',0)
                    nc = QColor(Theme.SUCCESS)
                    self._nozzle_item.setData(pos=np.array([[nx, ny, nz]], dtype=np.float32), 
                                              color=np.array([[nc.redF(), nc.greenF(), nc.blueF(), 1.0]], dtype=np.float32))
                else:
                    self._nozzle_item.setData(pos=np.zeros((0,3), dtype=np.float32))
            else:
                self._nozzle_item.setData(pos=np.zeros((0,3), dtype=np.float32))
                p_idx = self._print_layer_indices[self._current_layer]
                t_idx = self._travel_layer_indices[self._current_layer]

            if p_idx > 0:
                self._print_item.setData(pos=self._full_print_pos[:p_idx], color=self._full_print_color[:p_idx])
            else:
                self._print_item.setData(pos=np.zeros((0,3), dtype=np.float32), color=np.zeros((0,4), dtype=np.float32))
                
            if t_idx > 0:
                self._travel_item.setData(pos=self._full_travel_pos[:t_idx], color=self._full_travel_color[:t_idx])
            else:
                self._travel_item.setData(pos=np.zeros((0,3), dtype=np.float32), color=np.zeros((0,4), dtype=np.float32))"""

update_new = """        def _update_geometry(self):
            if self._current_layer >= len(self._all_moves) or self._current_layer < 0:
                self._print_item.setData(pos=np.zeros((0,3), dtype=np.float32), color=np.zeros((0,4), dtype=np.float32))
                self._travel_item.setData(pos=np.zeros((0,3), dtype=np.float32), color=np.zeros((0,4), dtype=np.float32))
                self._nozzle_item.setData(pos=np.zeros((0,3), dtype=np.float32))
                return
                
            prev_p_idx = self._print_layer_indices[self._current_layer - 1] if self._current_layer > 0 else 0
            prev_t_idx = self._travel_layer_indices[self._current_layer - 1] if self._current_layer > 0 else 0
            
            p_idx = self._print_layer_indices[self._current_layer]
            t_idx = self._travel_layer_indices[self._current_layer]
            
            is_simulating = (0 <= self._sim_time_sec < self.get_current_layer_duration() - 0.001)
            
            if is_simulating:
                t = self._sim_time_sec
                
                # Find which move we are in
                move_idx = np.searchsorted(self._move_cum_times[self._current_layer], t)
                if move_idx >= len(self._all_moves[self._current_layer]):
                    move_idx = len(self._all_moves[self._current_layer]) - 1
                
                # Find how many print/travel moves are fully completed
                p_count = np.searchsorted(self._print_cum_times[self._current_layer], t) * 2
                t_count = np.searchsorted(self._travel_cum_times[self._current_layer], t) * 2
                
                p_idx = prev_p_idx + p_count
                t_idx = prev_t_idx + t_count
                
                m = self._all_moves[self._current_layer][move_idx]
                
                # Interpolate nozzle position
                start_t = self._move_cum_times[self._current_layer][move_idx - 1] if move_idx > 0 else 0.0
                end_t = self._move_cum_times[self._current_layer][move_idx]
                duration = max(end_t - start_t, 0.0001)
                frac = (t - start_t) / duration
                frac = max(0.0, min(1.0, frac))
                
                x1, y1, z1 = m.get('x1',0), m.get('y1',0), m.get('z1',0)
                x2, y2, z2 = m.get('x2',0), m.get('y2',0), m.get('z2',0)
                
                nx = x1 + (x2 - x1) * frac
                ny = y1 + (y2 - y1) * frac
                nz = z1 + (z2 - z1) * frac
                
                # We need to append the partial move to the array data
                # But PyQTGraph setData is fast, so we can just concat the partial line dynamically
                partial_pos = np.array([[x1, y1, z1], [nx, ny, nz]], dtype=np.float32)
                
                if m.get('type') == 'travel':
                    # Has partial travel
                    t_pos = np.concatenate((self._full_travel_pos[:t_idx], partial_pos)) if t_idx > 0 else partial_pos
                    tc = [Theme.TEXT_MUTED_QCOLOR.redF(), Theme.TEXT_MUTED_QCOLOR.greenF(), Theme.TEXT_MUTED_QCOLOR.blueF(), 0.5]
                    t_col = np.concatenate((self._full_travel_color[:t_idx], np.tile(tc, (2,1)).astype(np.float32))) if t_idx > 0 else np.tile(tc, (2,1)).astype(np.float32)
                    
                    self._travel_item.setData(pos=t_pos, color=t_col)
                    if p_idx > 0:
                        self._print_item.setData(pos=self._full_print_pos[:p_idx], color=self._full_print_color[:p_idx])
                    else:
                        self._print_item.setData(pos=np.zeros((0,3), dtype=np.float32), color=np.zeros((0,4), dtype=np.float32))
                else:
                    # Has partial print
                    p_pos = np.concatenate((self._full_print_pos[:p_idx], partial_pos)) if p_idx > 0 else partial_pos
                    qcolor = Theme.pressure_color(m.get('vpi', 0.0))
                    pc = [qcolor.redF(), qcolor.greenF(), qcolor.blueF(), qcolor.alphaF()]
                    p_col = np.concatenate((self._full_print_color[:p_idx], np.tile(pc, (2,1)).astype(np.float32))) if p_idx > 0 else np.tile(pc, (2,1)).astype(np.float32)
                    
                    self._print_item.setData(pos=p_pos, color=p_col)
                    if t_idx > 0:
                        self._travel_item.setData(pos=self._full_travel_pos[:t_idx], color=self._full_travel_color[:t_idx])
                    else:
                        self._travel_item.setData(pos=np.zeros((0,3), dtype=np.float32), color=np.zeros((0,4), dtype=np.float32))

                nc = QColor(Theme.SUCCESS)
                self._nozzle_item.setData(pos=np.array([[nx, ny, nz]], dtype=np.float32), 
                                          color=np.array([[nc.redF(), nc.greenF(), nc.blueF(), 1.0]], dtype=np.float32))
            else:
                # Show full layer
                if p_idx > 0:
                    self._print_item.setData(pos=self._full_print_pos[:p_idx], color=self._full_print_color[:p_idx])
                else:
                    self._print_item.setData(pos=np.zeros((0,3), dtype=np.float32), color=np.zeros((0,4), dtype=np.float32))
                    
                if t_idx > 0:
                    self._travel_item.setData(pos=self._full_travel_pos[:t_idx], color=self._full_travel_color[:t_idx])
                else:
                    self._travel_item.setData(pos=np.zeros((0,3), dtype=np.float32), color=np.zeros((0,4), dtype=np.float32))
                    
                # Nozzle at the very end
                if len(self._all_moves[self._current_layer]) > 0:
                    last_m = self._all_moves[self._current_layer][-1]
                    nx, ny, nz = last_m.get('x2',0), last_m.get('y2',0), last_m.get('z2',0)
                    nc = QColor(Theme.SUCCESS)
                    self._nozzle_item.setData(pos=np.array([[nx, ny, nz]], dtype=np.float32), 
                                              color=np.array([[nc.redF(), nc.greenF(), nc.blueF(), 1.0]], dtype=np.float32))
                else:
                    self._nozzle_item.setData(pos=np.zeros((0,3), dtype=np.float32))"""

# Wait, `update_old` might have `p_idx = self._print_layer_indices[self._current_layer]` in the `else` block which I previously wrote.
# I will just use regex to replace the entire `_update_geometry` method.
import re
content = re.sub(r'def _update_geometry\(self\):.*?(?=\n\n|\Z)', update_new, content, flags=re.DOTALL)


# Let's write the theme color helper for TEXT_MUTED if it doesn't exist
if "Theme.TEXT_MUTED_QCOLOR = QColor(Theme.TEXT_MUTED)" not in content:
    content = content.replace("class _LayerCanvas3D", "Theme.TEXT_MUTED_QCOLOR = QColor(Theme.TEXT_MUTED)\n    class _LayerCanvas3D")

with open("src/ui/widgets/layer_viewer_widget.py", "w") as f:
    f.write(content)

print("Patched physics engine")
