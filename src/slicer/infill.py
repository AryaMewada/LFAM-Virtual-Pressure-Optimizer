import numpy as np
import pyclipper
from typing import List
from .types import Polygon

CLIPPER_SCALE = 100000.0

def generate_infill(boundaries: List[Polygon], density: float, pattern: str, extrusion_width: float) -> List[np.ndarray]:
    """
    Generates infill lines inside the given boundaries.
    
    Args:
        boundaries: The infill boundaries (inner wall - overlap).
        density: Infill density between 0.0 and 1.0 (e.g., 0.15 for 15%).
        pattern: 'grid' or 'lines'
        extrusion_width: The physical width of the extruded bead.
        
    Returns:
        A list of numpy arrays, each of shape (2, 2) representing a line segment.
    """
    if density <= 0.01 or not boundaries:
        return []
        
    # Minimum spacing to avoid infinite loops or solid blocks if density is tiny/huge
    density = min(max(density, 0.01), 0.99)
    spacing = extrusion_width / density
    
    # 1. Find the global bounding box of all boundaries
    min_x = float('inf')
    max_x = float('-inf')
    min_y = float('inf')
    max_y = float('-inf')
    
    clipper_bounds = []
    
    for poly in boundaries:
        pts = poly.points
        min_x = min(min_x, pts[:, 0].min())
        max_x = max(max_x, pts[:, 0].max())
        min_y = min(min_y, pts[:, 1].min())
        max_y = max(max_y, pts[:, 1].max())
        
        # Prepare for clipper
        clipper_path = tuple((int(x * CLIPPER_SCALE), int(y * CLIPPER_SCALE)) for x, y in pts)
        clipper_bounds.append(clipper_path)
        
    # We will generate lines that cover the bounding box
    # To handle 45 degree rotation easily, we generate lines over a larger bounding circle
    cx = (min_x + max_x) / 2.0
    cy = (min_y + max_y) / 2.0
    radius = np.hypot(max_x - min_x, max_y - min_y) / 2.0
    
    # Generate infinite lines
    angles = []
    if pattern == 'grid':
        angles = [45, 135]
    else: # 'lines'
        angles = [45]
        
    clipper_lines = []
    
    for angle in angles:
        theta = np.radians(angle)
        dx = np.cos(theta)
        dy = np.sin(theta)
        
        # Normal vector to the line
        nx = -dy
        ny = dx
        
        # We start from -radius to +radius along the normal
        d_start = -radius
        d_end = radius
        
        d = d_start
        while d <= d_end:
            # Line equation point
            px = cx + nx * d
            py = cy + ny * d
            
            # Extend along direction vector by radius
            p1x = px + dx * radius * 1.5
            p1y = py + dy * radius * 1.5
            p2x = px - dx * radius * 1.5
            p2y = py - dy * radius * 1.5
            
            p1 = (int(p1x * CLIPPER_SCALE), int(p1y * CLIPPER_SCALE))
            p2 = (int(p2x * CLIPPER_SCALE), int(p2y * CLIPPER_SCALE))
            
            clipper_lines.append([p1, p2])
            d += spacing
            
    # 2. Intersect lines with boundaries
    pc = pyclipper.Pyclipper()
    
    # Add boundaries as subject (clip area)
    for b in clipper_bounds:
        pc.AddPath(b, pyclipper.PT_CLIP, True)
        
    # Add lines as subject
    for line in clipper_lines:
        pc.AddPath(line, pyclipper.PT_SUBJECT, False) # False means Open path (line)
        
    # Execute intersection
    tree = pc.Execute2(pyclipper.CT_INTERSECTION, pyclipper.PFT_EVENODD, pyclipper.PFT_EVENODD)
    
    def extract_lines(node):
        lines = []
        if getattr(node, 'IsOpen', False) and len(node.Contour) >= 2:
            contour = node.Contour
            for i in range(len(contour) - 1):
                p1 = np.array(contour[i]) / CLIPPER_SCALE
                p2 = np.array(contour[i+1]) / CLIPPER_SCALE
                lines.append(np.array([p1, p2]))
        for child in node.Childs:
            lines.extend(extract_lines(child))
        return lines
        
    result_lines = extract_lines(tree)
    return result_lines
