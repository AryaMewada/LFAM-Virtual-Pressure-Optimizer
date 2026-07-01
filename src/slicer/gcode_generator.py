import numpy as np
from typing import List
from .types import SliceResult

class GCodeGenerator:
    def __init__(self, layer_height: float, extrusion_width: float, 
                 filament_diameter: float = 1.75, 
                 travel_speed: int = 3000, 
                 print_speed: int = 1500,
                 z_hop: float = 2.0):
        self.layer_height = layer_height
        self.extrusion_width = extrusion_width
        self.filament_area = np.pi * ((filament_diameter / 2.0) ** 2)
        self.travel_speed = travel_speed
        self.print_speed = print_speed
        self.z_hop = z_hop
        
        self.current_e = 0.0
        self.current_x = 0.0
        self.current_y = 0.0
        self.lines = []
        
    def begin(self, bed_temp=110, nozzle_temp=235):
        self.lines = []
        self.lines.append("; =========================================")
        self.lines.append("; LFAM Optimizer - Optimized G-code")
        self.lines.append("; =========================================")
        self.lines.append(f"; layer_height = {self.layer_height}mm")
        self.lines.append(f"; extrusion_width = {self.extrusion_width}mm")
        self.lines.append("")
        self.lines.append(f"M190 S{bed_temp} ; set bed temperature and wait")
        self.lines.append(f"G10 S{nozzle_temp} P0 ; set hotend temperature")
        self.lines.append("G28 ; home all axes")
        self.lines.append("G0 Z5.0000 F5000 ; lift nozzle")
        self.lines.append("T0 ; Select tool 0")
        self.lines.append("G1 E20.0000 F60 ; Purge")
        self.lines.append("M116 ; wait for temperature to be reached")
        self.lines.append("G21 ; set units to millimeters")
        self.lines.append("G90 ; use absolute coordinates")
        self.lines.append("M83 ; use relative distances for extrusion")
        self.lines.append("M107 ; Disable fan for first layers")
        self.lines.append("M204 P100 ; Set default printing acceleration")
        self.lines.append("G92 E0 ; Reset Extruder")
        
        self.current_x = 0.0
        self.current_y = 0.0
        self.current_e = 0.0
        
    def add_result(self, result: SliceResult, island_idx: int, model_idx: int):
        self.lines.append(f"; --- Island {island_idx} Model {model_idx} ---")
        
        for i, layer in enumerate(result.layers):
            self.lines.append(f"; --- Layer {i} (Z={layer.z_height:.2f}) ---")
            
            # Z Hop and Move to start
            self.lines.append(f"G0 Z{layer.z_height + self.z_hop:.3f} F{self.travel_speed}")
            
            for perim, infill in zip(layer.perimeters, getattr(layer, 'infill_lines', [])):
                if perim is not None:
                    pts = perim.points
                    if len(pts) < 2: continue
                    
                    self.lines.append(f"G0 X{pts[0][0]:.3f} Y{pts[0][1]:.3f} F{self.travel_speed}")
                    self.lines.append(f"G0 Z{layer.z_height:.3f} F{self.travel_speed}")
                    self.current_x, self.current_y = pts[0][0], pts[0][1]
                    
                    for pt in pts[1:]:
                        dist = np.hypot(pt[0] - self.current_x, pt[1] - self.current_y)
                        if dist > 0:
                            vol = dist * self.extrusion_width * self.layer_height
                            e_inc = vol / self.filament_area
                            self.current_e += e_inc
                            self.lines.append(f"G1 X{pt[0]:.3f} Y{pt[1]:.3f} E{e_inc:.5f} F{self.print_speed}")
                            self.current_x, self.current_y = pt[0], pt[1]
                            
                    # Close loop
                    dist = np.hypot(pts[0][0] - self.current_x, pts[0][1] - self.current_y)
                    if dist > 0:
                        vol = dist * self.extrusion_width * self.layer_height
                        e_inc = vol / self.filament_area
                        self.current_e += e_inc
                        self.lines.append(f"G1 X{pts[0][0]:.3f} Y{pts[0][1]:.3f} E{e_inc:.5f} F{self.print_speed}")
                        self.current_x, self.current_y = pts[0][0], pts[0][1]
                        
                    self.lines.append(f"G0 Z{layer.z_height + self.z_hop:.3f} F{self.travel_speed}")
                    
                elif infill is not None:
                    pts = infill
                    if len(pts) < 2: continue
                    
                    self.lines.append(f"G0 X{pts[0][0]:.3f} Y{pts[0][1]:.3f} F{self.travel_speed}")
                    self.lines.append(f"G0 Z{layer.z_height:.3f} F{self.travel_speed}")
                    self.current_x, self.current_y = pts[0][0], pts[0][1]
                    
                    for pt in pts[1:]:
                        dist = np.hypot(pt[0] - self.current_x, pt[1] - self.current_y)
                        if dist > 0:
                            vol = dist * self.extrusion_width * self.layer_height
                            e_inc = vol / self.filament_area
                            self.current_e += e_inc
                            self.lines.append(f"G1 X{pt[0]:.3f} Y{pt[1]:.3f} E{e_inc:.5f} F{self.print_speed}")
                            self.current_x, self.current_y = pt[0], pt[1]
                            
                    self.lines.append(f"G0 Z{layer.z_height + self.z_hop:.3f} F{self.travel_speed}")
                    
    def end(self) -> str:
        self.lines.append("; --- End Print ---")
        self.lines.append("G91 ; Relative positioning")
        self.lines.append("G0 Z20 F3000 ; Lift Z")
        self.lines.append("G90 ; Absolute positioning")
        self.lines.append("G28 X Y ; Home X Y")
        self.lines.append("M84 ; Disable motors")
        
        return "\n".join(self.lines)
