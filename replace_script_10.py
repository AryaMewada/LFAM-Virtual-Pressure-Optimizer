import re

with open('src/slicer/gcode_generator.py', 'r') as f:
    content = f.read()

replacement = """
                    # Travel to start
                    lines.append(f"G0 X{pts[0][0]:.3f} Y{pts[0][1]:.3f} F{self.travel_speed}")
                    lines.append(f"G0 Z{layer.z_height:.3f} F{self.travel_speed}") # Un-hop
                    current_x, current_y = pts[0][0], pts[0][1]
"""

content = content.replace('                    # Travel to start\n                    lines.append(f"G0 X{pts[0][0]:.3f} Y{pts[0][1]:.3f} F{self.travel_speed}")\n                    lines.append(f"G0 Z{layer.z_height:.3f} F{self.travel_speed}") # Un-hop', replacement.strip('\n'))

with open('src/slicer/gcode_generator.py', 'w') as f:
    f.write(content)
print("Updated gcode current pos.")
