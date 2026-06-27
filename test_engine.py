try:
    from src.engine.parser.parser import GCodeParser
    from src.engine.analysis.geometry_analyzer import GeometryAnalyzer
    from src.engine.pressure.virtual_pressure_engine import VirtualPressureEngine
    from src.engine.optimizer.pressure_optimizer import PressureOptimizer, OptimizationSettings
    from src.engine.emitter.gcode_emitter import GCodeEmitter
    print("SUCCESS")
except Exception as e:
    print(f"FAILED: {e}")
