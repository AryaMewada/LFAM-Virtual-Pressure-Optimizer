import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from PyQt6.QtGui import QMatrix4x4

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.slicer.engine import SlicerEngine

def create_cube_mesh(size=100.0):
    """Creates a raw vertices array (N, 3, 3) for a simple cube."""
    s = size / 2.0
    # 8 vertices
    v = np.array([
        [-s, -s, 0], [s, -s, 0], [s, s, 0], [-s, s, 0],
        [-s, -s, size], [s, -s, size], [s, s, size], [-s, s, size]
    ])
    
    # 12 triangles (2 per face)
    faces = [
        [0, 1, 2], [0, 2, 3], # Bottom (Z=0)
        [4, 5, 6], [4, 6, 7], # Top (Z=size)
        [0, 1, 5], [0, 5, 4], # Front
        [1, 2, 6], [1, 6, 5], # Right
        [2, 3, 7], [2, 7, 6], # Back
        [3, 0, 4], [3, 4, 7]  # Left
    ]
    
    vertices = np.zeros((12, 3, 3))
    for i, face in enumerate(faces):
        for j in range(3):
            vertices[i, j] = v[face[j]]
            
    return vertices

def main():
    print("Generating test mesh (100x100x100 cube)...")
    raw_verts = create_cube_mesh(100.0)
    
    # Fake UI parameters
    pos = np.array([50.0, 50.0, 0.0])
    rot = QMatrix4x4()
    # Let's rotate it 45 degrees around Z and 45 around Y to get some interesting cross sections!
    rot.rotate(45, 0, 0, 1)
    rot.rotate(45, 0, 1, 0)
    scale = [1.0, 1.0, 1.0]
    
    print("Initializing SlicerEngine...")
    engine = SlicerEngine(layer_height=2.0, initial_layer_height=1.0)
    
    print("Slicing...")
    result = engine.slice_model(raw_verts, pos, rot, scale)
    
    # Pick a few layers to plot
    layers_to_plot = [
        result.layers[len(result.layers)//4],
        result.layers[len(result.layers)//2],
        result.layers[3*len(result.layers)//4]
    ]
    
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    for ax, layer in zip(axes, layers_to_plot):
        ax.set_title(f"Z = {layer.z_height:.2f}")
        ax.set_xlim(0, 200)
        ax.set_ylim(-50, 150)
        ax.set_aspect('equal')
        
        for poly in layer.polygons:
            # Extract x and y
            x = poly.points[:, 0]
            y = poly.points[:, 1]
            
            # Close the loop for plotting
            x = np.append(x, x[0])
            y = np.append(y, y[0])
            
            ax.plot(x, y, 'b-', linewidth=2)
            
    plt.tight_layout()
    plt.savefig('slicer_test_output.png')
    print("Saved output to slicer_test_output.png")

if __name__ == '__main__':
    main()
