import re

with open("src/ui/widgets/layer_viewer_widget.py", "r") as f:
    content = f.read()

# Modify _LayerCanvas __init__ to add _sim_index
init_old = """            self._dragging = False
            self._last_mouse_pos = QPointF()

            # Cached bounds"""
init_new = """            self._dragging = False
            self._last_mouse_pos = QPointF()
            
            self._sim_index = -1

            # Cached bounds"""
if "self._sim_index = -1" not in content:
    content = content.replace(init_old, init_new, 1)

# Modify _safe_paintEvent to use _sim_index and draw nozzle
draw_old = """                for move in self._moves:
                    x1 = move.get('x1', 0.0)
                    y1 = move.get('y1', 0.0)
                    x2 = move.get('x2', 0.0)
                    y2 = move.get('y2', 0.0)"""

draw_new = """                # Slice moves for simulation
                moves_to_draw = self._moves if self._sim_index == -1 else self._moves[:self._sim_index + 1]
                
                nozzle_pos = None
                
                for i, move in enumerate(moves_to_draw):
                    x1 = move.get('x1', 0.0)
                    y1 = move.get('y1', 0.0)
                    x2 = move.get('x2', 0.0)
                    y2 = move.get('y2', 0.0)"""
if "moves_to_draw = self._moves" not in content:
    content = content.replace(draw_old, draw_new, 1)

# Find the end of the loop and extract nozzle pos
loop_end_old = """                        if draw_arrows:
                            color = Theme.pressure_color(bucket_idx / float(num_buckets - 1))
                            arrow_data.append((p1, p2, color))"""
loop_end_new = """                        if draw_arrows:
                            color = Theme.pressure_color(bucket_idx / float(num_buckets - 1))
                            arrow_data.append((p1, p2, color))
                            
                    if i == len(moves_to_draw) - 1:
                        nozzle_pos = p2"""
if "nozzle_pos = p2" not in content:
    content = content.replace(loop_end_old, loop_end_new, 1)
    
# Draw nozzle at the end
nozzle_draw_old = """                if arrow_data:
                    self._draw_arrows(cache_painter, arrow_data)
                    
            # Draw cache to screen"""
nozzle_draw_new = """                if arrow_data:
                    self._draw_arrows(cache_painter, arrow_data)
                    
                if nozzle_pos and self._sim_index != -1 and self._sim_index < len(self._moves) - 1:
                    cache_painter.setPen(Qt.PenStyle.NoPen)
                    cache_painter.setBrush(QBrush(QColor(Theme.SUCCESS)))
                    cache_painter.drawEllipse(nozzle_pos, 5, 5)
                    
            # Draw cache to screen"""
if "cache_painter.drawEllipse(nozzle_pos, 5, 5)" not in content:
    content = content.replace(nozzle_draw_old, nozzle_draw_new, 1)

with open("src/ui/widgets/layer_viewer_widget.py", "w") as f:
    f.write(content)
print("Patched 2D canvas")
