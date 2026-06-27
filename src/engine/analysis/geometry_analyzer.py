from __future__ import annotations
from dataclasses import dataclass, field
import math
from typing import List, Dict, Any, Optional
from src.engine.parser.move import Move, MoveType, Point3D

class AnalyzedMove(Move):
    """Extended Move dataclass containing geometric analysis data."""
    __slots__ = ['corner_angle', 'curve_radius', 'is_path_start', 'is_path_end', 'continuous_region_id', 'segment_density', 'flow_rate_change', 'speed_change']
    
    def __init__(self, id: int, type: MoveType, start: Point3D, end: Point3D, feedrate: float, 
                 extrusion: float, extrusion_mode: str, layer: int, line_number: int,
                 arc_center=None, arc_radius=None, arc_direction=None, original_line="",
                 is_travel=False, is_print=False, is_arc=False, comment="", raw_params=None,
                 corner_angle=0.0, curve_radius=float('inf'), is_path_start=False, is_path_end=False,
                 continuous_region_id=-1, segment_density=0.0, flow_rate_change=0.0, speed_change=0.0):
        super().__init__(id, type, start, end, feedrate, extrusion, extrusion_mode, layer, line_number,
                         arc_center, arc_radius, arc_direction, original_line, is_travel, is_print, is_arc, comment, raw_params)
        self.corner_angle = corner_angle
        self.curve_radius = curve_radius
        self.is_path_start = is_path_start
        self.is_path_end = is_path_end
        self.continuous_region_id = continuous_region_id
        self.segment_density = segment_density
        self.flow_rate_change = flow_rate_change
        self.speed_change = speed_change

    @classmethod
    def from_move(cls, move: Move) -> AnalyzedMove:
        """Creates an AnalyzedMove from a base Move."""
        return cls(
            id=move.id, type=move.type, start=move.start, end=move.end, feedrate=move.feedrate,
            extrusion=move.extrusion, extrusion_mode=move.extrusion_mode, layer=move.layer, line_number=move.line_number,
            arc_center=move.arc_center, arc_radius=move.arc_radius, arc_direction=move.arc_direction, original_line=move.original_line,
            is_travel=move.is_travel, is_print=move.is_print, is_arc=move.is_arc, comment=move.comment, raw_params=move.raw_params
        )


class GeometryAnalyzer:
    """Analyzes a sequence of moves to extract geometric features like corner angles and curve radii."""
    
    def analyze(self, moves: List[Move], machine_profile: Dict[str, Any]) -> List[AnalyzedMove]:
        """Analyzes moves and returns a list of AnalyzedMove objects."""
        analyzed = [AnalyzedMove.from_move(m) for m in moves]
        
        region_id = 0
        in_region = False
        
        for i in range(len(analyzed)):
            curr = analyzed[i]
            
            if curr.is_print:
                if not in_region:
                    region_id += 1
                    in_region = True
                    curr.is_path_start = True
                curr.continuous_region_id = region_id
            else:
                if in_region:
                    # Previous was end of region
                    if i > 0 and analyzed[i-1].is_print:
                        analyzed[i-1].is_path_end = True
                in_region = False
                
            # Density
            if curr.length > 0:
                curr.segment_density = 1.0 / curr.length
                
            # Changes
            if i > 0:
                prev = analyzed[i-1]
                curr.flow_rate_change = curr.flow_rate - prev.flow_rate
                curr.speed_change = curr.feedrate - prev.feedrate
                
            # Geometry - Corner angle and Curve radius
            if 0 < i < len(analyzed) - 1:
                prev = analyzed[i-1]
                next_m = analyzed[i+1]
                
                if curr.is_print and prev.is_print and next_m.is_print:
                    # Corner angle using vector dot product
                    v1 = (curr.end.x - curr.start.x, curr.end.y - curr.start.y)
                    v2 = (next_m.end.x - next_m.start.x, next_m.end.y - next_m.start.y)
                    
                    len1 = math.hypot(v1[0], v1[1])
                    len2 = math.hypot(v2[0], v2[1])
                    
                    if len1 > 1e-5 and len2 > 1e-5:
                        dot = v1[0]*v2[0] + v1[1]*v2[1]
                        cos_theta = max(-1.0, min(1.0, dot / (len1 * len2)))
                        angle_rad = math.acos(cos_theta)
                        # angle in degrees (0 = straight, 180 = full reversal)
                        curr.corner_angle = math.degrees(angle_rad)
                        
                    # Curve radius using circumradius formula of 3 points
                    # P1 = prev.start, P2 = curr.start (or midpoint), P3 = next_m.start
                    # For better approximation, let's use prev.start, curr.start, next_m.start
                    p1 = prev.start
                    p2 = curr.start
                    p3 = next_m.start
                    
                    a = math.hypot(p2.x - p1.x, p2.y - p1.y)
                    b = math.hypot(p3.x - p2.x, p3.y - p2.y)
                    c = math.hypot(p3.x - p1.x, p3.y - p1.y)
                    
                    # Area using Heron's formula
                    s = (a + b + c) / 2
                    area_sq = s * (s - a) * (s - b) * (s - c)
                    
                    if area_sq > 1e-5 and a > 0 and b > 0 and c > 0:
                        area = math.sqrt(area_sq)
                        radius = (a * b * c) / (4 * area)
                        curr.curve_radius = radius
                        
        # Handle last move in a continuous region
        if in_region and len(analyzed) > 0 and analyzed[-1].is_print:
            analyzed[-1].is_path_end = True
            
        return analyzed
