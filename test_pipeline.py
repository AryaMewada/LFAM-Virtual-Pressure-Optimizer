import time
import tracemalloc
from src.engine.parser.parser import GCodeParser
from src.engine.analysis.geometry_analyzer import GeometryAnalyzer
from src.engine.pressure.virtual_pressure_engine import VirtualPressureEngine
from src.engine.optimizer.pressure_optimizer import PressureOptimizer, OptimizationSettings

def run_test():
    tracemalloc.start()
    
    t0 = time.time()
    print("Parsing...")
    parser = GCodeParser()
    moves = parser.parse_file("test.gcode")
    t1 = time.time()
    print(f"Parsed {len(moves)} moves in {t1 - t0:.2f}s")
    
    print("Analyzing...")
    analyzer = GeometryAnalyzer()
    analyzed_moves = analyzer.analyze(moves, {})
    t2 = time.time()
    print(f"Analyzed {len(analyzed_moves)} moves in {t2 - t1:.2f}s")
    
    print("Computing Pressure...")
    pressure_engine = VirtualPressureEngine({}, {})
    pressure_data = pressure_engine.compute_pressure(analyzed_moves)
    t3 = time.time()
    print(f"Computed pressure in {t3 - t2:.2f}s")
    
    print("Optimizing...")
    settings = OptimizationSettings(
        corner_slowdown=70,
        curve_adaptation=60,
        start_ramp=50,
        end_taper=50,
        flow_smoothing=40,
        speed_smoothing=40
    )
    optimizer = PressureOptimizer({}, {}, settings)
    result = optimizer.optimize(moves, analyzed_moves, pressure_data)
    t4 = time.time()
    print(f"Optimized in {t4 - t3:.2f}s")
    
    current, peak = tracemalloc.get_traced_memory()
    print(f"Memory Peak: {peak / 10**6:.2f} MB")
    tracemalloc.stop()

if __name__ == "__main__":
    run_test()
