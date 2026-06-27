import re

# move.py
with open("src/engine/parser/move.py", "r") as f:
    content = f.read()
content = content.replace("@dataclass(slots=True)", "@dataclass")
content = content.replace("class Point2D:\n    \"\"\"Represents a 2D point (X, Y).\"\"\"\n    x: float", "class Point2D:\n    \"\"\"Represents a 2D point (X, Y).\"\"\"\n    __slots__ = ['x', 'y']\n    x: float")
content = content.replace("class Point3D:\n    \"\"\"Represents a 3D point (X, Y, Z).\"\"\"\n    x: float", "class Point3D:\n    \"\"\"Represents a 3D point (X, Y, Z).\"\"\"\n    __slots__ = ['x', 'y', 'z']\n    x: float")

move_slots = "    __slots__ = ['id', 'type', 'start', 'end', 'feedrate', 'extrusion', 'extrusion_mode', 'layer', 'line_number', 'arc_center', 'arc_radius', 'arc_direction', 'original_line', 'is_travel', 'is_print', 'is_arc', 'comment', 'raw_params']\n"
content = content.replace("class Move:\n    \"\"\"Represents a single G-code movement.\"\"\"\n    id: int", f"class Move:\n    \"\"\"Represents a single G-code movement.\"\"\"\n{move_slots}    id: int")

with open("src/engine/parser/move.py", "w") as f:
    f.write(content)

# geometry_analyzer.py
with open("src/engine/analysis/geometry_analyzer.py", "r") as f:
    content = f.read()
content = content.replace("@dataclass(slots=True)", "@dataclass")
amove_slots = "    __slots__ = ['corner_angle', 'curve_radius', 'is_path_start', 'is_path_end', 'continuous_region_id', 'segment_density', 'flow_rate_change', 'speed_change']\n"
content = content.replace("class AnalyzedMove(Move):\n    \"\"\"Extended Move dataclass containing geometric analysis data.\"\"\"\n    corner_angle: float", f"class AnalyzedMove(Move):\n    \"\"\"Extended Move dataclass containing geometric analysis data.\"\"\"\n{amove_slots}    corner_angle: float")

with open("src/engine/analysis/geometry_analyzer.py", "w") as f:
    f.write(content)

# pressure_optimizer.py
with open("src/engine/optimizer/pressure_optimizer.py", "r") as f:
    content = f.read()
content = content.replace("@dataclass(slots=True)", "@dataclass")
mod_slots = "    __slots__ = ['move_id', 'type', 'value', 'description']\n"
content = content.replace("class Modification:\n    \"\"\"Represents a G-code modification to be applied.\"\"\"\n    move_id: int", f"class Modification:\n    \"\"\"Represents a G-code modification to be applied.\"\"\"\n{mod_slots}    move_id: int")

with open("src/engine/optimizer/pressure_optimizer.py", "w") as f:
    f.write(content)

print("Slots manually added for python 3.9!")
