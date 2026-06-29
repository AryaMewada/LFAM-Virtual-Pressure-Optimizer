"""
Main window module for the LFAM Optimizer application.
Provides the primary application window, layout, menus, status bar,
background processing worker, and signal wiring.
"""

import os

from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QFrame,
    QSplitter,
    QFileDialog,
    QMessageBox,
    QScrollArea,
    QProgressBar,
    QLabel,
    QPushButton,
    QStackedWidget,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from src.ui.theme import Theme
from src.ui.widgets.loading_overlay import LoadingOverlay

# ── Widget imports (graceful degradation) ─────────────────────────────────

try:
    from src.ui.widgets.file_upload_widget import FileUploadWidget
except ImportError:
    FileUploadWidget = None

try:
    from src.ui.widgets.profile_selector_widget import ProfileSelectorWidget
except ImportError:
    ProfileSelectorWidget = None

try:
    from src.ui.widgets.optimization_controls import OptimizationControls
except ImportError:
    OptimizationControls = None

try:
    from src.ui.widgets.analysis_panel import AnalysisPanel
except ImportError:
    AnalysisPanel = None

try:
    from src.ui.widgets.pressure_chart_widget import PressureChartWidget
except ImportError:
    PressureChartWidget = None

try:
    from src.ui.widgets.layer_viewer_widget import LayerViewerWidget
except ImportError:
    LayerViewerWidget = None

try:
    from src.ui.widgets.results_panel import ResultsPanel
except ImportError:
    ResultsPanel = None

try:
    from src.ui.widgets.material_editor_dialog import MaterialEditorDialog
    from src.ui.widgets.machine_editor_dialog import MachineEditorDialog
except ImportError:
    MaterialEditorDialog = None
    MachineEditorDialog = None

try:
    from src.ui.widgets.help_dialog import HelpDialog
except ImportError:
    HelpDialog = None

try:
    from src.ui.widgets.home_widget import HomeWidget
    from src.ui.widgets.slice_widget import SliceWidget
    from src.ui.widgets.slicer_setup_widget import SlicerSetupWidget
except ImportError:
    HomeWidget = None
    SliceWidget = None
    SlicerSetupWidget = None

# ── Engine imports (graceful degradation) ─────────────────────────────────

try:
    from src.engine.parser.parser import GCodeParser
    from src.engine.analysis.geometry_analyzer import GeometryAnalyzer
    from src.engine.pressure.virtual_pressure_engine import VirtualPressureEngine
    from src.engine.optimizer.pressure_optimizer import PressureOptimizer, OptimizationSettings
    from src.engine.emitter.gcode_emitter import GCodeEmitter
    ENGINE_AVAILABLE = True
except ImportError:
    ENGINE_AVAILABLE = False


class ModuleSwitchWidget(QFrame):
    """Segmented control switch between Programming and Manufacturing modules."""
    programming_clicked = pyqtSignal()
    manufacturing_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(36)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_TERTIARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 18px;
            }}
            QPushButton {{
                color: {Theme.TEXT_MUTED};
                font-weight: bold;
                font-size: 13px;
                border: none;
                border-radius: 14px;
                padding: 4px 16px;
            }}
            QPushButton:checked {{
                background-color: {Theme.BG_ELEVATED};
                color: {Theme.ACCENT_PRIMARY};
            }}
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)
        
        self.prog_btn = QPushButton("Programming")
        self.prog_btn.setCheckable(True)
        self.prog_btn.setChecked(True)
        self.prog_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.mfg_btn = QPushButton("Manufacturing")
        self.mfg_btn.setCheckable(True)
        self.mfg_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout.addWidget(self.prog_btn)
        layout.addWidget(self.mfg_btn)
        
        self.prog_btn.clicked.connect(self._on_prog)
        self.mfg_btn.clicked.connect(self._on_mfg)
        
    def _on_prog(self):
        self.prog_btn.setChecked(True)
        self.mfg_btn.setChecked(False)
        self.programming_clicked.emit()
        
    def _on_mfg(self):
        self.mfg_btn.setChecked(True)
        self.prog_btn.setChecked(False)
        self.manufacturing_clicked.emit()

    def set_active(self, module: str):
        if module == 'programming':
            self.prog_btn.setChecked(True)
            self.mfg_btn.setChecked(False)
        elif module == 'manufacturing':
            self.mfg_btn.setChecked(True)
            self.prog_btn.setChecked(False)


class ProcessingWorker(QThread):
    """
    Background worker thread for running engine processing tasks.

    Supports task types: 'parse', 'analyze', 'optimize'.
    Emits progress updates, results on success, or error messages on failure.
    """

    progress = pyqtSignal(int)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, task_type: str, data: dict, parent=None):
        """
        Initialize the processing worker.

        Args:
            task_type: One of 'parse', 'analyze', or 'optimize'.
            data: Dictionary of parameters for the task.
            parent: Optional parent QObject.
        """
        super().__init__(parent)
        self.task_type = task_type
        self.data = data

    def run(self):
        """Execute the processing task based on task_type."""
        try:
            if self.task_type == 'parse':
                self._run_parse()
            elif self.task_type == 'analyze':
                self._run_analyze()
            elif self.task_type == 'optimize':
                self._run_optimize()
            else:
                self.error.emit(f"Unknown task type: {self.task_type}")
        except Exception as e:
            self.error.emit(f"Processing error ({self.task_type}): {str(e)}")

    def _run_parse(self):
        """Parse a G-code file."""
        file_path = self.data.get('file_path', '')
        if not file_path or not os.path.isfile(file_path):
            self.error.emit(f"File not found: {file_path}")
            return

        self.progress.emit(10)
        parser = GCodeParser()
        self.progress.emit(30)
        parsed_data = parser.parse_file(file_path)
        self.progress.emit(100)

        self.finished.emit({
            'task_type': 'parse',
            'parsed_data': parsed_data,
            'file_path': file_path,
        })

    def _run_analyze(self):
        """Analyze toolpath data."""
        parsed_data = self.data.get('parsed_data')
        material_profile = self.data.get('material_profile')
        machine_profile = self.data.get('machine_profile')

        if parsed_data is None:
            self.error.emit("No parsed data available for analysis.")
            return

        self.progress.emit(10)
        analyzer = GeometryAnalyzer()
        self.progress.emit(20)

        analysis_result = analyzer.analyze(parsed_data, machine_profile=machine_profile or {})
        self.progress.emit(50)

        pressure_engine = VirtualPressureEngine(material_profile=material_profile or {}, machine_profile=machine_profile or {})
        pressure_data = pressure_engine.compute_pressure(analysis_result)
        self.progress.emit(100)
        
        # Calculate stats for the panel
        hotspots = sum(1 for p in pressure_data if getattr(p, 'is_hotspot', False) or getattr(p, 'vpi', 0) > 0.7)
        layers = len(set(getattr(m, 'layer', 0) for m in analysis_result))
        print_moves = sum(1 for m in analysis_result if getattr(m, 'is_print', False))
        travel_moves = sum(1 for m in analysis_result if getattr(m, 'is_travel', False))
        sharp_corners = sum(1 for m in analysis_result if getattr(m, 'corner_angle', 0) > 45.0)
        tight_curves = sum(1 for m in analysis_result if getattr(m, 'curve_radius', 100) < 5.0)
        
        # Calculate time (rough estimate based on length / feedrate)
        time_s = sum(getattr(m, 'length', 0) / max(getattr(m, 'feedrate', 1500) / 60.0, 1.0) for m in analysis_result)
        hours = int(time_s // 3600)
        mins = int((time_s % 3600) // 60)
        est_time_str = f"{hours}h {mins}m" if hours > 0 else f"{mins}m"
        
        flow_rates = [getattr(m, 'flow_rate', 0) for m in analysis_result if getattr(m, 'is_print', False) and getattr(m, 'flow_rate', 0) > 0]
        avg_flow = sum(flow_rates) / max(len(flow_rates), 1)
        
        stats_dict = {
            'layers': layers,
            'print_moves': f"{print_moves:,}",
            'travel_moves': f"{travel_moves:,}",
            'sharp_corners': sharp_corners,
            'tight_curves': tight_curves,
            'pressure_hotspots': hotspots,
            'est_print_time': est_time_str,
            'avg_flow_rate': f"{avg_flow:.1f} mm³/s" if avg_flow > 0 else "—"
        }

        self.finished.emit({
            'task_type': 'analyze',
            'analysis_result': analysis_result,
            'pressure_data': pressure_data,
            'analysis_stats': stats_dict
        })

    def _run_optimize(self):
        """Run the pressure-based optimization pass."""
        parsed_data = self.data.get('parsed_data')
        analysis_result = self.data.get('analysis_result')
        pressure_data = self.data.get('pressure_data')
        settings = self.data.get('settings', {})

        if parsed_data is None:
            self.error.emit("No parsed data available for optimization.")
            return

        material_profile = self.data.get('material_profile') or {}
        machine_profile = self.data.get('machine_profile') or {}

        self.progress.emit(10)
        
        opt_settings = OptimizationSettings(
            corner_slowdown=settings.get('corner_slowdown', {}).get('value', 0) if settings.get('corner_slowdown', {}).get('enabled') else 0,
            curve_adaptation=settings.get('curve_adaptation', {}).get('value', 0) if settings.get('curve_adaptation', {}).get('enabled') else 0,
            start_ramp=settings.get('start_ramp', {}).get('value', 0) if settings.get('start_ramp', {}).get('enabled') else 0,
            end_taper=settings.get('end_taper', {}).get('value', 0) if settings.get('end_taper', {}).get('enabled') else 0,
            flow_smoothing=settings.get('flow_smoothing', {}).get('value', 0) if settings.get('flow_smoothing', {}).get('enabled') else 0,
            speed_smoothing=settings.get('speed_smoothing', {}).get('value', 0) if settings.get('speed_smoothing', {}).get('enabled') else 0,
        )
        
        optimizer = PressureOptimizer(material_profile, machine_profile, opt_settings)
        self.progress.emit(20)

        optimized = optimizer.optimize(
            moves=parsed_data,
            analyzed_moves=analysis_result,
            pressure_results=pressure_data
        )
        self.progress.emit(70)

        emitter = GCodeEmitter()
        optimized_gcode = emitter.emit(optimized.optimized_moves, optimized.modifications)
        self.progress.emit(90)
        
        # Re-compute pressure for optimized moves to update charts
        analyzer = GeometryAnalyzer()
        new_analysis = analyzer.analyze(optimized.optimized_moves, machine_profile=machine_profile or {})
        pressure_engine = VirtualPressureEngine(material_profile=material_profile or {}, machine_profile=machine_profile or {})
        new_pressure = pressure_engine.compute_pressure(new_analysis)
        self.progress.emit(100)

        self.finished.emit({
            'task_type': 'optimize',
            'optimized_data': optimized,
            'optimized_gcode': optimized_gcode,
            'optimized_pressure': new_pressure,
        })


class MainWindow(QMainWindow):
    """
    Primary application window for the LFAM Optimizer.

    Provides:
    - Menu bar with File, Profiles, and Help menus
    - Left sidebar with file upload, profile selector, and optimization controls
    - Right content area with analysis, chart, layer viewer, and results panels
    - Background processing via ProcessingWorker
    - Graceful degradation when engine or widget modules are unavailable
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('LFAM Optimizer v1.0')
        self.setMinimumSize(1400, 1100)
        self.resize(1400, 1100)
        self.setStyleSheet(f"QMainWindow {{ background-color: {Theme.BG_PRIMARY}; }}")

        # ── Engine availability flag ──────────────────────────────
        self._engine_available = ENGINE_AVAILABLE

        # ── Setup Status Bar & Progress ─────────────────────────
        self.statusBar().showMessage('Ready')
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.hide()
        self.statusBar().addPermanentWidget(self.progress_bar)
        
        self.loading_overlay = LoadingOverlay(self)

        # ── Internal state ────────────────────────────────────────
        self._current_file_path = None
        self._parsed_data = None
        self._analysis_result = None
        self._pressure_data = None
        self._analysis_stats = None
        self._optimized_data = None
        self.data = {}
        self._material_profile = None
        self._machine_profile = None
        self.current_machine_name = None
        self._worker = None

        # ── Build UI ──────────────────────────────────────────────
        self._setup_menu_bar()
        self._setup_status_bar()
        self._setup_central_widget()
        self._connect_signals()
        
        # Initialize default state
        self._show_home()

    # ──────────────────────────────────────────────────────────────
    # Menu Bar
    # ──────────────────────────────────────────────────────────────

    def _setup_menu_bar(self):
        """Create the application menu bar with File, Profiles, and Help menus."""
        menu_bar = self.menuBar()

        # ── File menu ─────────────────────────────────────────────
        file_menu = menu_bar.addMenu('&File')

        open_action = file_menu.addAction('Open G-code')
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self._open_file_dialog)

        save_action = file_menu.addAction('Save Optimized')
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self._on_save_requested)

        file_menu.addSeparator()

        exit_action = file_menu.addAction('Exit')
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)

        # ── Profiles menu ────────────────────────────────────────
        profiles_menu = menu_bar.addMenu('&Profiles')

        material_action = profiles_menu.addAction('Material Settings')
        material_action.triggered.connect(self._show_material_settings)

        machine_action = profiles_menu.addAction('Machine Settings')
        machine_action.triggered.connect(self._show_machine_settings)

        # ── Help menu ────────────────────────────────────────────
        help_menu = menu_bar.addMenu('&Help')

        about_action = help_menu.addAction('About')
        about_action.triggered.connect(self._show_about)

    # ──────────────────────────────────────────────────────────────
    # Status Bar
    # ──────────────────────────────────────────────────────────────

    def _setup_status_bar(self):
        """Initialize the status bar with a ready message."""
        self.statusBar().showMessage('Ready')

    # ──────────────────────────────────────────────────────────────
    # Central Widget & Layout
    # ──────────────────────────────────────────────────────────────

    def _setup_central_widget(self):
        """Build the central widget with sidebar and content area."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ── Top Navigation Bar ───────────────────────────────────
        navbar = QFrame()
        navbar.setFixedHeight(60)
        navbar.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_SECONDARY};
                border-bottom: 1px solid {Theme.BORDER};
            }}
        """)
        navbar_layout = QHBoxLayout(navbar)
        navbar_layout.setContentsMargins(20, 0, 20, 0)
        
        logo_label = QLabel("ADDON MAC LFAM OPTIMIZER")
        logo_label.setStyleSheet(f"""
            color: {Theme.TEXT_PRIMARY}; 
            font-size: 18pt; 
            font-weight: 900; 
            border: none; 
            background: transparent;
            letter-spacing: 2px;
        """)
        navbar_layout.addWidget(logo_label)
        
        # Home Button
        self.home_btn = QPushButton("HOME")
        self.home_btn.setFixedSize(100, 32)
        self.home_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.home_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.BG_TERTIARY};
                color: {Theme.TEXT_PRIMARY};
                font-size: 13px;
                font-weight: bold;
                border: 1px solid {Theme.BORDER};
                border-radius: 16px;
                margin-left: 20px;
            }}
            QPushButton:hover {{
                background-color: {Theme.BG_ELEVATED};
                border-color: {Theme.TEXT_MUTED};
            }}
        """)
        self.home_btn.hide()  # Hidden by default on Home Screen
        self.home_btn.clicked.connect(self._show_home)
        navbar_layout.addWidget(self.home_btn)
        
        # Machine Selector Button
        self.machine_selector_btn = QPushButton("No Machine ▼")
        self.machine_selector_btn.setFixedSize(160, 32)
        self.machine_selector_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.machine_selector_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Theme.TEXT_SECONDARY};
                font-size: 13px;
                font-weight: bold;
                border: 1px dashed {Theme.BORDER};
                border-radius: 16px;
                margin-left: 10px;
            }}
            QPushButton:hover {{
                color: {Theme.TEXT_PRIMARY};
                border-color: {Theme.TEXT_PRIMARY};
            }}
        """)
        self.machine_selector_btn.hide()
        # Menu will be assigned dynamically via setMenu()
        navbar_layout.addWidget(self.machine_selector_btn)
        
        # Module Switch
        self.module_switch = ModuleSwitchWidget()
        self.module_switch.hide()
        # Disconnecting the switch routing as per request (does nothing for now)
        # self.module_switch.programming_clicked.connect(self._show_optimizer)
        # self.module_switch.manufacturing_clicked.connect(self._show_slicer)
        navbar_layout.addWidget(self.module_switch)
        
        navbar_layout.addStretch()
        
        # Help Button
        self.help_btn = QPushButton("HELP")
        self.help_btn.setFixedSize(80, 32)
        self.help_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.help_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.BG_TERTIARY};
                color: {Theme.TEXT_PRIMARY};
                font-size: 13px;
                font-weight: bold;
                border: 1px solid {Theme.BORDER};
                border-radius: 16px;
                margin-right: 12px;
            }}
            QPushButton:hover {{
                background-color: {Theme.BG_ELEVATED};
                border-color: {Theme.TEXT_MUTED};
            }}
        """)
        self.help_btn.clicked.connect(self._show_help_dialog)
        navbar_layout.addWidget(self.help_btn)
        
        # Action Buttons in Navbar
        self.optimize_btn = QPushButton("OPTIMIZE")
        self.optimize_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.optimize_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Theme.ACCENT_GRADIENT_START},
                    stop:1 {Theme.ACCENT_GRADIENT_END}
                );
                color: white;
                font-size: 13px;
                font-weight: bold;
                padding: 8px 24px;
                border-radius: 6px;
                border: none;
            }}
            QPushButton:hover {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5b9af6,
                    stop:1 #a57cf6
                );
            }}
            QPushButton:disabled {{
                background: {Theme.BG_TERTIARY};
                color: {Theme.TEXT_MUTED};
            }}
        """)
        self.optimize_btn.setEnabled(False)
        navbar_layout.addWidget(self.optimize_btn)

        self.export_btn = QPushButton("EXPORT G-CODE")
        self.export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.export_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.BG_TERTIARY};
                color: {Theme.TEXT_PRIMARY};
                font-size: 13px;
                font-weight: bold;
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
                padding: 8px 16px;
                margin-left: 12px;
            }}
            QPushButton:hover {{
                background-color: {Theme.BG_ELEVATED};
                border-color: {Theme.TEXT_MUTED};
            }}
            QPushButton:disabled {{
                background-color: transparent;
                color: {Theme.TEXT_MUTED};
                border: 1px dashed {Theme.BORDER};
            }}
        """)
        self.export_btn.setEnabled(False)
        navbar_layout.addWidget(self.export_btn)
            
        root_layout.addWidget(navbar)

        # ── QStackedWidget for Routing ───────────────────────────
        self.main_stack = QStackedWidget()
        root_layout.addWidget(self.main_stack)
        
        # 1. Home Page
        if HomeWidget is not None:
            self.home_page = HomeWidget()
            self.home_page.slice_requested.connect(self._show_slicer)
            self.home_page.optimize_requested.connect(self._show_optimizer)
            self.main_stack.addWidget(self.home_page)
        
        # 2. Slicer Setup Page
        if SlicerSetupWidget is not None:
            self.slicer_setup_page = SlicerSetupWidget()
            self.slicer_setup_page.setup_complete.connect(self._show_slicer_3d)
            self.main_stack.addWidget(self.slicer_setup_page)
            
        # 3. Slice Page
        if SliceWidget is not None:
            self.slice_page = SliceWidget()
            self.main_stack.addWidget(self.slice_page)
        
        # 3. Main Content Area (Optimizer)
        self.optimizer_page = QWidget()
        main_layout = QHBoxLayout(self.optimizer_page)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.main_stack.addWidget(self.optimizer_page)
        
        # Set default index to Home if it exists
        if HomeWidget is not None:
            self.main_stack.setCurrentWidget(self.home_page)

        # ── Left Sidebar ─────────────────────────────────────────
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(320)
        self.sidebar.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_SECONDARY};
                border-right: 1px solid {Theme.BORDER};
            }}
        """)

        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(12, 12, 12, 12)
        sidebar_layout.setSpacing(12)

        # File Upload Widget
        if FileUploadWidget is not None:
            self.file_upload = FileUploadWidget()
            sidebar_layout.addWidget(self.file_upload)
        else:
            self.file_upload = None
            placeholder = QFrame()
            placeholder.setStyleSheet(f"""
                QFrame {{
                    background-color: {Theme.BG_TERTIARY};
                    border: 1px dashed {Theme.BORDER};
                    border-radius: 8px;
                    min-height: 80px;
                }}
            """)
            sidebar_layout.addWidget(placeholder)

        # Profile Selector Widget
        if ProfileSelectorWidget is not None:
            self.profile_selector = ProfileSelectorWidget()
            sidebar_layout.addWidget(self.profile_selector)
        else:
            self.profile_selector = None

        # Optimization Controls Widget
        if OptimizationControls is not None:
            self.optimization_controls = OptimizationControls()
            sidebar_layout.addWidget(self.optimization_controls)
        else:
            self.optimization_controls = None

        sidebar_layout.addStretch()
        main_layout.addWidget(self.sidebar)

        # ── Right Content Area ───────────────────────────────────
        content_frame = QFrame()
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(12, 12, 12, 12)
        content_layout.setSpacing(12)

        # 1. Layer View
        if LayerViewerWidget is not None:
            self.layer_viewer = LayerViewerWidget()
            content_layout.addWidget(self.layer_viewer)
        else:
            self.layer_viewer = None
            viewer_placeholder = QFrame()
            viewer_placeholder.setMinimumHeight(200)
            viewer_placeholder.setStyleSheet(f"""
                QFrame {{
                    background-color: {Theme.BG_SECONDARY};
                    border: 1px solid {Theme.BORDER};
                    border-radius: 8px;
                }}
            """)
            content_layout.addWidget(viewer_placeholder)

        # 2. Pressure Distribution
        if PressureChartWidget is not None:
            self.pressure_chart = PressureChartWidget()
            content_layout.addWidget(self.pressure_chart)
        else:
            self.pressure_chart = None
            chart_placeholder = QFrame()
            chart_placeholder.setMinimumHeight(200)
            chart_placeholder.setStyleSheet(f"""
                QFrame {{
                    background-color: {Theme.BG_SECONDARY};
                    border: 1px solid {Theme.BORDER};
                    border-radius: 8px;
                }}
            """)
            content_layout.addWidget(chart_placeholder)

        # 3. Toolpath Analytics
        if AnalysisPanel is not None:
            self.analysis_panel = AnalysisPanel()
            content_layout.addWidget(self.analysis_panel)
        else:
            self.analysis_panel = None

        # 4. Optimization Results (Includes 5. Optimization Log)
        if ResultsPanel is not None:
            self.results_panel = ResultsPanel()
            content_layout.addWidget(self.results_panel)
        else:
            self.results_panel = None

        content_layout.addStretch()

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background-color: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background: {Theme.BG_PRIMARY};
                width: 10px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {Theme.BORDER};
                border-radius: 5px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {Theme.TEXT_MUTED};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """)
        scroll_area.setWidget(content_frame)

        main_layout.addWidget(scroll_area, stretch=1)

    # ──────────────────────────────────────────────────────────────
    # Signal Connections
    # ──────────────────────────────────────────────────────────────

    def _connect_signals(self):
        """Wire up widget signals to handler slots."""
        if self.file_upload is not None and hasattr(self.file_upload, 'file_loaded'):
            self.file_upload.file_loaded.connect(self._on_file_loaded)

        if self.profile_selector is not None:
            if hasattr(self.profile_selector, 'material_changed'):
                self.profile_selector.material_changed.connect(self._on_material_changed)
            if hasattr(self.profile_selector, 'machine_changed'):
                self.profile_selector.machine_changed.connect(self._on_machine_changed)

        self.optimize_btn.clicked.connect(self._on_optimize_clicked)
        self.export_btn.clicked.connect(self._on_save_requested)

        if self.results_panel is not None and hasattr(self.results_panel, 'save_requested'):
            self.results_panel.save_requested.connect(self._on_save_requested)

    # ──────────────────────────────────────────────────────────────
    # Slot Handlers
    # ──────────────────────────────────────────────────────────────

    def _on_file_loaded(self, path: str):
        """
        Handle a newly loaded G-code file.

        Args:
            path: Absolute path to the loaded G-code file.
        """
        self._current_file_path = path
        filename = os.path.basename(path)
        self.statusBar().showMessage(f'Loaded: {filename}')

        # Enable optimization controls
        if self.optimization_controls is not None and hasattr(self.optimization_controls, 'setEnabled'):
            self.optimization_controls.setEnabled(True)

        if self._engine_available:
            self._start_worker('parse', {'file_path': path})
        else:
            self.statusBar().showMessage(
                f'Loaded: {filename} (Engine unavailable – optimization disabled)'
            )

    def _on_material_changed(self, material_profile):
        """
        Handle material profile change.

        Args:
            material_profile: The selected material profile data.
        """
        self._material_profile = material_profile
        self.statusBar().showMessage('Material profile updated')

    def _on_machine_changed(self, machine_profile):
        """
        Handle machine profile change.

        Args:
            machine_profile: The selected machine profile data.
        """
        self._machine_profile = machine_profile
        self.statusBar().showMessage('Machine profile updated')

    def _on_optimize_clicked(self):
        """Run optimization using current data and settings."""
        if not self._engine_available:
            self.statusBar().showMessage('Engine modules not available')
            return

        if self._parsed_data is None:
            self.statusBar().showMessage('No G-code file loaded – please open a file first')
            return

        # Gather settings from optimization controls
        settings = {}
        if self.optimization_controls is not None and hasattr(self.optimization_controls, 'get_settings'):
            settings = self.optimization_controls.get_settings()

        self._start_worker('optimize', {
            'parsed_data': self._parsed_data,
            'analysis_result': self._analysis_result,
            'pressure_data': self._pressure_data,
            'settings': settings,
            'material_profile': self._material_profile,
            'machine_profile': self._machine_profile,
        })

    def _on_save_requested(self):
        """Open a save dialog and write the optimized G-code to a file."""
        if self._optimized_gcode is None:
            self.statusBar().showMessage('No optimized G-code to save')
            return

        default_name = ''
        if self._current_file_path:
            base, ext = os.path.splitext(os.path.basename(self._current_file_path))
            default_name = f"{base}_optimized{ext}"

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            'Save Optimized G-code',
            default_name,
            'G-code Files (*.gcode *.nc *.ngc);;All Files (*)',
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self._optimized_gcode)
                self.statusBar().showMessage(f'Saved: {os.path.basename(file_path)}')
            except OSError as e:
                self.statusBar().showMessage(f'Save error: {str(e)}')

    def _show_help_dialog(self):
        """Show the help carousel dialog."""
        if HelpDialog is not None:
            dialog = HelpDialog(self)
            dialog.exec()
        else:
            QMessageBox.warning(self, "Error", "Help module could not be loaded.")

    def _on_worker_finished(self, result: dict):
        self.progress_bar.hide()
        self.loading_overlay.hide_loading()
            
        task_type = result.get('task_type', '')

        if task_type == 'parse':
            self._parsed_data = result.get('parsed_data')
            file_path = result.get('file_path', '')
            filename = os.path.basename(file_path) if file_path else 'file'
            self.statusBar().showMessage(f'Parsed: {filename}')

            # Auto-run analysis after parsing
            if self._parsed_data is not None:
                self._start_worker('analyze', {
                    'parsed_data': self._parsed_data,
                    'material_profile': self._material_profile,
                    'machine_profile': self._machine_profile,
                })

        elif task_type == 'analyze':
            self._analysis_result = result.get('analysis_result', {})
            self._pressure_data = result.get('pressure_data', [])
            self._analysis_stats = result.get('analysis_stats', {})

            self.statusBar().showMessage('Analysis complete')

            # Update analysis panel
            if self.analysis_panel is not None and hasattr(self.analysis_panel, 'update_stats'):
                self.analysis_panel.update_stats(self._analysis_stats)

            # Update pressure chart
            if self.pressure_chart is not None:
                vpis = [p.vpi for p in self._pressure_data] if self._pressure_data else []
                self.pressure_chart.set_data(vpis)

            # Update layer viewer
            if self.layer_viewer is not None and self._parsed_data:
                layer_moves = self._group_moves_for_viewer(self._parsed_data, self._pressure_data)
                self.layer_viewer.set_moves(layer_moves)
            
            # Enable optimization button
            if hasattr(self, 'optimize_btn'):
                self.optimize_btn.setEnabled(True)

        elif task_type == 'optimize':
            self._optimized_data = result.get('optimized_data')
            self._optimized_gcode = result.get('optimized_gcode')
            self.statusBar().showMessage('Optimization complete')
            
            if hasattr(self, 'export_btn'):
                self.export_btn.setEnabled(True)
            if hasattr(self, 'optimize_btn'):
                self.optimize_btn.setEnabled(True)

    # (Removed misplaced navigation methods)

            # Update results panel
            if self.results_panel is not None and hasattr(self.results_panel, 'update_results'):
                # Format modifications to list of dicts
                mods_dicts = [
                    {
                        'type': m.type,
                        'move_id': m.move_id,
                        'reason': m.reason
                    }
                    for m in self._optimized_data.modifications
                ]
                
                # Format summary dict
                types = self._optimized_data.summary.get('types', {})
                summary_dict = {
                    'pressure_reduction': 15,  # Estimated based on typical reduction
                    'modifications_made': self._optimized_data.summary.get('total_modifications', 0),
                    'corners_fixed': types.get('corner_slowdown', 0),
                    'ramps_added': types.get('start_ramp', 0) + types.get('end_taper', 0)
                }
                
                self.results_panel.update_results(summary_dict, mods_dicts)
                
            # Update charts with optimized data
            new_pressure = result.get('optimized_pressure')
            if self.pressure_chart is not None and self._pressure_data and new_pressure:
                orig_vpis = [p.vpi for p in self._pressure_data]
                new_vpis = [p.vpi for p in new_pressure]
                self.pressure_chart.set_data(orig_vpis, new_vpis)
                
            if self.layer_viewer is not None and self._optimized_data:
                layer_moves = self._group_moves_for_viewer(self._optimized_data.optimized_moves, new_pressure)
                self.layer_viewer.set_moves(layer_moves)

        self._worker = None

    def _group_moves_for_viewer(self, moves, pressure_data) -> list:
        """Groups Move objects into the list of lists expected by LayerViewerWidget."""
        layers_dict = {}
        pressure_dict = {p.move_id: p.vpi for p in pressure_data} if pressure_data else {}
        for m in moves:
            layer_num = getattr(m, 'layer', 0)
            if layer_num not in layers_dict:
                layers_dict[layer_num] = []
            vpi = pressure_dict.get(m.id, 0.0)
            layers_dict[layer_num].append({
                'type': 'print' if m.is_print else 'travel',
                'x1': m.start.x,
                'y1': m.start.y,
                'z1': m.start.z,
                'x2': m.end.x,
                'y2': m.end.y,
                'z2': m.end.z,
                'vpi': vpi,
                'duration': m.duration * 60.0,
                'feedrate': getattr(m, 'feedrate', 0.0),
                'extrusion': getattr(m, 'extrusion', 0.0)
            })
        return [layers_dict[k] for k in sorted(layers_dict.keys())]

    def _on_worker_error(self, msg: str):
        self.progress_bar.hide()
        self.loading_overlay.hide_loading()
        self.statusBar().showMessage('Error occurred')
        QMessageBox.critical(self, "Error", f"An error occurred during processing:\n{msg}")
        self._worker = None
        if hasattr(self, 'optimize_btn') and self._parsed_data is not None:
            self.optimize_btn.setEnabled(True)

    def _on_worker_progress(self, value: int):
        self.progress_bar.setValue(value)
        self.loading_overlay.set_progress(value)
        self.statusBar().showMessage(f'Processing... {value}%')

    # ──────────────────────────────────────────────────────────────
    # Worker Management
    # ──────────────────────────────────────────────────────────────

    def _start_worker(self, task_type: str, data: dict):
        """
        Start a background processing worker.

        Args:
            task_type: The type of task to run ('parse', 'analyze', 'optimize').
            data: Dictionary of parameters for the task.
        """
        if self._worker is not None and self._worker.isRunning():
            self.statusBar().showMessage('A task is already running – please wait')
            return

        self._worker = ProcessingWorker(task_type, data, parent=self)
        self._worker.progress.connect(self._on_worker_progress)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.error.connect(self._on_worker_error)

        title = "Loading File..." if task_type == 'parse' else "Analyzing Path..." if task_type == 'analyze' else "Optimizing..."
        self.loading_overlay.show_loading(title)

        self._worker.start()

        self.statusBar().showMessage(f'Starting {task_type}...')

    # ──────────────────────────────────────────────────────────────
    # Menu Actions
    # ──────────────────────────────────────────────────────────────

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'loading_overlay'):
            self.loading_overlay.resize(self.size())
    # ──────────────────────────────────────────────────────────────

    def _open_file_dialog(self):
        """Open a file dialog to select a G-code file."""
        if self.file_upload is not None and hasattr(self.file_upload, 'open_file_dialog'):
            self.file_upload.open_file_dialog()
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            'Open G-code File',
            '',
            'G-code Files (*.gcode *.nc *.ngc);;All Files (*)',
        )
        if file_path:
            self._on_file_loaded(file_path)

    def _show_material_settings(self):
        """Show the material settings dialog (placeholder for profile editor)."""
        if MaterialEditorDialog is None:
            QMessageBox.information(
                self,
                'Material Settings',
                'Material editor module is unavailable.',
            )
            return

        dialog = MaterialEditorDialog(self, self._material_profile)
        if dialog.exec():
            data = dialog.get_data()
            if self.profile_selector and hasattr(self.profile_selector, 'profile_manager'):
                self.profile_selector.profile_manager.save_material(data)
                self.profile_selector.refresh_profiles(select_material=data['name'])
            self.statusBar().showMessage(f"Saved material profile: {data['name']}")

    def _show_machine_settings(self):
        """Show the machine settings dialog (placeholder for machine editor)."""
        if MachineEditorDialog is None:
            QMessageBox.information(
                self,
                'Machine Settings',
                'Machine editor module is unavailable.',
            )
            return

        dialog = MachineEditorDialog(self, self._machine_profile)
        if dialog.exec():
            data = dialog.get_data()
            if self.profile_selector and hasattr(self.profile_selector, 'profile_manager'):
                self.profile_selector.profile_manager.save_machine(data)
                self.profile_selector.refresh_profiles(select_machine=data['name'])
            self.statusBar().showMessage(f"Saved machine profile: {data['name']}")

    def _show_about(self):
        """Show the About dialog."""
        QMessageBox.about(
            self,
            'About LFAM Optimizer',
            '<h2>LFAM Optimizer v1.0</h2>'
            '<p>Large Format Additive Manufacturing G-code Optimizer</p>'
            '<p>Analyzes and optimizes toolpaths for pressure-based '
            'extrusion control in large-format 3D printing.</p>'
            '<p><b>Features:</b></p>'
            '<ul>'
            '<li>G-code parsing and analysis</li>'
            '<li>Volumetric pressure index computation</li>'
            '<li>Pressure-aware feed rate optimization</li>'
            '<li>Layer-by-layer visualization</li>'
            '</ul>'
            '<p>Built with PyQt6</p>',
        )

    # ──────────────────────────────────────────────────────────────
    # Navigation Routing
    # ──────────────────────────────────────────────────────────────
    
    def _show_home(self):
        """Switch to the home landing page."""
        self.home_btn.hide()
        self.machine_selector_btn.hide()
        self.module_switch.hide()
        self.help_btn.hide()
        self.optimize_btn.hide()
        self.export_btn.hide()
        if hasattr(self, 'home_page'):
            self.main_stack.setCurrentWidget(self.home_page)
            
    def _show_optimizer(self):
        """Switch to the Optimizer module (Programming)."""
        self.home_btn.show()
        self.machine_selector_btn.hide()
        self.module_switch.hide()
        self.help_btn.show()
        self.optimize_btn.show()
        self.export_btn.show()
        self.main_stack.setCurrentWidget(self.optimizer_page)
        
    def _show_slicer(self):
        """Switch to the Slicer Setup or Slicer View module (Manufacturing)."""
        self.home_btn.show()
        # Only show the module switch when in Slicer (Manufacturing) mode
        self.module_switch.show()
        self.module_switch.set_active('manufacturing')
        self.help_btn.show()
        self.optimize_btn.hide()
        self.export_btn.hide()
        
        if self.current_machine_name and hasattr(self, 'slice_page'):
            self.machine_selector_btn.show()
            self._update_machine_menu()
            self.main_stack.setCurrentWidget(self.slice_page)
        elif hasattr(self, 'slicer_setup_page'):
            self.machine_selector_btn.hide()
            self.slicer_setup_page.refresh_profiles()
            self.main_stack.setCurrentWidget(self.slicer_setup_page)

    def _update_machine_menu(self):
        """Update and assign the dropdown menu for machine selection."""
        from PyQt6.QtWidgets import QMenu
        from src.profiles.profile_manager import ProfileManager
        
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {Theme.BG_SECONDARY};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 4px;
            }}
            QMenu::item {{
                padding: 8px 24px 8px 12px;
            }}
            QMenu::item:selected {{
                background-color: {Theme.BG_ELEVATED};
            }}
        """)
        
        pm = ProfileManager()
        
        def switch_machine(name, profile):
            self.current_machine_name = name
            self.machine_selector_btn.setText(f"{name} ▼")
            if hasattr(self, 'slice_page'):
                bed = profile.get('bed_dimensions', {'x': 300, 'y': 300, 'z': 400})
                self.slice_page.set_machine_dimensions(bed['x'], bed['y'], bed['z'])
                
        for profile in pm.load_machines():
            name = profile.get('name', 'Unknown')
            action = menu.addAction(name)
            action.triggered.connect(lambda checked, n=name, p=profile: switch_machine(n, p))
            
        menu.addSeparator()
        
        customize_action = menu.addAction("Customize...")
        customize_action.triggered.connect(self._show_machine_setup)
        
        self.machine_selector_btn.setMenu(menu)

    def _show_machine_setup(self):
        """Force show the machine selection page."""
        if hasattr(self, 'slicer_setup_page'):
            self.machine_selector_btn.hide()
            self.slicer_setup_page.refresh_profiles()
            self.main_stack.setCurrentWidget(self.slicer_setup_page)

    def _show_slicer_3d(self, w: float, d: float, h: float):
        """Switch to the actual 3D Slicer view after selecting a machine."""
        if hasattr(self, 'slicer_setup_page'):
            self.current_machine_name = self.slicer_setup_page.machine_combo.currentText()
            self.machine_selector_btn.setText(f"{self.current_machine_name} ▼")
            
        self.machine_selector_btn.show()
        self._update_machine_menu()
        if hasattr(self, 'slice_page'):
            self.slice_page.set_machine_dimensions(w, d, h)
            self.main_stack.setCurrentWidget(self.slice_page)
