import numpy as np
from typing import List, Tuple
from .types import Polygon

def optimize_travel(perimeters: List[Polygon], infill_lines: List[np.ndarray], start_pos: np.ndarray) -> Tuple[List[Polygon], List[np.ndarray], np.ndarray]:
    """
    Optimizes travel moves by greedily picking the nearest perimeter or infill line.
    Rolls perimeters to start at the nearest vertex.
    Draws infill lines from the nearest end to the farthest end.
    
    Returns:
        (optimized_perimeters, optimized_infill_lines, end_pos)
    """
    unvisited_perimeters = list(perimeters)
    unvisited_infill = list(infill_lines)
    
    optimized_perimeters = []
    optimized_infill = []
    
    current_pos = start_pos.copy()
    
    while unvisited_perimeters or unvisited_infill:
        best_dist = float('inf')
        best_p_idx = -1
        best_p_roll = 0
        best_p_end = None
        
        best_i_idx = -1
        best_i_reverse = False
        best_i_end = None
        
        # Check perimeters
        for i, p in enumerate(unvisited_perimeters):
            pts = p.points
            dists = np.sum((pts - current_pos)**2, axis=1)
            min_idx = np.argmin(dists)
            min_d = dists[min_idx]
            
            if min_d < best_dist:
                best_dist = min_d
                best_p_idx = i
                best_p_roll = min_idx
                best_p_end = pts[min_idx] # Closed loop ends where it starts
                best_i_idx = -1
                
        # Check infill lines
        for i, line in enumerate(unvisited_infill):
            d1 = np.sum((line[0] - current_pos)**2)
            d2 = np.sum((line[-1] - current_pos)**2)
            
            if d1 < best_dist:
                best_dist = d1
                best_p_idx = -1
                best_i_idx = i
                best_i_reverse = False
                best_i_end = line[-1]
            if d2 < best_dist:
                best_dist = d2
                best_p_idx = -1
                best_i_idx = i
                best_i_reverse = True
                best_i_end = line[0]
                
        if best_p_idx != -1:
            # Picked a perimeter
            p = unvisited_perimeters.pop(best_p_idx)
            rolled_pts = np.roll(p.points, -best_p_roll, axis=0)
            optimized_perimeters.append(Polygon(points=rolled_pts, is_hole=p.is_hole))
            current_pos = best_p_end
            # Pad with None for infill ordering interleaving
            optimized_infill.append(None)
        else:
            # Picked an infill line
            line = unvisited_infill.pop(best_i_idx)
            if best_i_reverse:
                line = line[::-1]
            optimized_infill.append(line)
            current_pos = best_i_end
            # Pad with None for perimeter ordering interleaving
            optimized_perimeters.append(None)
            
    return optimized_perimeters, optimized_infill, current_pos
