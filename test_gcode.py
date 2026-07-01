import numpy as np
from src.slicer.engine import SlicerEngine
from src.slicer.gcode_generator import GCodeGenerator
import stl
from PyQt6.QtGui import QMatrix4x4

mesh = stl.mesh.Mesh.from_file('test_cube.stl')
# scale the cube up
mesh.vectors *= 10.0 # 10x10x10 cube, 50 layers

engine = SlicerEngine(layer_height=0.2, initial_layer_height=0.2, extrusion_width=0.4, wall_count=2, infill_density=0.15, infill_pattern='grid')
result = engine.slice_model(mesh.vectors, np.array([0,0,0]), QMatrix4x4(), [1,1,1])

generator = GCodeGenerator(layer_height=0.2, extrusion_width=0.4)
generator.begin(bed_temp=110, nozzle_temp=235)
generator.add_result(result, island_idx=0, model_idx=0)
gcode = generator.end()

print(gcode[:1000])
