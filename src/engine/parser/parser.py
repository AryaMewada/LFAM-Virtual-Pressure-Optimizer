from __future__ import annotations
import re
import os
from typing import List, Dict, Any, Tuple
from src.engine.parser.move import Move, MoveType, Point3D, Point2D
from src.engine.parser.arc_utils import compute_arc_center, compute_arc_radius

class GCodeParser:
    """Parser for converting G-code text into a sequence of Move objects."""
    
    def __init__(self):
        self.reset_state()

    def reset_state(self):
        """Resets the parser's machine state."""
        self.current_x = 0.0
        self.current_y = 0.0
        self.current_z = 0.0
        self.current_e = 0.0
        self.feedrate = 0.0
        self.absolute_mode = True  # G90
        self.extrusion_absolute = True  # M82
        self.layer = 0
        self.move_id_counter = 0

    def parse_file(self, filepath: str) -> List[Move]:
        """Parses a G-code file line by line."""
        moves = []
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")
            
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_number, line in enumerate(f, start=1):
                move = self._parse_line(line, line_number)
                if move:
                    moves.append(move)
        return moves

    def parse(self, gcode_text: str) -> List[Move]:
        """Parses a G-code string."""
        moves = []
        for line_number, line in enumerate(gcode_text.splitlines(), start=1):
            move = self._parse_line(line, line_number)
            if move:
                moves.append(move)
        return moves

    def _parse_line(self, line: str, line_number: int) -> Move | None:
        """Parses a single line of G-code and returns a Move object if applicable."""
        original_line = line.rstrip('\n\r')
        line = line.strip()
        
        # Handle empty lines
        if not line:
            return None
            
        # Parse comments
        comment = ""
        if ';' in line:
            parts = line.split(';', 1)
            line = parts[0].strip()
            comment = parts[1].strip()
            
            # Layer detection
            if "LAYER:" in comment.upper() or comment.upper() == "LAYER":
                self.layer += 1
                
        # If line only contained a comment
        if not line:
            return self._create_comment_move(original_line, comment, line_number)

        # Tokenize
        tokens = line.split()
        if not tokens:
            return self._create_comment_move(original_line, comment, line_number)
            
        command = tokens[0].upper()
        params = self._extract_params(tokens[1:])
        
        # Handle state changes
        if command == 'G90':
            self.absolute_mode = True
            return self._create_raw_move(MoveType.OTHER, original_line, comment, line_number, command, params)
        elif command == 'G91':
            self.absolute_mode = False
            return self._create_raw_move(MoveType.OTHER, original_line, comment, line_number, command, params)
        elif command == 'M82':
            self.extrusion_absolute = True
            return self._create_raw_move(MoveType.OTHER, original_line, comment, line_number, command, params)
        elif command == 'M83':
            self.extrusion_absolute = False
            return self._create_raw_move(MoveType.OTHER, original_line, comment, line_number, command, params)
        elif command == 'G92':
            if 'X' in params: self.current_x = params['X']
            if 'Y' in params: self.current_y = params['Y']
            if 'Z' in params: self.current_z = params['Z']
            if 'E' in params: self.current_e = params['E']
            return self._create_raw_move(MoveType.OTHER, original_line, comment, line_number, command, params)
        elif command == 'G28':
            self.current_x = 0.0
            self.current_y = 0.0
            self.current_z = 0.0
            return self._create_raw_move(MoveType.OTHER, original_line, comment, line_number, command, params)
            
        # Handle motion commands
        if command in ('G0', 'G1', 'G2', 'G3'):
            return self._process_motion(command, params, original_line, comment, line_number)
            
        # Unknown/Other commands
        return self._create_raw_move(MoveType.RAW, original_line, comment, line_number, command, params)

    def _extract_params(self, tokens: List[str]) -> Dict[str, float]:
        """Extracts parameters like X10.5 from tokens."""
        params = {}
        for token in tokens:
            token = token.upper()
            match = re.match(r'([A-Z])([-+]?\d*\.?\d+)', token)
            if match:
                key = match.group(1)
                val = float(match.group(2))
                params[key] = val
        return params

    def _process_motion(self, command: str, params: Dict[str, float], original_line: str, comment: str, line_number: int) -> Move:
        """Processes G0, G1, G2, G3 commands and creates a Move object."""
        start_pt = Point3D(self.current_x, self.current_y, self.current_z)
        
        # Update Feedrate
        if 'F' in params:
            self.feedrate = params['F']
            
        # Determine target position
        target_x = self.current_x
        target_y = self.current_y
        target_z = self.current_z
        
        if self.absolute_mode:
            if 'X' in params: target_x = params['X']
            if 'Y' in params: target_y = params['Y']
            if 'Z' in params: target_z = params['Z']
        else:
            if 'X' in params: target_x += params['X']
            if 'Y' in params: target_y += params['Y']
            if 'Z' in params: target_z += params['Z']
            
        # Z-hop based layer increment heuristic if not explicitly commented
        if target_z > self.current_z and ('X' in params or 'Y' in params or 'E' in params):
            # Only increment if we also moved in XY or extruded, simple heuristic
            pass # We rely on comments for reliable layer detection as per requirements, but we can do it if Z increases.
        
        if target_z > self.current_z and target_z != self.current_z:
            # The prompt asks: "increment layer on Z increases"
            # It's tricky because Z-hop is a Z increase but not a layer change. 
            # We'll just increment it for any positive Z change as a basic implementation.
            if not ('E' in params and params['E'] < 0): # Rough check against retract + zhop
                 pass
                 # Actually, it's better to stick to comments or just any Z increase
        
        if target_z > self.current_z and command in ('G0', 'G1'):
            # Only increment if it looks like a layer change. Let's just do it on any Z increase.
            self.layer += 1
            
        # Determine extrusion
        extrusion_delta = 0.0
        if 'E' in params:
            if self.extrusion_absolute:
                extrusion_delta = params['E'] - self.current_e
                self.current_e = params['E']
            else:
                extrusion_delta = params['E']
                self.current_e += extrusion_delta
                
        end_pt = Point3D(target_x, target_y, target_z)
        
        # Determine move type properties
        is_travel = extrusion_delta <= 0.0
        is_print = extrusion_delta > 0.0
        is_arc = command in ('G2', 'G3')
        
        move_type = MoveType.G1
        if command == 'G0' or (command == 'G1' and is_travel):
            move_type = MoveType.TRAVEL if is_travel else MoveType.G1
        elif command == 'G1' and is_print:
            move_type = MoveType.G1
        elif command == 'G2':
            move_type = MoveType.G2
        elif command == 'G3':
            move_type = MoveType.G3
            
        if extrusion_delta < 0.0:
            move_type = MoveType.RETRACT
            
        # Handle Arcs
        arc_center = None
        arc_radius = None
        arc_direction = None
        
        if is_arc:
            i_offset = params.get('I', 0.0)
            j_offset = params.get('J', 0.0)
            arc_center = compute_arc_center(start_pt, end_pt, i_offset, j_offset)
            arc_radius = compute_arc_radius(arc_center, start_pt)
            arc_direction = 'CW' if command == 'G2' else 'CCW'

        self.move_id_counter += 1
        move = Move(
            id=self.move_id_counter,
            type=move_type,
            start=start_pt,
            end=end_pt,
            feedrate=self.feedrate,
            extrusion=extrusion_delta,
            extrusion_mode='absolute' if self.extrusion_absolute else 'relative',
            layer=self.layer,
            line_number=line_number,
            arc_center=arc_center,
            arc_radius=arc_radius,
            arc_direction=arc_direction,
            original_line=original_line,
            is_travel=is_travel,
            is_print=is_print,
            is_arc=is_arc,
            comment=comment,
            raw_params=params
        )
        
        # Update state
        self.current_x = target_x
        self.current_y = target_y
        self.current_z = target_z
        
        return move

    def _create_comment_move(self, original_line: str, comment: str, line_number: int) -> Move:
        """Creates a Move object for a comment-only line."""
        self.move_id_counter += 1
        pt = Point3D(self.current_x, self.current_y, self.current_z)
        return Move(
            id=self.move_id_counter,
            type=MoveType.COMMENT,
            start=pt,
            end=pt,
            feedrate=self.feedrate,
            extrusion=0.0,
            extrusion_mode='absolute' if self.extrusion_absolute else 'relative',
            layer=self.layer,
            line_number=line_number,
            original_line=original_line,
            comment=comment
        )
        
    def _create_raw_move(self, move_type: MoveType, original_line: str, comment: str, line_number: int, command: str, params: Dict[str, float]) -> Move:
        """Creates a Move object for non-motion commands."""
        self.move_id_counter += 1
        pt = Point3D(self.current_x, self.current_y, self.current_z)
        return Move(
            id=self.move_id_counter,
            type=move_type,
            start=pt,
            end=pt,
            feedrate=self.feedrate,
            extrusion=0.0,
            extrusion_mode='absolute' if self.extrusion_absolute else 'relative',
            layer=self.layer,
            line_number=line_number,
            original_line=original_line,
            comment=comment,
            raw_params={command: params}
        )
