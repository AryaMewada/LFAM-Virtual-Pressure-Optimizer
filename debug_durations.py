import sys
from src.engine.parser.parser import GCodeParser

test_gcode = """
G28
G92 E0
G1 F1500 X10 Y10 Z0.2 E1.0
G1 X20 Y20 E2.0
G1 X10 Y20 E3.0
G1 X10 Y10 E4.0
M82
"""

parser = GCodeParser()
moves = parser.parse(test_gcode)

layer_t = 0.0
for m in moves:
    dur = m.duration * 60.0
    layer_t += dur
    print(f"Move {m.id}: length={m.length:.2f}, feedrate={m.feedrate}, duration(sec)={dur:.4f}, cum_time={layer_t:.4f}")
