import numpy as np

def slice_mesh_at_z(vertices: np.ndarray, z: float) -> np.ndarray:
    """
    Slices a 3D mesh at a specific Z height using fully vectorized numpy operations.
    
    Args:
        vertices: (N, 3, 3) numpy array of transformed triangles
        z: Float Z-height to slice at
        
    Returns:
        (M, 2, 2) numpy array of line segments in the XY plane.
        Each segment is [[x0, y0], [x1, y1]].
    """
    # Perturb Z slightly to avoid exact vertex hits (which cause zero-division or 1/3/0 edge intersections)
    epsilon = 1e-7
    z += epsilon
    
    # 1. Fast bounding box filter for triangles
    Z = vertices[:, :, 2]
    min_z = np.min(Z, axis=1)
    max_z = np.max(Z, axis=1)
    
    mask = (min_z < z) & (max_z > z)
    active_tris = vertices[mask]
    
    if len(active_tris) == 0:
        return np.empty((0, 2, 2))
        
    # active_tris shape: (M, 3, 3)
    # Get Z shifted to origin for easy crossing detection
    Z_shift = active_tris[:, :, 2] - z
    
    # Define the 3 edges of every triangle
    e0 = active_tris[:, [0, 1], :] # shape (M, 2, 3)
    e1 = active_tris[:, [1, 2], :]
    e2 = active_tris[:, [2, 0], :]
    
    z0 = Z_shift[:, [0, 1]]
    z1 = Z_shift[:, [1, 2]]
    z2 = Z_shift[:, [2, 0]]
    
    # Check if edge endpoints straddle the plane (one positive, one negative)
    cross0 = (z0[:, 0] * z0[:, 1]) < 0
    cross1 = (z1[:, 0] * z1[:, 1]) < 0
    cross2 = (z2[:, 0] * z2[:, 1]) < 0
    
    # Helper function to compute precise intersection X,Y points
    def intersect(e, z_vals, cross_mask):
        valid_e = e[cross_mask]
        valid_z = z_vals[cross_mask]
        if len(valid_e) == 0:
            return np.empty((0, 2)), np.empty(0, dtype=int)
            
        za = valid_z[:, 0]
        zb = valid_z[:, 1]
        
        # Linear interpolation fraction: t = -z_a / (z_b - z_a)
        t = -za / (zb - za)
        
        # Point = A + t * (B - A) - We only care about X and Y coordinates now
        A = valid_e[:, 0, :2]
        B = valid_e[:, 1, :2]
        pts = A + t[:, np.newaxis] * (B - A)
        
        return pts, np.nonzero(cross_mask)[0]

    p0, idx0 = intersect(e0, z0, cross0)
    p1, idx1 = intersect(e1, z1, cross1)
    p2, idx2 = intersect(e2, z2, cross2)
    
    # Combine all intersected points and their parent triangle indices
    all_pts = np.vstack([p0, p1, p2]) if len(p0) or len(p1) or len(p2) else np.empty((0, 2))
    all_idx = np.concatenate([idx0, idx1, idx2]) if len(idx0) or len(idx1) or len(idx2) else np.empty(0, dtype=int)
    
    if len(all_pts) == 0:
        return np.empty((0, 2, 2))
    
    # Sort by triangle index. Since each intersecting triangle must have exactly 2 
    # edges that cross the plane, this will pair up the endpoints of each line segment.
    sort_order = np.argsort(all_idx)
    sorted_pts = all_pts[sort_order]
    sorted_idx = all_idx[sort_order]
    
    # Robustness check: Ensure we only keep triangles that produced exactly 2 points
    unique, counts = np.unique(sorted_idx, return_counts=True)
    valid_indices = unique[counts == 2]
    
    # Filter points belonging to valid triangles
    valid_mask = np.isin(sorted_idx, valid_indices)
    valid_pts = sorted_pts[valid_mask]
    
    # Reshape the flat list of points into paired line segments: (M, 2, 2)
    segments = valid_pts.reshape(-1, 2, 2)
    
    return segments
