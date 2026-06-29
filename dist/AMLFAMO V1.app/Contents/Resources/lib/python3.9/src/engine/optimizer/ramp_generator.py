from __future__ import annotations
import math
from typing import List
from src.engine.parser.move import Move
import copy

class RampGenerator:
    """Generates ramps for smoothly interpolating values like feedrate and extrusion."""
    
    @staticmethod
    def generate_linear_ramp(start_value: float, end_value: float, n_steps: int) -> List[float]:
        """Generates a linear ramp between two values."""
        if n_steps <= 0:
            return []
        if n_steps == 1:
            return [end_value]
            
        step_size = (end_value - start_value) / (n_steps - 1)
        return [start_value + i * step_size for i in range(n_steps)]

    @staticmethod
    def generate_scurve_ramp(start_value: float, end_value: float, n_steps: int) -> List[float]:
        """Generates an S-curve (sigmoid) ramp for smooth acceleration/deceleration."""
        if n_steps <= 0:
            return []
        if n_steps == 1:
            return [end_value]
            
        ramp = []
        for i in range(n_steps):
            # Map i from [0, n_steps-1] to [-6, 6] for sigmoid
            t = (i / (n_steps - 1)) * 12.0 - 6.0
            sigmoid = 1.0 / (1.0 + math.exp(-t))
            val = start_value + (end_value - start_value) * sigmoid
            ramp.append(val)
        return ramp

    @staticmethod
    def apply_feedrate_ramp(moves: List[Move], target_feedrates: List[float]) -> List[Move]:
        """Applies feedrate values to a list of moves."""
        if len(moves) != len(target_feedrates):
            raise ValueError("Length of moves and target_feedrates must match.")
            
        result = []
        for m, f in zip(moves, target_feedrates):
            new_m = copy.deepcopy(m)
            new_m.feedrate = f
            result.append(new_m)
        return result

    @staticmethod
    def apply_extrusion_ramp(moves: List[Move], scale_factors: List[float]) -> List[Move]:
        """Scales extrusion amounts in a list of moves."""
        if len(moves) != len(scale_factors):
            raise ValueError("Length of moves and scale_factors must match.")
            
        result = []
        for m, s in zip(moves, scale_factors):
            new_m = copy.deepcopy(m)
            new_m.extrusion *= s
            result.append(new_m)
        return result
