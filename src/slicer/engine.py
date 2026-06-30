import numpy as np
from typing import List
import time

from .types import SliceLayer, SliceResult
from .mesh_prep import prepare_mesh_for_slicing, get_mesh_z_bounds
from .intersection import slice_mesh_at_z
from .stitcher import stitch_segments_to_polygons

class SlicerEngine:
    def __init__(self, layer_height: float = 0.2, initial_layer_height: float = 0.2):
        self.layer_height = layer_height
        self.initial_layer_height = initial_layer_height
        
    def slice_model(self, raw_vertices: np.ndarray, pos: np.ndarray, rot_matrix, scale: list) -> SliceResult:
        """
        Slices a single 3D model into a stack of 2D layers.
        
        Args:
            raw_vertices: (N, 3, 3) raw STL vertices
            pos: (3,) position from UI
            rot_matrix: QMatrix4x4 from UI
            scale: list of 3 scale factors from UI
            
        Returns:
            SliceResult containing all layers.
        """
        t0 = time.time()
        
        # 1. Prepare Mesh (Apply world transforms)
        vertices = prepare_mesh_for_slicing(raw_vertices, pos, rot_matrix, scale)
        
        # 2. Get bounds
        z_min, z_max = get_mesh_z_bounds(vertices)
        
        # If the object is floating or sunken, we usually slice from Z=0 upwards in the real world
        # For a robust slicer, we slice from max(0.0, z_min).
        # Let's start at Z = initial_layer_height
        current_z = max(0.0, z_min) + self.initial_layer_height
        
        result = SliceResult()
        
        layer_count = 0
        while current_z <= z_max:
            # 3. Intersect plane
            segments = slice_mesh_at_z(vertices, current_z)
            
            # 4. Stitch segments
            polygons = stitch_segments_to_polygons(segments)
            
            # Store layer (even if empty, maybe useful for debugging)
            result.layers.append(SliceLayer(z_height=current_z, polygons=polygons))
            
            current_z += self.layer_height
            layer_count += 1
            
        t1 = time.time()
        print(f"SlicerEngine: Sliced {layer_count} layers in {t1 - t0:.3f} seconds.")
        
        return result
