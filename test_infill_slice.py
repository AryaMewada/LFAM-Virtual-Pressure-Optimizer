import numpy as np
from src.slicer.engine import SlicerEngine
import stl
from PyQt6.QtGui import QMatrix4x4

mesh = stl.mesh.Mesh.from_file('test_cube.stl')
# scale the cube up
mesh.vectors *= 100.0

engine = SlicerEngine(layer_height=0.2, initial_layer_height=0.2, extrusion_width=0.4, wall_count=2, infill_density=0.15, infill_pattern='grid')
result = engine.slice_model(mesh.vectors, np.array([0,0,0]), QMatrix4x4(), [1,1,1])

print(f"Sliced {len(result.layers)} layers.")
for i, layer in enumerate(result.layers[:3]):
    print(f"Layer {i}: {len([p for p in layer.perimeters if p is not None])} perimeters, {len([p for p in getattr(layer, 'infill_lines', []) if p is not None])} infill lines")
