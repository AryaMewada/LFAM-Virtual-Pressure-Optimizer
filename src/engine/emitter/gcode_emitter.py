from __future__ import annotations
from typing import List, Dict
from src.engine.parser.move import Move, MoveType
from src.engine.optimizer.pressure_optimizer import Modification

class GCodeEmitter:
    """Converts a sequence of Move objects back into G-code text."""
    
    def __init__(self, precision: int = 4):
        self.precision = precision

    def emit(self, moves: List[Move], modifications: List[Modification] = None) -> str:
        """Converts moves to a single G-code string."""
        if modifications is None:
            modifications = []
            
        mod_map = {}
        for mod in modifications:
            if mod.move_id not in mod_map:
                mod_map[mod.move_id] = []
            mod_map[mod.move_id].append(mod)
            
        lines = []
        
        # Header block
        lines.append("; =========================================")
        lines.append("; LFAM Optimizer - Optimized G-code")
        if modifications:
            lines.append(f"; Total Modifications: {len(modifications)}")
        lines.append("; =========================================\n")
        
        prev_x, prev_y, prev_z, prev_e, prev_f = None, None, None, None, None
        fmt = f"{{:.{self.precision}f}}"
        
        for move in moves:
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
                continue
                
            cmd = ""
            if move.type == MoveType.G0 or move.is_travel:
                cmd = "G0"
            elif move.type == MoveType.G1 or move.type == MoveType.RETRACT:
                cmd = "G1"
            elif move.type == MoveType.G2:
                cmd = "G2"
            elif move.type == MoveType.G3:
                cmd = "G3"
                
            if not cmd:
                lines.append(move.original_line)
                continue
                
            parts = [cmd]
            
            # Format XYZ
            if prev_x != move.end.x:
                parts.append(f"X{fmt.format(move.end.x)}")
                prev_x = move.end.x
            if prev_y != move.end.y:
                parts.append(f"Y{fmt.format(move.end.y)}")
                prev_y = move.end.y
            if prev_z != move.end.z:
                parts.append(f"Z{fmt.format(move.end.z)}")
                prev_z = move.end.z
                
            # Arcs
            if move.is_arc and move.arc_center:
                # I and J are usually relative to start point
                i_val = move.arc_center.x - move.start.x
                j_val = move.arc_center.y - move.start.y
                parts.append(f"I{fmt.format(i_val)}")
                parts.append(f"J{fmt.format(j_val)}")
                
            # Extrusion
            # In absolute mode, E is accumulated. The Move object stores extrusion_delta in .extrusion
            # and it seems we need absolute E if we're emitting absolute.
            # Wait, the parser tracks extrusion_absolute mode. 
            # If the mode is absolute, the E value in the output should be the absolute position.
            # But we don't have absolute E readily available in the Move unless we track it during emit.
            # Let's accumulate E.
            if move.extrusion_mode == 'absolute':
                if prev_e is None:
                    prev_e = 0.0
                current_e = prev_e + move.extrusion
                # Only output if extrusion changed (delta != 0)
                if move.extrusion != 0.0:
                    parts.append(f"E{fmt.format(current_e)}")
                    prev_e = current_e
            else:
                if move.extrusion != 0.0:
                    parts.append(f"E{fmt.format(move.extrusion)}")
                if prev_e is not None:
                    prev_e += move.extrusion
                    
            # Feedrate
            if prev_f != move.feedrate and move.feedrate > 0:
                # Feedrate usually doesn't need high precision
                parts.append(f"F{move.feedrate:.0f}")
                prev_f = move.feedrate
                
            line_str = " ".join(parts)
            
            # Add inline comments for modifications
            if move.id in mod_map:
                mod_comments = []
                for m in mod_map[move.id]:
                    mod_comments.append(f"[{m.type}] - {m.reason}")
                line_str += f" ; LFAM-OPT: {', '.join(mod_comments)}"
            elif move.comment:
                line_str += f" ; {move.comment}"
                
            lines.append(line_str)
            
        return "\n".join(lines) + "\n"

    def emit_to_file(self, moves: List[Move], modifications: List[Modification], filepath: str):
        """Emits G-code and writes directly to a file."""
        gcode_text = self.emit(moves, modifications)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(gcode_text)
