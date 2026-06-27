import re

with open("src/ui/widgets/layer_viewer_widget.py", "r") as f:
    content = f.read()

old_code = """                scale = min(scale_x, scale_y) * 0.9
                cx = w / 2.0
                cy = h / 2.0
                data_cx = (min_x + max_x) / 2.0
                data_cy = (min_y + max_y) / 2.0"""

new_code = """                scale = min(scale_x, scale_y) * 0.9
                cx = w / 2.0
                cy = h / 2.0
                data_cx = (min_x + max_x) / 2.0
                data_cy = (min_y + max_y) / 2.0
                
                with open("viewer_debug.txt", "w") as dbgf:
                    dbgf.write(f"w: {w}, h: {h}\\n")
                    dbgf.write(f"min_x: {min_x}, max_x: {max_x}, extent_x: {extent_x}, scale_x: {scale_x}\\n")
                    dbgf.write(f"min_y: {min_y}, max_y: {max_y}, extent_y: {extent_y}, scale_y: {scale_y}\\n")
                    dbgf.write(f"scale: {scale}, zoom: {self._zoom}\\n")
                    dbgf.write(f"moves len: {len(self._moves)}\\n")
                    if self._moves:
                        dbgf.write(f"first move: {self._moves[0]}\\n")
"""

if old_code in content:
    content = content.replace(old_code, new_code)
    with open("src/ui/widgets/layer_viewer_widget.py", "w") as f:
        f.write(content)
    print("Injected debug code!")
else:
    print("Could not inject debug code.")
