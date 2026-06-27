from __future__ import annotations
from dataclasses import dataclass
from typing import List
from src.engine.parser.move import Move

@dataclass
class ExtrusionPath:
    """Represents a continuous path of extrusion (print moves)."""
    id: int
    start_index: int
    end_index: int
    move_count: int
    total_length: float
    total_extrusion: float
    layer: int
    path_type: str = "unknown"

class PathDetector:
    """Detects continuous extrusion paths separated by travel moves."""
    
    def detect_paths(self, moves: List[Move]) -> List[ExtrusionPath]:
        """Groups consecutive print moves into paths."""
        paths = []
        
        in_path = False
        start_idx = 0
        move_count = 0
        total_length = 0.0
        total_extrusion = 0.0
        current_layer = 0
        path_id = 0
        current_type = "unknown"
        
        for i, move in enumerate(moves):
            # Try to detect path type from comments
            if move.comment:
                comment_lower = move.comment.lower()
                if any(k in comment_lower for k in ['perimeter', 'wall']):
                    current_type = "perimeter"
                elif any(k in comment_lower for k in ['infill', 'fill']):
                    current_type = "infill"
                    
            if move.is_print:
                if not in_path:
                    in_path = True
                    start_idx = i
                    move_count = 0
                    total_length = 0.0
                    total_extrusion = 0.0
                    current_layer = move.layer
                    
                move_count += 1
                total_length += move.length
                total_extrusion += move.extrusion
            else:
                if in_path:
                    path_id += 1
                    paths.append(ExtrusionPath(
                        id=path_id,
                        start_index=start_idx,
                        end_index=i - 1,
                        move_count=move_count,
                        total_length=total_length,
                        total_extrusion=total_extrusion,
                        layer=current_layer,
                        path_type=current_type
                    ))
                    in_path = False
                    
        # Handle path ending at the very last move
        if in_path:
            path_id += 1
            paths.append(ExtrusionPath(
                id=path_id,
                start_index=start_idx,
                end_index=len(moves) - 1,
                move_count=move_count,
                total_length=total_length,
                total_extrusion=total_extrusion,
                layer=current_layer,
                path_type=current_type
            ))
            
        return paths
