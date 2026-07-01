import re

with open('src/slicer/gcode_generator.py', 'r') as f:
    content = f.read()

replacement = """
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
"""

pattern_begin = re.compile(r'    def begin\(self\):.*?        self.current_e = 0\.0', re.DOTALL)
content = pattern_begin.sub(replacement.strip('\n'), content)

# Update to use relative E values since M83 was specified
# We just need to replace E{self.current_e:.5f} with E{e_inc:.5f}
content = content.replace("E{self.current_e:.5f}", "E{e_inc:.5f}")

with open('src/slicer/gcode_generator.py', 'w') as f:
    f.write(content)
print("Updated start g-code and switched to relative extrusion.")
