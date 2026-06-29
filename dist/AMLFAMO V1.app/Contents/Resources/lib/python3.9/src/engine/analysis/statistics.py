from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any
from src.engine.analysis.geometry_analyzer import AnalyzedMove
from src.engine.analysis.path_detector import ExtrusionPath

@dataclass
class AnalysisReport:
    """Comprehensive statistics about the analyzed G-code."""
    total_layers: int = 0
    total_moves: int = 0
    print_moves: int = 0
    travel_moves: int = 0
    sharp_corners: int = 0
    tight_curves: int = 0
    total_print_distance: float = 0.0
    total_travel_distance: float = 0.0
    estimated_print_time: float = 0.0
    pressure_hotspots: List[Dict[str, Any]] = field(default_factory=list)
    avg_flow_rate: float = 0.0
    max_flow_rate: float = 0.0
    min_segment_length: float = float('inf')
    avg_segment_length: float = 0.0
    
    @classmethod
    def generate_report(cls, analyzed_moves: List[AnalyzedMove], paths: List[ExtrusionPath]) -> AnalysisReport:
        """Generates a statistical report from analyzed moves and paths."""
        report = cls()
        
        report.total_moves = len(analyzed_moves)
        layers = set()
        
        total_flow = 0.0
        flow_samples = 0
        
        for move in analyzed_moves:
            layers.add(move.layer)
            report.estimated_print_time += move.duration
            
            if move.is_print:
                report.print_moves += 1
                report.total_print_distance += move.length
                
                if move.corner_angle > 45.0:
                    report.sharp_corners += 1
                if move.curve_radius < 5.0:
                    report.tight_curves += 1
                    
                flow = move.flow_rate
                if flow > 0:
                    total_flow += flow
                    flow_samples += 1
                    report.max_flow_rate = max(report.max_flow_rate, flow)
                    
                if move.length > 0:
                    report.min_segment_length = min(report.min_segment_length, move.length)
            
            elif move.is_travel:
                report.travel_moves += 1
                report.total_travel_distance += move.length
                
        report.total_layers = len(layers)
        
        if flow_samples > 0:
            report.avg_flow_rate = total_flow / flow_samples
            
        if report.print_moves > 0:
            report.avg_segment_length = report.total_print_distance / report.print_moves
            
        if report.min_segment_length == float('inf'):
            report.min_segment_length = 0.0
            
        return report
