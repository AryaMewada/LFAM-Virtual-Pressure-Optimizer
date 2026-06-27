from __future__ import annotations
from typing import List, Tuple
from src.engine.parser.move import Move, Point3D
import copy

class MoveSplitter:
    """Splits a single move into multiple segments."""
    
    def __init__(self):
        self.next_id = 999999  # Temporary ID offset for split moves

    def split_move(self, move: Move, n_segments: int) -> List[Move]:
        """Splits a linear move into N equal segments."""
        if n_segments <= 1 or move.is_arc or not move.is_print:
            return [copy.deepcopy(move)]
            
        segments = []
        dx = (move.end.x - move.start.x) / n_segments
        dy = (move.end.y - move.start.y) / n_segments
        dz = (move.end.z - move.start.z) / n_segments
        de = move.extrusion / n_segments
        
        curr_start = move.start
        
        for i in range(n_segments):
            self.next_id += 1
            curr_end = Point3D(
                curr_start.x + dx,
                curr_start.y + dy,
                curr_start.z + dz
            )
            
            # Ensure exact end point on last segment to avoid float rounding errors
            if i == n_segments - 1:
                curr_end = move.end
                
            new_move = copy.deepcopy(move)
            new_move.id = self.next_id
            new_move.start = curr_start
            new_move.end = curr_end
            new_move.extrusion = de
            
            # Clear original raw params and line for derived moves
            new_move.original_line = f"; split segment {i+1}/{n_segments} of original id {move.id}"
            new_move.raw_params = {}
            
            segments.append(new_move)
            curr_start = curr_end
            
        return segments

    def split_at_point(self, move: Move, fraction: float) -> Tuple[Move, Move]:
        """Splits a linear move at a fraction (0-1) along its length."""
        if fraction <= 0.0 or fraction >= 1.0 or move.is_arc or not move.is_print:
            return copy.deepcopy(move), copy.deepcopy(move) # Dummy fallback
            
        self.next_id += 1
        id1 = self.next_id
        self.next_id += 1
        id2 = self.next_id
        
        mid_x = move.start.x + (move.end.x - move.start.x) * fraction
        mid_y = move.start.y + (move.end.y - move.start.y) * fraction
        mid_z = move.start.z + (move.end.z - move.start.z) * fraction
        mid_e = move.extrusion * fraction
        
        mid_pt = Point3D(mid_x, mid_y, mid_z)
        
        m1 = copy.deepcopy(move)
        m1.id = id1
        m1.end = mid_pt
        m1.extrusion = mid_e
        m1.original_line = f"; split part 1 of original id {move.id}"
        m1.raw_params = {}
        
        m2 = copy.deepcopy(move)
        m2.id = id2
        m2.start = mid_pt
        m2.extrusion = move.extrusion - mid_e
        m2.original_line = f"; split part 2 of original id {move.id}"
        m2.raw_params = {}
        
        return m1, m2
