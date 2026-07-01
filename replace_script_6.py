import re

with open('src/ui/widgets/slice_widget.py', 'r') as f:
    content = f.read()
    
old_block = """
                    for poly in layer.perimeters:
                        pts = poly.points
                        num_pts = len(pts)
                        if num_pts < 2: continue
                        
                        pts_3d = np.zeros((num_pts, 3))
                        pts_3d[:, :2] = pts
                        pts_3d[:, 2] = z
                        
                        idx0 = np.arange(num_pts)
                        idx1 = np.roll(idx0, -1)
                        pairs = np.empty((num_pts * 2, 3))
                        pairs[0::2] = pts_3d[idx0]
                        pairs[1::2] = pts_3d[idx1]
                        
                        z_groups[matched_z].append(pairs)
                        
            # Output Island Layers sequentially
            for z in sorted(z_groups.keys()):
                layer_pairs = []
                layer_colors = []
                group_polys = z_groups[z]
                
                for i in range(len(group_polys)):
                    pairs = group_polys[i]
                    layer_pairs.append(pairs)
                    layer_colors.append(np.tile(green_color, (len(pairs), 1)))
                    
                    if i < len(group_polys) - 1:
                        last_pt = pairs[-1]
                        next_pt = group_polys[i+1][0]
                        layer_pairs.append(np.array([last_pt, next_pt]))
                        layer_colors.append(np.tile(blue_color, (2, 1)))
"""

new_block = """
                    # Zip padded perimeters and infill lines
                    orange_color = (1.0, 0.5, 0.0, 1.0)
                    for poly, infill in zip(layer.perimeters, getattr(layer, 'infill_lines', [])):
                        if poly is not None:
                            pts = poly.points
                            num_pts = len(pts)
                            if num_pts < 2: continue
                            
                            pts_3d = np.zeros((num_pts, 3))
                            pts_3d[:, :2] = pts
                            pts_3d[:, 2] = z
                            
                            idx0 = np.arange(num_pts)
                            idx1 = np.roll(idx0, -1)
                            pairs = np.empty((num_pts * 2, 3))
                            pairs[0::2] = pts_3d[idx0]
                            pairs[1::2] = pts_3d[idx1]
                            
                            z_groups[matched_z].append((pairs, green_color))
                        elif infill is not None:
                            num_pts = len(infill)
                            if num_pts < 2: continue
                            
                            pts_3d = np.zeros((num_pts, 3))
                            pts_3d[:, :2] = infill
                            pts_3d[:, 2] = z
                            
                            idx0 = np.arange(num_pts - 1)
                            idx1 = idx0 + 1
                            pairs = np.empty(((num_pts - 1) * 2, 3))
                            pairs[0::2] = pts_3d[idx0]
                            pairs[1::2] = pts_3d[idx1]
                            
                            z_groups[matched_z].append((pairs, orange_color))
                            
            # Output Island Layers sequentially
            for z in sorted(z_groups.keys()):
                layer_pairs = []
                layer_colors = []
                group_polys = z_groups[z]
                
                for i in range(len(group_polys)):
                    pairs, color = group_polys[i]
                    layer_pairs.append(pairs)
                    layer_colors.append(np.tile(color, (len(pairs), 1)))
                    
                    if i < len(group_polys) - 1:
                        last_pt = pairs[-1]
                        next_pt = group_polys[i+1][0][0]
                        layer_pairs.append(np.array([last_pt, next_pt]))
                        layer_colors.append(np.tile(blue_color, (2, 1)))
"""

if old_block.strip() in content:
    content = content.replace(old_block.strip(), new_block.strip())
    with open('src/ui/widgets/slice_widget.py', 'w') as f:
        f.write(content)
    print("Successfully replaced.")
else:
    print("Old block not found!")
