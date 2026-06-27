import re

with open("src/engine/emitter/gcode_emitter.py", "r") as f:
    content = f.read()

old_code = """            else:
                if move.extrusion != 0.0:
                    parts.append(f"E{fmt.format(move.extrusion)}")"""

new_code = """            else:
                if move.extrusion != 0.0:
                    parts.append(f"E{fmt.format(move.extrusion)}")
                if prev_e is not None:
                    prev_e += move.extrusion"""

if old_code in content:
    content = content.replace(old_code, new_code)
    with open("src/engine/emitter/gcode_emitter.py", "w") as f:
        f.write(content)
    print("Patched emitter relative tracking successfully!")
else:
    print("Could not patch emitter relative tracking.")
