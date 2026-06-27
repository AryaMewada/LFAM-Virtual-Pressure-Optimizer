import sys
from PyQt6.QtWidgets import QApplication
from src.ui.widgets.analysis_panel import AnalysisPanel

app = QApplication(sys.argv)
panel = AnalysisPanel()
panel.show()

# Test update_stats
stats_dict = {
    'layers': 100,
    'print_moves': "10,000",
    'travel_moves': "500",
    'sharp_corners': 60,
    'tight_curves': 20,
    'pressure_hotspots': 25,
    'est_print_time': "1h 30m",
    'avg_flow_rate': "45.0 mm³/s"
}
try:
    panel.update_stats(stats_dict)
    panel.repaint()
    print("update_stats succeeded!")
except Exception as e:
    print(f"update_stats FAILED: {e}")

sys.exit(0)
