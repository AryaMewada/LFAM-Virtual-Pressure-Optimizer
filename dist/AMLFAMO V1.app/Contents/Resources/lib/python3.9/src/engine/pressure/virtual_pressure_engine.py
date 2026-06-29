from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any
from src.engine.analysis.geometry_analyzer import AnalyzedMove
from src.engine.pressure.pressure_model import (
    flow_factor, speed_factor, corner_factor, curve_factor,
    history_factor, acceleration_factor, start_stop_factor, segment_density_factor
)

@dataclass
class PressureResult:
    """Results of virtual pressure calculation for a single move."""
    move_id: int
    vpi: float
    factors: Dict[str, float]
    is_hotspot: bool = False

class VirtualPressureEngine:
    """Computes the Virtual Pressure Index (VPI) for each move."""
    
    def __init__(self, material_profile: Dict[str, Any], machine_profile: Dict[str, Any]):
        self.material_profile = material_profile
        self.machine_profile = machine_profile
        
        # Default weights
        self.weights = {
            'flow': 0.20,
            'speed': 0.15,
            'corner': 0.20,
            'curve': 0.10,
            'history': 0.10,
            'acceleration': 0.10,
            'start_stop': 0.10,
            'density': 0.05
        }
        
        # Override with material profile if provided
        if 'weights' in material_profile:
            self.weights.update(material_profile['weights'])

    def compute_pressure(self, analyzed_moves: List[AnalyzedMove]) -> List[PressureResult]:
        """Computes VPI for all moves based on 8 factors."""
        results = []
        
        max_flow_rate = self.machine_profile.get('max_flow_rate', 50.0)
        optimal_feedrate = self.material_profile.get('optimal_feedrate', 1500.0)
        max_feedrate = self.machine_profile.get('max_feedrate', 3000.0)
        corner_sensitivity = self.material_profile.get('corner_sensitivity', 1.0)
        curve_sensitivity = self.material_profile.get('curve_sensitivity', 1.0)
        min_radius = self.machine_profile.get('min_radius', 2.0)
        history_decay = self.material_profile.get('history_decay', 0.2)
        ramp_length = self.machine_profile.get('ramp_length', 10.0)
        min_segment_length = self.machine_profile.get('min_segment_length', 1.0)
        density_sensitivity = self.material_profile.get('density_sensitivity', 1.0)
        
        history_window = []
        
        # Pre-compute distances from start/end for paths
        distances_from_start = [0.0] * len(analyzed_moves)
        distances_from_end = [0.0] * len(analyzed_moves)
        
        current_dist_start = 0.0
        for i, move in enumerate(analyzed_moves):
            if move.is_path_start:
                current_dist_start = 0.0
            distances_from_start[i] = current_dist_start
            current_dist_start += move.length
            
        current_dist_end = 0.0
        for i in range(len(analyzed_moves) - 1, -1, -1):
            move = analyzed_moves[i]
            if move.is_path_end:
                current_dist_end = 0.0
            distances_from_end[i] = current_dist_end
            current_dist_end += move.length

        for i, move in enumerate(analyzed_moves):
            if not move.is_print:
                results.append(PressureResult(move.id, 0.0, {}, False))
                history_window.append(0.0)
                if len(history_window) > 10:
                    history_window.pop(0)
                continue
                
            f_flow = flow_factor(move.flow_rate, max_flow_rate)
            f_speed = speed_factor(move.feedrate, optimal_feedrate, max_feedrate)
            f_corner = corner_factor(move.corner_angle, corner_sensitivity)
            f_curve = curve_factor(move.curve_radius, min_radius, curve_sensitivity)
            f_history = history_factor(history_window, history_decay)
            f_accel = acceleration_factor(move.flow_rate_change, max_flow_rate)
            f_ss = start_stop_factor(move.is_path_start, move.is_path_end, distances_from_start[i], distances_from_end[i], ramp_length)
            f_density = segment_density_factor(move.length, min_segment_length, density_sensitivity)
            
            factors = {
                'flow': f_flow,
                'speed': f_speed,
                'corner': f_corner,
                'curve': f_curve,
                'history': f_history,
                'acceleration': f_accel,
                'start_stop': f_ss,
                'density': f_density
            }
            
            vpi = 0.0
            weight_sum = 0.0
            for key, val in factors.items():
                w = self.weights.get(key, 0.0)
                vpi += val * w
                weight_sum += w
                
            if weight_sum > 0:
                vpi /= weight_sum
                
            vpi = max(0.0, min(1.0, vpi))
            
            history_window.append(vpi)
            if len(history_window) > 10:
                history_window.pop(0)
                
            results.append(PressureResult(
                move_id=move.id,
                vpi=vpi,
                factors=factors,
                is_hotspot=(vpi > 0.7)
            ))
            
        return results
