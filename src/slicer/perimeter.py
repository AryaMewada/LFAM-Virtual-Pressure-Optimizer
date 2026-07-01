import pyclipper
import numpy as np
from typing import List, Tuple
from .types import Polygon

CLIPPER_SCALE = 100000.0  # Scale factor to convert floats to integers for clipper

def generate_perimeters(raw_polygons: List[Polygon], extrusion_width: float, wall_count: int) -> Tuple[List[Polygon], List[Polygon]]:
    """
    Takes raw mathematical slice polygons and generates printable perimeters (walls)
    using Clipper offsetting. Also returns the infill boundary.
    
    Args:
        raw_polygons: The raw un-offset polygons from the Z-intersection.
        extrusion_width: The physical width of the extruded bead.
        wall_count: How many concentric walls to generate.
        
    Returns:
        (perimeters, infill_boundaries)
    """
    if not raw_polygons:
        return [], []

    scaled_paths = []
    for poly in raw_polygons:
        scaled_paths.append(tuple((int(x * CLIPPER_SCALE), int(y * CLIPPER_SCALE)) for x, y in poly.points))
        
    oriented_paths = pyclipper.SimplifyPolygons(scaled_paths, pyclipper.PFT_EVENODD)

    pco = pyclipper.PyclipperOffset()
    for path in oriented_paths:
        pco.AddPath(path, pyclipper.JT_SQUARE, pyclipper.ET_CLOSEDPOLYGON)

    perimeters = []
    
    # Generate concentric walls (Inside-Out order)
    if wall_count > 0:
        for i in reversed(range(wall_count)):
            delta = -(extrusion_width / 2.0) - (i * extrusion_width)
            solution = pco.Execute(delta * CLIPPER_SCALE)
            
            for path in solution:
                pts = np.array(path, dtype=np.float64) / CLIPPER_SCALE
                perimeters.append(Polygon(points=pts))
                
    # Generate infill boundary
    infill_boundaries = []
    infill_delta = -(extrusion_width / 2.0) - (wall_count * extrusion_width)
    # actually, overlap between wall and infill is good for adhesion.
    # usually infill overlaps inner wall by 15-20%.
    # So instead of full extrusion width, let's offset by 0.8 * extrusion_width
    overlap = 0.2 * extrusion_width
    infill_delta = -(extrusion_width / 2.0) - max(0, (wall_count - 1)) * extrusion_width - (extrusion_width - overlap)
    
    if wall_count == 0:
        infill_delta = -(extrusion_width / 2.0)
        
    infill_solution = pco.Execute(infill_delta * CLIPPER_SCALE)
    for path in infill_solution:
        pts = np.array(path, dtype=np.float64) / CLIPPER_SCALE
        infill_boundaries.append(Polygon(points=pts))
        
    return perimeters, infill_boundaries
