import pyclipper
import numpy as np

pc = pyclipper.Pyclipper()

# Add a box boundary
box = [(0, 0), (100, 0), (100, 100), (0, 100)]
pc.AddPath(box, pyclipper.PT_CLIP, True)

# Add a long line across it
line = [(-50, 50), (150, 50)]
pc.AddPath(line, pyclipper.PT_SUBJECT, False)

tree = pc.Execute2(pyclipper.CT_INTERSECTION, pyclipper.PFT_EVENODD, pyclipper.PFT_EVENODD)

def extract_lines(node):
    lines = []
    print(f"Node Contour: {node.Contour}, IsHole: {node.IsHole}, IsOpen: {getattr(node, 'IsOpen', 'No IsOpen prop')}")
    if len(node.Contour) >= 2:
        lines.append(node.Contour)
    for child in node.Childs:
        lines.extend(extract_lines(child))
    return lines

print(extract_lines(tree))
