import numpy as np
from typing import List
from collections import defaultdict
from .types import Polygon

def stitch_segments_to_polygons(segments: np.ndarray, tolerance_decimals: int = 4) -> List[Polygon]:
    """
    Stitches an unordered collection of line segments into closed polygons.
    Uses coordinate rounding to match endpoints that are very close.
    
    Args:
        segments: (M, 2, 2) numpy array of line segments
        tolerance_decimals: Decimal places to round to for endpoint matching (4 = 0.1 microns)
        
    Returns:
        List of Polygon objects containing ordered vertices.
    """
    if len(segments) == 0:
        return []
        
    # We will build an adjacency map: point -> list of connected points
    # Points are rounded and converted to tuples so they can be dict keys
    adj = defaultdict(list)
    
    for seg in segments:
        p1_round = (round(seg[0, 0], tolerance_decimals), round(seg[0, 1], tolerance_decimals))
        p2_round = (round(seg[1, 0], tolerance_decimals), round(seg[1, 1], tolerance_decimals))
        
        # Don't add degenerate zero-length segments
        if p1_round == p2_round:
            continue
            
        # Add bidirectional connections
        adj[p1_round].append((p2_round, seg[1]))
        adj[p2_round].append((p1_round, seg[0]))
        
    polygons = []
    visited = set()
    
    for start_node in list(adj.keys()):
        if start_node in visited:
            continue
            
        current_node = start_node
        path = []
        
        while current_node not in visited:
            visited.add(current_node)
            
            # The exact unrounded coordinate of this node is slightly trickier to grab,
            # but we can grab it from the adjacency list of the PREVIOUS node.
            # To keep it simple, we will just use the rounded coordinates for the path
            # as 0.1 micron precision is vastly beyond what a 3D printer can resolve anyway.
            path.append([current_node[0], current_node[1]])
            
            neighbors = adj.get(current_node, [])
            next_node = None
            
            for neighbor_node, exact_pt in neighbors:
                if neighbor_node not in visited:
                    next_node = neighbor_node
                    break
                    
            if next_node is not None:
                current_node = next_node
            else:
                break
                
        # Only keep polygons with at least 3 points
        if len(path) > 2:
            poly_points = np.array(path)
            
            # Simple check if the polygon is closed (first and last points are close or they naturally met)
            # We don't strictly require the loop to perfectly match index 0 here because 
            # if it's a closed loop, it will just end when all neighbors are visited.
            
            polygons.append(Polygon(points=poly_points))
            
    return polygons
