import os
import json
import math

base_dir = '/Users/admin/.gemini/antigravity/scratch/lfam-optimizer'
materials_dir = os.path.join(base_dir, 'src/profiles/materials')
machines_dir = os.path.join(base_dir, 'src/profiles/machines')
fixtures_dir = os.path.join(base_dir, 'tests/fixtures')

os.makedirs(materials_dir, exist_ok=True)
os.makedirs(machines_dir, exist_ok=True)
os.makedirs(fixtures_dir, exist_ok=True)

# 1. Materials
materials = {
    "abs.json": {
        "name": "ABS",
        "id": "abs",
        "category": "Commodity",
        "temperature": { "nozzle": 240, "bed": 100 },
        "pressure_sensitivity": 0.6,
        "flow_characteristics": {
            "optimal_flow_rate": 50.0,
            "max_flow_rate": 120.0,
            "viscosity_index": 0.7,
            "melt_flow_index": 10.0
        },
        "corner_sensitivity": 0.6,
        "curve_sensitivity": 0.5,
        "pressure_decay": 0.85,
        "vpi_weights": {
            "flow": 0.20, "speed": 0.15, "corner": 0.20, "curve": 0.10,
            "history": 0.10, "acceleration": 0.10, "start_stop": 0.10, "density": 0.05
        },
        "optimization_defaults": {
            "corner_slowdown": 70, "curve_adaptation": 60, "start_ramp": 50,
            "end_taper": 50, "flow_smoothing": 40, "speed_smoothing": 30
        },
        "description": "Commodity ABS material with moderate pressure sensitivity and good flow."
    },
    "abs_gf.json": {
        "name": "ABS GF20",
        "id": "abs_gf",
        "category": "Engineering",
        "temperature": { "nozzle": 255, "bed": 105 },
        "pressure_sensitivity": 0.75,
        "flow_characteristics": {
            "optimal_flow_rate": 45.0, "max_flow_rate": 100.0, "viscosity_index": 0.85, "melt_flow_index": 6.0
        },
        "corner_sensitivity": 0.8,
        "curve_sensitivity": 0.6,
        "pressure_decay": 0.75,
        "vpi_weights": {
            "flow": 0.25, "speed": 0.15, "corner": 0.25, "curve": 0.10,
            "history": 0.05, "acceleration": 0.05, "start_stop": 0.10, "density": 0.05
        },
        "optimization_defaults": {
            "corner_slowdown": 80, "curve_adaptation": 70, "start_ramp": 60,
            "end_taper": 60, "flow_smoothing": 50, "speed_smoothing": 40
        },
        "description": "ABS + 20% Glass Fiber. Higher viscosity, more corner sensitive, higher nozzle temp."
    },
    "nylon.json": {
        "name": "Nylon (PA6)",
        "id": "nylon",
        "category": "Engineering",
        "temperature": { "nozzle": 260, "bed": 90 },
        "pressure_sensitivity": 0.5,
        "flow_characteristics": {
            "optimal_flow_rate": 60.0, "max_flow_rate": 130.0, "viscosity_index": 0.5, "melt_flow_index": 15.0
        },
        "corner_sensitivity": 0.5,
        "curve_sensitivity": 0.4,
        "pressure_decay": 0.90,
        "vpi_weights": {
            "flow": 0.15, "speed": 0.15, "corner": 0.15, "curve": 0.10,
            "history": 0.15, "acceleration": 0.10, "start_stop": 0.10, "density": 0.10
        },
        "optimization_defaults": {
            "corner_slowdown": 60, "curve_adaptation": 50, "start_ramp": 40,
            "end_taper": 40, "flow_smoothing": 35, "speed_smoothing": 25
        },
        "description": "Engineering Nylon. Higher temps, moisture sensitive, good flow."
    },
    "nylon_gf.json": {
        "name": "Nylon (PA6) GF30",
        "id": "nylon_gf",
        "category": "Engineering",
        "temperature": { "nozzle": 275, "bed": 100 },
        "pressure_sensitivity": 0.9,
        "flow_characteristics": {
            "optimal_flow_rate": 35.0, "max_flow_rate": 80.0, "viscosity_index": 0.95, "melt_flow_index": 3.0
        },
        "corner_sensitivity": 0.95,
        "curve_sensitivity": 0.8,
        "pressure_decay": 0.65,
        "vpi_weights": {
            "flow": 0.30, "speed": 0.20, "corner": 0.30, "curve": 0.05,
            "history": 0.05, "acceleration": 0.05, "start_stop": 0.05, "density": 0.0
        },
        "optimization_defaults": {
            "corner_slowdown": 90, "curve_adaptation": 85, "start_ramp": 70,
            "end_taper": 70, "flow_smoothing": 60, "speed_smoothing": 50
        },
        "description": "Nylon + 30% Glass Fiber. Much higher viscosity, very corner sensitive, needs slower speeds."
    },
    "petg.json": {
        "name": "PETG",
        "id": "petg",
        "category": "Commodity",
        "temperature": { "nozzle": 245, "bed": 85 },
        "pressure_sensitivity": 0.55,
        "flow_characteristics": {
            "optimal_flow_rate": 55.0, "max_flow_rate": 110.0, "viscosity_index": 0.65, "melt_flow_index": 12.0
        },
        "corner_sensitivity": 0.65,
        "curve_sensitivity": 0.55,
        "pressure_decay": 0.80,
        "vpi_weights": {
            "flow": 0.20, "speed": 0.15, "corner": 0.20, "curve": 0.10,
            "history": 0.10, "acceleration": 0.10, "start_stop": 0.10, "density": 0.05
        },
        "optimization_defaults": {
            "corner_slowdown": 65, "curve_adaptation": 60, "start_ramp": 45,
            "end_taper": 45, "flow_smoothing": 40, "speed_smoothing": 30
        },
        "description": "Commodity PETG. Easy to print, moderate everything."
    },
    "petg_cf.json": {
        "name": "PETG CF15",
        "id": "petg_cf",
        "category": "Engineering",
        "temperature": { "nozzle": 255, "bed": 90 },
        "pressure_sensitivity": 0.8,
        "flow_characteristics": {
            "optimal_flow_rate": 40.0, "max_flow_rate": 90.0, "viscosity_index": 0.88, "melt_flow_index": 5.0
        },
        "corner_sensitivity": 0.85,
        "curve_sensitivity": 0.7,
        "pressure_decay": 0.70,
        "vpi_weights": {
            "flow": 0.25, "speed": 0.20, "corner": 0.25, "curve": 0.10,
            "history": 0.05, "acceleration": 0.05, "start_stop": 0.05, "density": 0.05
        },
        "optimization_defaults": {
            "corner_slowdown": 85, "curve_adaptation": 75, "start_ramp": 65,
            "end_taper": 65, "flow_smoothing": 55, "speed_smoothing": 45
        },
        "description": "PETG + 15% Carbon Fiber. Stiffer melt, more pressure sensitive."
    },
    "pp.json": {
        "name": "Polypropylene",
        "id": "pp",
        "category": "Commodity",
        "temperature": { "nozzle": 230, "bed": 80 },
        "pressure_sensitivity": 0.4,
        "flow_characteristics": {
            "optimal_flow_rate": 70.0, "max_flow_rate": 150.0, "viscosity_index": 0.4, "melt_flow_index": 20.0
        },
        "corner_sensitivity": 0.4,
        "curve_sensitivity": 0.3,
        "pressure_decay": 0.95,
        "vpi_weights": {
            "flow": 0.10, "speed": 0.10, "corner": 0.10, "curve": 0.10,
            "history": 0.20, "acceleration": 0.15, "start_stop": 0.15, "density": 0.10
        },
        "optimization_defaults": {
            "corner_slowdown": 50, "curve_adaptation": 40, "start_ramp": 30,
            "end_taper": 30, "flow_smoothing": 25, "speed_smoothing": 20
        },
        "description": "Commodity PP. Low viscosity, fast printing, very flexible melt."
    },
    "pesu.json": {
        "name": "PESU",
        "id": "pesu",
        "category": "High-Performance",
        "temperature": { "nozzle": 380, "bed": 160 },
        "pressure_sensitivity": 0.95,
        "flow_characteristics": {
            "optimal_flow_rate": 30.0, "max_flow_rate": 70.0, "viscosity_index": 0.98, "melt_flow_index": 2.0
        },
        "corner_sensitivity": 0.95,
        "curve_sensitivity": 0.9,
        "pressure_decay": 0.60,
        "vpi_weights": {
            "flow": 0.30, "speed": 0.20, "corner": 0.30, "curve": 0.10,
            "history": 0.05, "acceleration": 0.05, "start_stop": 0.0, "density": 0.0
        },
        "optimization_defaults": {
            "corner_slowdown": 95, "curve_adaptation": 90, "start_ramp": 80,
            "end_taper": 80, "flow_smoothing": 70, "speed_smoothing": 60
        },
        "description": "High-performance PESU. Very high temps, very high viscosity, extremely corner sensitive."
    },
    "peek.json": {
        "name": "PEEK",
        "id": "peek",
        "category": "High-Performance",
        "temperature": { "nozzle": 410, "bed": 180 },
        "pressure_sensitivity": 1.0,
        "flow_characteristics": {
            "optimal_flow_rate": 25.0, "max_flow_rate": 60.0, "viscosity_index": 1.0, "melt_flow_index": 1.5
        },
        "corner_sensitivity": 1.0,
        "curve_sensitivity": 0.95,
        "pressure_decay": 0.55,
        "vpi_weights": {
            "flow": 0.35, "speed": 0.25, "corner": 0.30, "curve": 0.10,
            "history": 0.0, "acceleration": 0.0, "start_stop": 0.0, "density": 0.0
        },
        "optimization_defaults": {
            "corner_slowdown": 100, "curve_adaptation": 95, "start_ramp": 85,
            "end_taper": 85, "flow_smoothing": 80, "speed_smoothing": 70
        },
        "description": "High-performance PEEK. Highest temps, highest viscosity, most demanding optimization."
    }
}

for filename, data in materials.items():
    with open(os.path.join(materials_dir, filename), 'w') as f:
        json.dump(data, f, indent=2)


# 2. Machines
machines = {
    "generic_lfam.json": {
        "name": "Generic LFAM System",
        "id": "generic_lfam",
        "description": "Generic large format additive manufacturing system with single-screw pellet extruder",
        "nozzle_diameter": 4.0,
        "layer_height": 2.0,
        "extrusion_width": 6.0,
        "screw_diameter": 30,
        "screw_rpm_limits": { "min": 5, "max": 200 },
        "max_feedrate": 6000,
        "max_acceleration": 500,
        "build_volume": { "x": 1000, "y": 1000, "z": 500 },
        "motion_controller": "Duet3",
        "extruder_type": "single-screw",
        "firmware": "RepRapFirmware"
    },
    "large_pellet_printer.json": {
        "name": "Large Pellet Printer",
        "id": "large_pellet_printer",
        "description": "Larger machine with twin-screw extruder and high throughput",
        "nozzle_diameter": 8.0,
        "layer_height": 3.0,
        "extrusion_width": 12.0,
        "screw_diameter": 45,
        "screw_rpm_limits": { "min": 10, "max": 300 },
        "max_feedrate": 10000,
        "max_acceleration": 800,
        "build_volume": { "x": 2000, "y": 2000, "z": 1000 },
        "motion_controller": "Beckhoff",
        "extruder_type": "twin-screw",
        "firmware": "Custom"
    }
}

for filename, data in machines.items():
    with open(os.path.join(machines_dir, filename), 'w') as f:
        json.dump(data, f, indent=2)

# 3. G-code Fixtures
e_per_mm = 0.955

# 3.1 simple_cube.gcode
def generate_simple_cube():
    lines = [
        ";TYPE:Header",
        ";Machine: Generic LFAM",
        ";Material: ABS",
        "G28",
        "M82",
        "G90",
        "M104 S240",
        "M140 S100",
        "M109 S240",
        "M190 S100"
    ]
    e_val = 0.0
    feedrate = 2000
    for layer in range(1, 4):
        z = layer * 2.0
        lines.append(f";LAYER:{layer-1}")
        lines.append(f"G1 Z{z:.3f} F{feedrate}")
        
        lines.append(";TYPE:Perimeter")
        lines.append(f"G1 X100.0 Y100.0 F3000")
        
        e_val += 100.0 * e_per_mm; lines.append(f"G1 X200.0 Y100.0 E{e_val:.3f} F{feedrate}")
        e_val += 100.0 * e_per_mm; lines.append(f"G1 X200.0 Y200.0 E{e_val:.3f}")
        e_val += 100.0 * e_per_mm; lines.append(f"G1 X100.0 Y200.0 E{e_val:.3f}")
        e_val += 100.0 * e_per_mm; lines.append(f"G1 X100.0 Y100.0 E{e_val:.3f}")
        
        lines.append(";TYPE:Infill")
        for y in range(110, 200, 10):
            lines.append(f"G1 X100.0 Y{y:.1f} F3000")
            e_val += 100.0 * e_per_mm
            lines.append(f"G1 X200.0 Y{y:.1f} E{e_val:.3f} F{feedrate}")
            
    lines.extend(["M104 S0", "M140 S0", "G28"])
    with open(os.path.join(fixtures_dir, 'simple_cube.gcode'), 'w') as f:
        f.write('\\n'.join(lines) + '\\n')

generate_simple_cube()

# 3.2 curved_vase.gcode
def generate_curved_vase():
    lines = [
        ";TYPE:Header",
        ";Machine: Generic LFAM",
        ";Material: PETG",
        "G28", "M82", "G90",
        "M104 S245", "M140 S85", "M109 S245", "M190 S85"
    ]
    e_val = 0.0
    feedrate = 2500
    r1 = 50.0
    r2 = 10.0
    arc_len = (math.pi * r1) / 2
    arc_len_tight = math.pi * r2
    
    for layer in range(1, 4):
        z = layer * 2.0
        lines.append(f";LAYER:{layer-1}")
        lines.append(f"G1 Z{z:.3f} F{feedrate}")
        
        lines.append(";TYPE:Perimeter")
        lines.append("G1 X150.0 Y100.0 F3000")
        
        e_val += arc_len * e_per_mm; lines.append(f"G3 X100.0 Y150.0 I-50.0 J0.0 E{e_val:.3f} F{feedrate}")
        e_val += arc_len * e_per_mm; lines.append(f"G3 X50.0 Y100.0 I0.0 J-50.0 E{e_val:.3f}")
        e_val += arc_len * e_per_mm; lines.append(f"G3 X100.0 Y50.0 I50.0 J0.0 E{e_val:.3f}")
        e_val += arc_len * e_per_mm; lines.append(f"G3 X150.0 Y100.0 I0.0 J50.0 E{e_val:.3f}")
        
        lines.append("G1 X160.0 Y100.0 F3000")
        e_val += arc_len_tight * e_per_mm; lines.append(f"G2 X160.0 Y80.0 I0.0 J-10.0 E{e_val:.3f} F1500")
        
    lines.extend(["M104 S0", "M140 S0", "G28"])
    with open(os.path.join(fixtures_dir, 'curved_vase.gcode'), 'w') as f:
        f.write('\\n'.join(lines) + '\\n')

generate_curved_vase()

# 3.3 complex_part.gcode
def generate_complex_part():
    lines = [
        ";TYPE:Header",
        ";Machine: Large Pellet Printer",
        ";Material: PEEK",
        "G28", "M82", "G90",
        "M104 S410", "M140 S180", "M109 S410", "M190 S180"
    ]
    e_val = 0.0
    for layer in range(1, 5):
        z = layer * 3.0
        lines.append(f";LAYER:{layer-1}")
        lines.append(f"G1 Z{z:.3f} F2000")
        
        lines.append(";TYPE:Perimeter")
        lines.append("G1 X50.0 Y50.0 F4000")
        e_val += 50.0 * e_per_mm; lines.append(f"G1 X100.0 Y50.0 E{e_val:.3f} F3000")
        
        dist = math.sqrt(50**2 + 50**2)
        e_val += dist * e_per_mm; lines.append(f"G1 X150.0 Y100.0 E{e_val:.3f}")
        
        e_val += 50.0 * e_per_mm; lines.append(f"G1 X100.0 Y100.0 E{e_val:.3f}")
        e_val += 50.0 * e_per_mm; lines.append(f"G1 X100.0 Y150.0 E{e_val:.3f}")
        e_val += 50.0 * e_per_mm; lines.append(f"G1 X50.0 Y150.0 E{e_val:.3f}")
        e_val += 100.0 * e_per_mm; lines.append(f"G1 X50.0 Y50.0 E{e_val:.3f}")
        
        lines.append("G1 X160.0 Y160.0 F4000")
        
        lines.append(";TYPE:InnerFeature")
        arc_len = (math.pi * 20) / 2
        e_val += arc_len * e_per_mm; lines.append(f"G3 X200.0 Y160.0 I20.0 J0.0 E{e_val:.3f} F2000")
        e_val += arc_len * e_per_mm; lines.append(f"G3 X160.0 Y160.0 I-20.0 J0.0 E{e_val:.3f}")
        
        lines.append(";TYPE:Infill")
        for x in range(55, 96, 10):
            lines.append(f"G1 X{x:.1f} Y55.0 F4000")
            e_val += 40.0 * e_per_mm; lines.append(f"G1 X{x:.1f} Y95.0 E{e_val:.3f} F3500")
            e_val += 10.0 * e_per_mm; lines.append(f"G1 X{x+5:.1f} Y95.0 E{e_val:.3f}")
            e_val += 40.0 * e_per_mm; lines.append(f"G1 X{x+5:.1f} Y55.0 E{e_val:.3f}")
            
    lines.extend(["M104 S0", "M140 S0", "G28"])
    with open(os.path.join(fixtures_dir, 'complex_part.gcode'), 'w') as f:
        f.write('\\n'.join(lines) + '\\n')

generate_complex_part()
