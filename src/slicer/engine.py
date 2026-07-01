import numpy as np
from typing import List
import time

from .types import SliceLayer, SliceResult
from .mesh_prep import prepare_mesh_for_slicing, get_mesh_z_bounds
from .intersection import slice_mesh_at_z
from .stitcher import stitch_segments_to_polygons
from .perimeter import generate_perimeters
from .infill import generate_infill
from .optimize import optimize_travel

class SlicerEngine:
    def __init__(self, layer_height: float = 0.2, initial_layer_height: float = 0.2, extrusion_width: float = 0.6, wall_count: int = 2, infill_density: float = 0.15, infill_pattern: str = 'grid'):
        self.layer_height = layer_height
        self.initial_layer_height = initial_layer_height
        self.extrusion_width = extrusion_width
        self.wall_count = wall_count
        self.infill_density = infill_density
        self.infill_pattern = infill_pattern
        
    def slice_model(self, raw_vertices: np.ndarray, pos: np.ndarray, rot_matrix, scale: list) -> SliceResult:
        t0 = time.time()
        
        vertices = prepare_mesh_for_slicing(raw_vertices, pos, rot_matrix, scale)
        z_min, z_max = get_mesh_z_bounds(vertices)
        current_z = max(0.0, z_min) + self.initial_layer_height
        
        result = SliceResult()
        layer_count = 0
        current_nozzle_pos = np.array([0.0, 0.0])
        
        while current_z <= z_max:
            segments = slice_mesh_at_z(vertices, current_z)
            polygons = stitch_segments_to_polygons(segments)
            perimeters, infill_boundaries = generate_perimeters(polygons, self.extrusion_width, self.wall_count)
            infill_lines = generate_infill(infill_boundaries, self.infill_density, self.infill_pattern, self.extrusion_width)
            
            opt_perims, opt_infill, current_nozzle_pos = optimize_travel(perimeters, infill_lines, current_nozzle_pos)
            
            result.layers.append(SliceLayer(z_height=current_z, polygons=polygons, perimeters=opt_perims, infill_lines=opt_infill))
            
            current_z += self.layer_height
            layer_count += 1
            
        t1 = time.time()
        print(f"SlicerEngine: Sliced {layer_count} layers in {t1 - t0:.3f} seconds.")
        
        return result
