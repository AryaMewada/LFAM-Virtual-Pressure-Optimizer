import sys
from PyQt6.QtWidgets import QApplication
from src.ui.widgets.pressure_chart_widget import PressureChartWidget
from src.engine.pressure.virtual_pressure_engine import PressureResult

app = QApplication(sys.argv)
chart = PressureChartWidget()
chart.show()

# Test set_data with PressureResult
pr = [PressureResult(move_id=i, vpi=i*0.1, factors={}) for i in range(10)]
try:
    chart.set_data(pr)
    chart.repaint()
    print("set_data succeeded!")
except Exception as e:
    print(f"set_data FAILED: {e}")

sys.exit(0)
