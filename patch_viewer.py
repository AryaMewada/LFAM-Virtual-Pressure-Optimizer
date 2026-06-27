import re

with open("src/ui/widgets/layer_viewer_widget.py", "r") as f:
    content = f.read()

# Replace the missing method calls with inlined math

old_code = """                scale, cx, cy, data_cx, data_cy, pan_x, pan_y = self._get_transforms()
                
                for move in self._moves:
                    x1 = move.get('x1', 0.0)
                    y1 = move.get('y1', 0.0)
                    x2 = move.get('x2', 0.0)
                    y2 = move.get('y2', 0.0)
                    move_type = move.get('type', 'travel')
                    vpi = move.get('vpi', 0.0)
                    
                    p1 = self._transform_point_fast(x1, y1, scale, cx, cy, data_cx, data_cy, pan_x, pan_y)
                    p2 = self._transform_point_fast(x2, y2, scale, cx, cy, data_cx, data_cy, pan_x, pan_y)"""

new_code = """                # Precompute transforms
                bounds = self._calculate_bounds()
                min_x, min_y, max_x, max_y = bounds
                extent_x = max_x - min_x
                extent_y = max_y - min_y
                w = self.width()
                h = self.height()
                scale_x = w / extent_x if extent_x > 0 else 1.0
                scale_y = h / extent_y if extent_y > 0 else 1.0
                scale = min(scale_x, scale_y) * 0.9
                cx = w / 2.0
                cy = h / 2.0
                data_cx = (min_x + max_x) / 2.0
                data_cy = (min_y + max_y) / 2.0
                eff_scale = scale * self._zoom
                pan_x = self._pan_offset.x()
                pan_y = self._pan_offset.y()
                
                for move in self._moves:
                    x1 = move.get('x1', 0.0)
                    y1 = move.get('y1', 0.0)
                    x2 = move.get('x2', 0.0)
                    y2 = move.get('y2', 0.0)
                    move_type = move.get('type', 'travel')
                    vpi = move.get('vpi', 0.0)
                    
                    px1 = cx + (x1 - data_cx) * eff_scale + pan_x
                    py1 = cy - (y1 - data_cy) * eff_scale + pan_y
                    px2 = cx + (x2 - data_cx) * eff_scale + pan_x
                    py2 = cy - (y2 - data_cy) * eff_scale + pan_y
                    
                    p1 = QPointF(px1, py1)
                    p2 = QPointF(px2, py2)"""

if old_code in content:
    content = content.replace(old_code, new_code)
    with open("src/ui/widgets/layer_viewer_widget.py", "w") as f:
        f.write(content)
    print("Patched successfully!")
else:
    print("Could not find code block to replace.")
