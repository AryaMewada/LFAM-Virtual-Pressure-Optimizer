import numpy as np

def prepare_mesh_for_slicing(vertices: np.ndarray, pos: np.ndarray, rot_matrix, scale: list) -> np.ndarray:
    """
    Applies the UI layout transformations (scale, rotate, translate) to the raw mesh vertices
    so they reflect their exact position and scale in the build volume.
    
    Args:
        vertices: (N, 3, 3) array of triangle vertices
        pos: (3,) array of world position (X, Y, Z)
        rot_matrix: PyQt6 QMatrix4x4 representing rotation
        scale: list of 3 floats representing scaling
        
    Returns:
        (N, 3, 3) array of transformed triangle vertices
    """
    import PyQt6.QtGui as QtGui
    
    # 1. Scale
    scaled_verts = vertices * np.array(scale)
    
    # 2. Rotate & Translate
    # Since we need to apply rot_matrix to a large number of vertices, 
    # extracting the 4x4 data into numpy is much faster than looping QMatrix4x4.map()
    mat_data = rot_matrix.data()
    # QMatrix4x4.data() returns a list of 16 floats in column-major order
    # Let's reshape it to a 4x4 numpy matrix
    np_mat = np.array(mat_data, dtype=np.float32).reshape((4, 4)).T
    
    # Extract the 3x3 rotation/scale part
    rot_3x3 = np_mat[:3, :3]
    
    # Flatten the (N, 3, 3) to (N*3, 3) for matrix multiplication
    flat_verts = scaled_verts.reshape(-1, 3)
    
    # Apply rotation
    rotated_verts = np.dot(flat_verts, rot_3x3.T)
    
    # Add translation
    translated_verts = rotated_verts + pos
    
    # Reshape back to (N, 3, 3)
    final_verts = translated_verts.reshape(-1, 3, 3)
    
    return final_verts

def get_mesh_z_bounds(vertices: np.ndarray) -> tuple[float, float]:
    """
    Calculates the absolute min and max Z coordinates of a mesh.
    
    Args:
        vertices: (N, 3, 3) array of transformed vertices
        
    Returns:
        (z_min, z_max)
    """
    z_coords = vertices[:, :, 2]
    return float(np.min(z_coords)), float(np.max(z_coords))
