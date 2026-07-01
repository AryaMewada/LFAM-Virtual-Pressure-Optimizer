import numpy as np
from typing import List, Tuple
from .types import Polygon

def optimize_travel(polygons: List[Polygon], start_pos: np.ndarray) -> Tuple[List[Polygon], np.ndarray]:
    """
    Greedy shortest path optimization:
    1. Finds the nearest polygon to start_pos.
    2. Rolls its vertices so it starts at the point closest to start_pos.
    3. Updates start_pos to the end of that polygon.
    4. Repeats for all polygons.
    
    Returns the optimized list of polygons and the final position.
    """
    if not polygons:
        return [], start_pos
        
    unvisited = list(polygons)
    optimized = []
    current_pos = start_pos
    
    while unvisited:
        best_poly_idx = -1
        best_shift = 0
        min_dist = float('inf')
        
        for i, poly in enumerate(unvisited):
            pts = poly.points
            if len(pts) == 0:
                continue
            # Calculate distance from current_pos to all points in this polygon
            dists = np.linalg.norm(pts - current_pos[:2], axis=1)
            min_pt_idx = np.argmin(dists)
            
            if dists[min_pt_idx] < min_dist:
                min_dist = dists[min_pt_idx]
                best_poly_idx = i
                best_shift = min_pt_idx
                
        if best_poly_idx == -1:
            break
            
        best_poly = unvisited.pop(best_poly_idx)
        pts = best_poly.points
        
        # Roll the array so the closest point is first
        if best_shift != 0:
            pts = np.roll(pts, -best_shift, axis=0)
            
        optimized.append(Polygon(points=pts))
        # The end position is the last point in the polygon
        current_pos = np.array([pts[-1][0], pts[-1][1]])
        
    return optimized, current_pos
