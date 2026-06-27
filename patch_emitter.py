import re

with open("src/engine/emitter/gcode_emitter.py", "r") as f:
    content = f.read()

old_code = """        for move in moves:
            # Output RAW or COMMENT as-is
            if move.type in (MoveType.RAW, MoveType.OTHER, MoveType.COMMENT):
                lines.append(move.original_line)
                # Keep state sync
                prev_x = move.end.x
                prev_y = move.end.y
                prev_z = move.end.z
                continue"""

new_code = """        for move in moves:
            # Output RAW or COMMENT as-is
            if move.type in (MoveType.RAW, MoveType.OTHER, MoveType.COMMENT):
                lines.append(move.original_line)
                # Keep state sync
                prev_x = move.end.x
                prev_y = move.end.y
                prev_z = move.end.z
                
                # Critical bug fix: Sync absolute E tracker when G92 is emitted
                if move.type == MoveType.OTHER and 'G92' in move.raw_params:
                    params = move.raw_params['G92']
                    if 'E' in params:
                        prev_e = params['E']
                continue"""

if old_code in content:
    content = content.replace(old_code, new_code)
    with open("src/engine/emitter/gcode_emitter.py", "w") as f:
        f.write(content)
    print("Patched emitter successfully!")
else:
    print("Could not patch emitter.")
