import pyclipper
import numpy as np
from typing import List
from .types import Polygon

CLIPPER_SCALE = 100000.0  # Scale factor to convert floats to integers for clipper

def generate_perimeters(raw_polygons: List[Polygon], extrusion_width: float, wall_count: int) -> List[Polygon]:
    """
    Takes raw mathematical slice polygons and generates printable perimeters (walls)
    using Clipper offsetting.
    
    Args:
        raw_polygons: The raw un-offset polygons from the Z-intersection.
        extrusion_width: The physical width of the extruded bead.
        wall_count: How many concentric walls to generate.
        
    Returns:
        A flat list of generated perimeter polygons.
    """
    if not raw_polygons or wall_count < 1:
        return []

    scaled_paths = []
    for poly in raw_polygons:
        scaled_paths.append(tuple((int(x * CLIPPER_SCALE), int(y * CLIPPER_SCALE)) for x, y in poly.points))
        
    # SimplifyPolygons with EVENODD fill type correctly orients outer boundaries 
    # (counter-clockwise) and inner holes (clockwise), and merges any overlapping segments.
    # This ensures that a negative offset shrinks the solid volume correctly.
    oriented_paths = pyclipper.SimplifyPolygons(scaled_paths, pyclipper.PFT_EVENODD)

    pco = pyclipper.PyclipperOffset()
    for path in oriented_paths:
        # Add the path as a closed polygon. 
        # JT_SQUARE prevents sharp inward spikes caused by floating point wobble in the STL.
        pco.AddPath(path, pyclipper.JT_SQUARE, pyclipper.ET_CLOSEDPOLYGON)

    perimeters = []
    
    # Generate concentric walls
    for i in range(wall_count):
        # The first wall is inset by half the extrusion width so the bead edge aligns with the model surface.
        # Subsequent walls are inset by the full extrusion width.
        delta = -(extrusion_width / 2.0) - (i * extrusion_width)
        
        # Execute the offset
        solution = pco.Execute(delta * CLIPPER_SCALE)
        
        # Convert back to numpy arrays and Polygon objects
        for path in solution:
            # Scale down
            pts = np.array(path, dtype=np.float64) / CLIPPER_SCALE
            perimeters.append(Polygon(points=pts))
            
    return perimeters
