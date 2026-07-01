import numpy as np

def generate_volumetric_mesh(p0, p1, ew, eh, z_min, z_max):
    """
    p0: (N, 3) start points
    p1: (N, 3) end points
    ew: extrusion width
    eh: layer height
    
    Returns vertices, faces, face_colors
    """
    num_segments = len(p0)
    if num_segments == 0:
        return np.empty((0,3)), np.empty((0,3), dtype=np.uint32), np.empty((0,4))
        
    v = p1 - p0
    v[:, 2] = 0
    lengths = np.linalg.norm(v, axis=1, keepdims=True)
    lengths[lengths == 0] = 1.0
    v = v / lengths
    v_perp = np.column_stack([-v[:, 1], v[:, 0], np.zeros(num_segments)])
    
    hw = ew / 2.0
    hh = eh / 2.0
    
    # 8 vertices per segment
    # 0: p0_tl, 1: p0_tr, 2: p0_bl, 3: p0_br
    # 4: p1_tl, 5: p1_tr, 6: p1_bl, 7: p1_br
    
    z_offset = np.array([0, 0, hh])
    p0_tl = p0 - v_perp * hw + z_offset
    p0_tr = p0 + v_perp * hw + z_offset
    p0_bl = p0 - v_perp * hw - z_offset
    p0_br = p0 + v_perp * hw - z_offset
    
    p1_tl = p1 - v_perp * hw + z_offset
    p1_tr = p1 + v_perp * hw + z_offset
    p1_bl = p1 - v_perp * hw - z_offset
    p1_br = p1 + v_perp * hw - z_offset
    
    vertices = np.empty((num_segments * 8, 3), dtype=np.float32)
    vertices[0::8] = p0_tl
    vertices[1::8] = p0_tr
    vertices[2::8] = p0_bl
    vertices[3::8] = p0_br
    vertices[4::8] = p1_tl
    vertices[5::8] = p1_tr
    vertices[6::8] = p1_bl
    vertices[7::8] = p1_br
    
    # 8 faces (triangles) per segment
    faces = np.empty((num_segments * 8, 3), dtype=np.uint32)
    base = np.arange(num_segments, dtype=np.uint32) * 8
    
    # Top quad (faces 0, 1)
    faces[0::8, 0] = base + 0
    faces[0::8, 1] = base + 1
    faces[0::8, 2] = base + 5
    faces[1::8, 0] = base + 0
    faces[1::8, 1] = base + 5
    faces[1::8, 2] = base + 4
    
    # Bottom quad (faces 2, 3)
    faces[2::8, 0] = base + 2
    faces[2::8, 1] = base + 6
    faces[2::8, 2] = base + 7
    faces[3::8, 0] = base + 2
    faces[3::8, 1] = base + 7
    faces[3::8, 2] = base + 3
    
    # Left quad (faces 4, 5)
    faces[4::8, 0] = base + 0
    faces[4::8, 1] = base + 4
    faces[4::8, 2] = base + 6
    faces[5::8, 0] = base + 0
    faces[5::8, 1] = base + 6
    faces[5::8, 2] = base + 2
    
    # Right quad (faces 6, 7)
    faces[6::8, 0] = base + 1
    faces[6::8, 1] = base + 3
    faces[6::8, 2] = base + 7
    faces[7::8, 0] = base + 1
    faces[7::8, 1] = base + 7
    faces[7::8, 2] = base + 5
    
    # Colors
    z_vals = p0[:, 2]
    z_range = z_max - z_min
    if z_range <= 0: z_range = 1.0
    t = (z_vals - z_min) / z_range
    
    color_cyan = np.array([0.0, 0.6, 0.8])
    color_purple = np.array([0.5, 0.0, 0.8])
    color_magenta = np.array([0.8, 0.0, 0.5])
    
    segment_colors = np.zeros((num_segments, 3), dtype=np.float32)
    mask_low = t < 0.5
    if np.any(mask_low):
        t_low = t[mask_low] * 2.0
        segment_colors[mask_low] = color_cyan[None, :] * (1 - t_low[:, None]) + color_purple[None, :] * t_low[:, None]
    mask_high = ~mask_low
    if np.any(mask_high):
        t_high = (t[mask_high] - 0.5) * 2.0
        segment_colors[mask_high] = color_purple[None, :] * (1 - t_high[:, None]) + color_magenta[None, :] * t_high[:, None]
        
    # Apply shading logic (Ambient Occlusion)
    face_colors = np.ones((num_segments * 8, 4), dtype=np.float32)
    # Top faces (1.0 brightness)
    face_colors[0::8, :3] = segment_colors
    face_colors[1::8, :3] = segment_colors
    # Bottom faces (0.4 brightness)
    face_colors[2::8, :3] = segment_colors * 0.4
    face_colors[3::8, :3] = segment_colors * 0.4
    # Side faces (0.7 brightness)
    face_colors[4::8, :3] = segment_colors * 0.7
    face_colors[5::8, :3] = segment_colors * 0.7
    face_colors[6::8, :3] = segment_colors * 0.7
    face_colors[7::8, :3] = segment_colors * 0.7
    
    return vertices, faces, face_colors
