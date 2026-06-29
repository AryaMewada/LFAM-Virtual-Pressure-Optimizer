from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any
import copy

from src.engine.parser.move import Move
from src.engine.analysis.geometry_analyzer import AnalyzedMove
from src.engine.pressure.virtual_pressure_engine import PressureResult
from src.engine.optimizer.ramp_generator import RampGenerator

@dataclass
class OptimizationSettings:
    """Settings for the optimization engine."""
    corner_slowdown: int = 0  # 0-100
    curve_adaptation: int = 0 # 0-100
    start_ramp: int = 0       # 0-100
    end_taper: int = 0        # 0-100
    flow_smoothing: int = 0   # 0-100
    speed_smoothing: int = 0  # 0-100

class Modification:
    """Records a modification made to a move."""
    __slots__ = ['move_id', 'type', 'original_value', 'new_value', 'reason']
    def __init__(self, move_id: int, type: str, original_value: float, new_value: float, reason: str):
        self.move_id = move_id
        self.type = type
        self.original_value = original_value
        self.new_value = new_value
        self.reason = reason

@dataclass
class OptimizationResult:
    """Results of the optimization process."""
    optimized_moves: List[Move]
    modifications: List[Modification] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)

class PressureOptimizer:
    """Applies optimizations to G-code based on pressure analysis."""
    
    def __init__(self, material_profile: Dict[str, Any], machine_profile: Dict[str, Any], settings: OptimizationSettings):
        self.material_profile = material_profile
        self.machine_profile = machine_profile
        self.settings = settings

    def optimize(self, moves: List[Move], analyzed_moves: List[AnalyzedMove], pressure_results: List[PressureResult]) -> OptimizationResult:
        """Applies optimization strategies sequentially."""
        optimized = copy.deepcopy(moves)
        modifications = []
        
        # We index by move ID for quick lookups
        move_map = {m.id: i for i, m in enumerate(optimized)}
        analyzed_map = {m.id: m for m in analyzed_moves}
        pressure_map = {p.move_id: p for p in pressure_results}
        
        # 1. Corner Slowdown
        if self.settings.corner_slowdown > 0:
            intensity = self.settings.corner_slowdown / 100.0
            for am in analyzed_moves:
                if am.corner_angle > 30.0 and am.is_print:
                    idx = move_map.get(am.id)
                    if idx is not None:
                        target_m = optimized[idx]
                        orig_f = target_m.feedrate
                        # Reduce feedrate proportional to angle severity and intensity
                        reduction = intensity * (am.corner_angle / 180.0) * orig_f
                        new_f = max(orig_f * 0.1, orig_f - reduction)
                        target_m.feedrate = new_f
                        modifications.append(Modification(am.id, 'corner_slowdown', orig_f, new_f, f"Corner angle {am.corner_angle:.1f}°"))
                        
                        # Apply smoothing ramp before/after
                        ramp_len = 3
                        for j in range(max(0, idx - ramp_len), idx):
                            if optimized[j].is_print:
                                smoothed_f = optimized[j].feedrate - (optimized[j].feedrate - new_f) * (0.5 * intensity)
                                optimized[j].feedrate = smoothed_f
                                modifications.append(Modification(optimized[j].id, 'corner_slowdown', optimized[j].feedrate, smoothed_f, "Pre-corner ramp"))
                                
        # 2. Curve Adaptation
        if self.settings.curve_adaptation > 0:
            intensity = self.settings.curve_adaptation / 100.0
            threshold = self.machine_profile.get('min_radius', 10.0)
            for am in analyzed_moves:
                if am.curve_radius < threshold and am.is_print:
                    idx = move_map.get(am.id)
                    if idx is not None:
                        target_m = optimized[idx]
                        orig_f = target_m.feedrate
                        # Reduce proportional to 1/radius
                        reduction = intensity * (1.0 - (am.curve_radius / threshold)) * orig_f
                        new_f = max(orig_f * 0.1, orig_f - reduction)
                        target_m.feedrate = new_f
                        modifications.append(Modification(am.id, 'curve_adaptation', orig_f, new_f, f"Curve radius {am.curve_radius:.1f}mm"))
                        
        # Find paths for start/end ramps
        paths = []
        curr_path = []
        for i, am in enumerate(analyzed_moves):
            if am.is_print:
                curr_path.append(i)
            elif curr_path:
                paths.append(curr_path)
                curr_path = []
        if curr_path:
            paths.append(curr_path)
            
        # 3. Start Ramp (Pressure Priming)
        if self.settings.start_ramp > 0:
            intensity = self.settings.start_ramp / 100.0
            # Instead of starving the start, we OVER-extrude slightly to build pressure instantly.
            # Starts at 100% to 150% depending on intensity, and ramps DOWN to 100%.
            start_percent = 1.0 + (0.5 * intensity) 
            n_moves = min(5, int(10 * intensity) + 1)
            
            for path_indices in paths:
                ramp_len = min(n_moves, len(path_indices))
                if ramp_len > 1:
                    ramp = RampGenerator.generate_scurve_ramp(start_percent, 1.0, ramp_len)
                    for k, idx in enumerate(path_indices[:ramp_len]):
                        target_m = optimized[idx]
                        orig_e = target_m.extrusion
                        orig_f = target_m.feedrate
                        target_m.extrusion = orig_e * ramp[k]
                        target_m.feedrate = orig_f * max(0.2, ramp[k]) # Don't drop speed below 20%
                        modifications.append(Modification(target_m.id, 'start_ramp', orig_e, target_m.extrusion, "Start path ramp (E & F)"))
                        
        # 4. End Taper
        if self.settings.end_taper > 0:
            intensity = self.settings.end_taper / 100.0
            end_percent = 1.0 - (0.8 * intensity) # Ends at 20% to 100% depending on intensity
            n_moves = min(5, int(10 * intensity) + 1)
            
            for path_indices in paths:
                ramp_len = min(n_moves, len(path_indices))
                if ramp_len > 1:
                    ramp = RampGenerator.generate_scurve_ramp(1.0, end_percent, ramp_len)
                    for k, idx in enumerate(path_indices[-ramp_len:]):
                        target_m = optimized[idx]
                        orig_e = target_m.extrusion
                        orig_f = target_m.feedrate
                        target_m.extrusion = orig_e * ramp[k]
                        target_m.feedrate = orig_f * max(0.2, ramp[k]) # Don't drop speed below 20%
                        modifications.append(Modification(target_m.id, 'end_taper', orig_e, target_m.extrusion, "End path taper (E & F)"))
                        
        # 5. Flow Smoothing
        if self.settings.flow_smoothing > 0:
            intensity = self.settings.flow_smoothing / 100.0
            window = max(2, int(5 * intensity))
            for path_indices in paths:
                if len(path_indices) > window:
                    original_extrusions = [optimized[i].extrusion for i in path_indices]
                    for i in range(len(path_indices)):
                        start_w = max(0, i - window)
                        end_w = min(len(path_indices), i + window + 1)
                        window_vals = original_extrusions[start_w:end_w]
                        avg_e = sum(window_vals) / len(window_vals)
                        
                        target_m = optimized[path_indices[i]]
                        orig_e = target_m.extrusion
                        # Blend based on intensity
                        new_e = orig_e * (1.0 - intensity) + avg_e * intensity
                        target_m.extrusion = new_e
                        modifications.append(Modification(target_m.id, 'flow_smoothing', orig_e, new_e, "Flow smoothing"))
                        
        # 6. Speed Smoothing
        if self.settings.speed_smoothing > 0:
            intensity = self.settings.speed_smoothing / 100.0
            window = max(2, int(5 * intensity))
            for path_indices in paths:
                if len(path_indices) > window:
                    original_speeds = [optimized[i].feedrate for i in path_indices]
                    for i in range(len(path_indices)):
                        start_w = max(0, i - window)
                        end_w = min(len(path_indices), i + window + 1)
                        window_vals = original_speeds[start_w:end_w]
                        avg_f = sum(window_vals) / len(window_vals)
                        
                        target_m = optimized[path_indices[i]]
                        orig_f = target_m.feedrate
                        # Blend
                        new_f = orig_f * (1.0 - intensity) + avg_f * intensity
                        target_m.feedrate = new_f
                        modifications.append(Modification(target_m.id, 'speed_smoothing', orig_f, new_f, "Speed smoothing"))
                        
        summary = {
            'total_modifications': len(modifications),
            'types': {}
        }
        for mod in modifications:
            summary['types'][mod.type] = summary['types'].get(mod.type, 0) + 1
            
        return OptimizationResult(optimized_moves=optimized, modifications=modifications, summary=summary)
