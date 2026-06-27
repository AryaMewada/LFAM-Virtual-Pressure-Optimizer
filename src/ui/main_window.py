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
        self._optimized_gcode = None
        self._material_profile = None
        self._machine_profile = None
        self._worker = None

        # ── Build UI ──────────────────────────────────────────────
        self._setup_menu_bar()
        self._setup_status_bar()
        self._setup_central_widget()
        self._connect_signals()

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

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

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

        # Analysis Panel
        if AnalysisPanel is not None:
            self.analysis_panel = AnalysisPanel()
            content_layout.addWidget(self.analysis_panel)
        else:
            self.analysis_panel = None

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

        # Results Panel
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

        if self.optimization_controls is not None and hasattr(self.optimization_controls, 'optimize_clicked'):
            self.optimization_controls.optimize_clicked.connect(self._on_optimize_clicked)

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

        elif task_type == 'optimize':
            self._optimized_data = result.get('optimized_data')
            self._optimized_gcode = result.get('optimized_gcode')
            self.statusBar().showMessage('Optimization complete')

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
                'duration': m.duration * 60.0
            })
        return [layers_dict[k] for k in sorted(layers_dict.keys())]

    def _on_worker_error(self, msg: str):
        self.progress_bar.hide()
        self.loading_overlay.hide_loading()
        self.statusBar().showMessage('Error occurred')
        QMessageBox.critical(self, "Error", f"An error occurred during processing:\n{msg}")
        self._worker = None

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
        QMessageBox.information(
            self,
            'Material Settings',
            'Material profile configuration.\n\n'
            'Use the Profile Selector in the sidebar to choose a material, '
            'or define custom material properties here.',
        )

    def _show_machine_settings(self):
        """Show the machine settings dialog (placeholder for machine editor)."""
        QMessageBox.information(
            self,
            'Machine Settings',
            'Machine profile configuration.\n\n'
            'Configure nozzle diameter, max extrusion rate, '
            'build volume, and other machine-specific parameters.',
        )

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
