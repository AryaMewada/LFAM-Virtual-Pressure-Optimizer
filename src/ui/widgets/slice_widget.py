from PyQt6.QtCore import Qt, pyqtSignal

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame, QPushButton, QSpacerItem, 
    QSizePolicy, QFileDialog, QDialog, QFormLayout, QLineEdit, QDialogButtonBox
)

from src.ui.theme import Theme

import pyqtgraph
import pyqtgraph.opengl as gl
import numpy as np
from stl import mesh

def make_ring_verts(radius, segments=32):
    angles = np.linspace(0, 2*np.pi, segments+1)
    x = radius * np.cos(angles)
    y = radius * np.sin(angles)
    z = np.zeros_like(angles)
    return np.column_stack([x, y, z])

class MachineSettingsDialog(QDialog):
    def __init__(self, parent=None, current_w=400, current_d=400, current_h=400, nozzle_d=5.0):
        super().__init__(parent)
        self.setWindowTitle("Machine Settings")
        self.setStyleSheet(f"background-color: {Theme.BG_SECONDARY}; color: {Theme.TEXT_PRIMARY};")
        
        layout = QFormLayout(self)
        
        self.w_input = QLineEdit(str(current_w))
        self.d_input = QLineEdit(str(current_d))
        self.h_input = QLineEdit(str(current_h))
        self.nozzle_input = QLineEdit(str(nozzle_d))
        
        for inp in [self.w_input, self.d_input, self.h_input, self.nozzle_input]:
            inp.setStyleSheet(f"background-color: {Theme.BG_TERTIARY}; border: 1px solid {Theme.BORDER}; padding: 4px;")
            
        layout.addRow("Bed Width (mm):", self.w_input)
        layout.addRow("Bed Depth (mm):", self.d_input)
        layout.addRow("Max Height (mm):", self.h_input)
        layout.addRow("Nozzle Diameter (mm):", self.nozzle_input)
        
        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)
        
    def get_settings(self):
        try:
            return float(self.w_input.text()), float(self.d_input.text()), float(self.h_input.text()), float(self.nozzle_input.text())
        except ValueError:
            return 400.0, 400.0, 400.0, 5.0

class SceneGraphItem(QWidget):
    def __init__(self, name, model, canvas, parent=None):
        super().__init__(parent)
        self.model = model
        self.canvas = canvas
        self.setFixedHeight(36)
        self.setMinimumHeight(36)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        
        from src.ui.theme import Theme
        self.name_lbl = QLabel(name)
        self.name_lbl.setStyleSheet(f"color: {Theme.TEXT_PRIMARY};")
        
        from PyQt6.QtWidgets import QSizePolicy
        self.name_lbl.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        
        layout.addWidget(self.name_lbl, stretch=1)
        
        self.hide_btn = QPushButton("Hide")
        self.hide_btn.setFixedSize(40, 24)
        self.hide_btn.setCheckable(True)
        self.hide_btn.clicked.connect(self._toggle_hide)
        layout.addWidget(self.hide_btn)
        
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.setFixedSize(50, 24)
        self.reset_btn.clicked.connect(self._reset)
        layout.addWidget(self.reset_btn)
        self.set_selected(False)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.canvas.select_model(self.model)

    def set_selected(self, selected: bool):
        from src.ui.theme import Theme
        bg_color = Theme.ACCENT_PRIMARY if selected else Theme.BG_TERTIARY
        self.setStyleSheet(f"""
            SceneGraphItem {{
                background-color: {bg_color};
                border-radius: 4px;
            }}
            SceneGraphItem:hover {{
                background-color: {Theme.BG_ELEVATED};
            }}
            QPushButton {{
                background: transparent;
                border: 1px solid {Theme.BORDER};
                border-radius: 3px;
            }}
            QPushButton:hover {{
                background: {Theme.BG_ELEVATED};
            }}
        """)

    def _toggle_hide(self):
        self.model.setVisible(not self.hide_btn.isChecked())
        self.canvas.update()

    def _reset(self):
        self.model.pos = np.array([self.canvas.opts["center"].x(), self.canvas.opts["center"].y(), self.model.pos[2]])
        import PyQt6.QtGui as QtGui
        self.model.rot_matrix = QtGui.QMatrix4x4()
        self.model.scale_vec = [1.0, 1.0, 1.0]
        self.canvas.apply_transform(self.model)
        self.canvas.update()

    def paintEvent(self, pe):
        from PyQt6.QtWidgets import QStyleOption, QStyle
        from PyQt6.QtGui import QPainter
        o = QStyleOption()
        o.initFrom(self)
        p = QPainter(self)
        self.style().drawPrimitive(QStyle.PrimitiveElement.PE_Widget, o, p, self)


def make_arrow_verts(axis, length=50, tip_len=10, tip_w=4):
    import numpy as np
    lines = []
    lines.extend([[0,0,0], [length,0,0]])
    lines.extend([[length,0,0], [length-tip_len, tip_w, 0]])
    lines.extend([[length,0,0], [length-tip_len, -tip_w, 0]])
    lines.extend([[length,0,0], [length-tip_len, 0, tip_w]])
    lines.extend([[length,0,0], [length-tip_len, 0, -tip_w]])
    verts = np.array(lines)
    if axis == 'y': verts = verts[:, [1, 0, 2]]
    elif axis == 'z': verts = verts[:, [2, 1, 0]]
    return verts

class TransformGizmo:
    """3D Transform Gizmo with X, Y, Z axes for translate, rotate, scale."""
    def __init__(self, view):
        self.view = view
        self.mode = 'none'
        
        self.t_axes = {
            'x': gl.GLLinePlotItem(pos=make_arrow_verts('x', 50), color=(1,0,0,1), width=1, antialias=True, mode='lines'),
            'y': gl.GLLinePlotItem(pos=make_arrow_verts('y', 50), color=(0,1,0,1), width=1, antialias=True, mode='lines'),
            'z': gl.GLLinePlotItem(pos=make_arrow_verts('z', 50), color=(0,0,1,1), width=1, antialias=True, mode='lines')
        }
        
        self.s_axes = {
            'x': gl.GLLinePlotItem(pos=np.array([[0,0,0],[50,0,0]]), color=(1,0.5,0.5,1), width=1, antialias=True, mode='lines'),
            'y': gl.GLLinePlotItem(pos=np.array([[0,0,0],[0,50,0]]), color=(0.5,1,0.5,1), width=1, antialias=True, mode='lines'),
            'z': gl.GLLinePlotItem(pos=np.array([[0,0,0],[0,0,50]]), color=(0.5,0.5,1,1), width=1, antialias=True, mode='lines')
        }
        
        r_verts = make_ring_verts(50.0)
        x_ring = r_verts.copy(); x_ring[:, [0, 2]] = x_ring[:, [2, 0]]
        y_ring = r_verts.copy(); y_ring[:, [1, 2]] = y_ring[:, [2, 1]]
        z_ring = r_verts.copy()
        
        self.r_rings = {
            'x': gl.GLLinePlotItem(pos=x_ring, color=(1,0,0,1), width=1, antialias=True, mode='line_strip'),
            'y': gl.GLLinePlotItem(pos=y_ring, color=(0,1,0,1), width=1, antialias=True, mode='line_strip'),
            'z': gl.GLLinePlotItem(pos=z_ring, color=(0,0,1,1), width=1, antialias=True, mode='line_strip')
        }
        
        self.all_items = []
        import OpenGL.GL as ogl
        for d in [self.t_axes, self.s_axes, self.r_rings]:
            for item in d.values():
                item.setDepthValue(10)
                item.setGLOptions({
                    ogl.GL_DEPTH_TEST: False,
                    ogl.GL_BLEND: True,
                    'glBlendFunc': (ogl.GL_SRC_ALPHA, ogl.GL_ONE_MINUS_SRC_ALPHA)
                })
                self.view.addItem(item)
                self.all_items.append(item)
                
        self.set_mode('none')
        self.pos = np.array([0.0, 0.0, 0.0])
        self.size = 50.0

    def set_mode(self, mode):
        self.mode = mode
        
        # Remove all items from view
        for item in self.all_items:
            try:
                self.view.removeItem(item)
            except ValueError:
                pass # Already removed
                
        if mode == 'translate':
            for item in self.t_axes.values(): self.view.addItem(item)
        elif mode == 'scale':
            for item in self.s_axes.values(): self.view.addItem(item)
        elif mode == 'rotate':
            for item in self.r_rings.values(): self.view.addItem(item)
            
    def show(self):
        self.set_mode(self.mode)
        
    def hide(self):
        for item in self.all_items:
            try:
                self.view.removeItem(item)
            except ValueError:
                pass

    def update_position(self, pos, rot_matrix=None):
        self.pos = pos
        for item in self.all_items:
            item.resetTransform()
            item.translate(pos[0], pos[1], pos[2])
            if rot_matrix is not None:
                item.setTransform(item.transform() * rot_matrix)

    def highlight(self, axis):
        colors = {
            'x': (1,0,0,1), 'y': (0,1,0,1), 'z': (0,0,1,1)
        }
        h_color = (1,1,0,1)
        
        if self.mode == 'translate':
            for k, item in self.t_axes.items():
                item.setData(color=h_color if k == axis else colors[k])
        elif self.mode == 'scale':
            for k, item in self.s_axes.items():
                c = colors[k]
                sc = (c[0]*0.5+0.5, c[1]*0.5+0.5, c[2]*0.5+0.5, 1)
                item.setData(color=h_color if k == axis else sc)
        elif self.mode == 'rotate':
            for k, item in self.r_rings.items():
                item.setData(color=h_color if k == axis else colors[k])


class SliceWidget(QWidget):
    """
    Slicer module with a 3-column layout, collapsible left sidebar, vertical toolbar,
    and a fully interactive hardware-accelerated 3D OpenGL viewport for model viewing.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {Theme.BG_PRIMARY};
            }}
        """)
        
        # Main horizontal layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # ==========================================
        # 1. Left Section (Tools/Settings)
        # ==========================================
        self.left_sidebar = QFrame()
        self.left_sidebar.setFixedWidth(320)
        self.left_sidebar.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_SECONDARY};
                border-right: 1px solid {Theme.BORDER};
            }}
        """)
        left_layout = QVBoxLayout(self.left_sidebar)
        left_layout.setContentsMargins(12, 12, 12, 12)
        
        # Header with Title and Toggle Button
        left_header_layout = QHBoxLayout()
        left_title = QLabel("Slice Settings")
        left_title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-weight: bold; font-size: 16px; border: none;")
        left_header_layout.addWidget(left_title)
        
        left_header_layout.addStretch()
        
        self.collapse_btn = QPushButton("◀")
        self.collapse_btn.setFixedSize(28, 28)
        self.collapse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.collapse_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.BG_TERTIARY};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {Theme.BG_ELEVATED};
            }}
        """)
        self.collapse_btn.clicked.connect(self.collapse_sidebar)
        left_header_layout.addWidget(self.collapse_btn)
        
        left_layout.addLayout(left_header_layout)
        
        # Tools Group
        from PyQt6.QtWidgets import QGroupBox, QScrollArea, QWidget
        
        # Object List
        self.sg_group = QGroupBox("Objects")
        self.sg_group.setFixedHeight(180)
        sg_group_layout = QVBoxLayout(self.sg_group)
        
        self.scene_graph_area = QScrollArea()
        self.scene_graph_area.setWidgetResizable(True)
        self.scene_graph_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.sg_content = QWidget()
        self.sg_content.setObjectName("sg_content")
        self.sg_content.setStyleSheet("QWidget#sg_content { background: transparent; }")
        
        self.sg_layout = QVBoxLayout(self.sg_content)
        self.sg_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.sg_layout.setContentsMargins(0, 0, 0, 0)
        
        self.scene_graph_area.setWidget(self.sg_content)
        sg_group_layout.addWidget(self.scene_graph_area)
        
        left_layout.addWidget(self.sg_group)
        
        # Layer Settings
        self.settings_group = QGroupBox("Layer Settings")
        settings_layout = QVBoxLayout(self.settings_group)
        
        # Layer Height
        lh_layout = QHBoxLayout()
        lh_layout.addWidget(QLabel("Layer Height (mm):"))
        self.input_layer_height = QLineEdit("0.2")
        self.input_layer_height.setFixedWidth(60)
        self.input_layer_height.setStyleSheet(f"background-color: {Theme.BG_TERTIARY}; color: {Theme.TEXT_PRIMARY}; border: 1px solid {Theme.BORDER}; padding: 4px;")
        lh_layout.addWidget(self.input_layer_height)
        settings_layout.addLayout(lh_layout)
        
        # Initial Layer Height
        ilh_layout = QHBoxLayout()
        ilh_layout.addWidget(QLabel("Initial Height (mm):"))
        self.input_initial_height = QLineEdit("0.2")
        self.input_initial_height.setFixedWidth(60)
        self.input_initial_height.setStyleSheet(f"background-color: {Theme.BG_TERTIARY}; color: {Theme.TEXT_PRIMARY}; border: 1px solid {Theme.BORDER}; padding: 4px;")
        ilh_layout.addWidget(self.input_initial_height)
        settings_layout.addLayout(ilh_layout)
        
        # Extrusion Width
        ew_layout = QHBoxLayout()
        ew_layout.addWidget(QLabel("Extrusion Width (mm):"))
        self.input_extrusion_width = QLineEdit("0.6")
        self.input_extrusion_width.setFixedWidth(60)
        self.input_extrusion_width.setStyleSheet(f"background-color: {Theme.BG_TERTIARY}; color: {Theme.TEXT_PRIMARY}; border: 1px solid {Theme.BORDER}; padding: 4px;")
        ew_layout.addWidget(self.input_extrusion_width)
        settings_layout.addLayout(ew_layout)
        
        # Wall Count
        wc_layout = QHBoxLayout()
        wc_layout.addWidget(QLabel("Wall Count:"))
        self.input_wall_count = QLineEdit("2")
        self.input_wall_count.setFixedWidth(60)
        self.input_wall_count.setStyleSheet(f"background-color: {Theme.BG_TERTIARY}; color: {Theme.TEXT_PRIMARY}; border: 1px solid {Theme.BORDER}; padding: 4px;")
        wc_layout.addWidget(self.input_wall_count)
        settings_layout.addLayout(wc_layout)
        
        left_layout.addWidget(self.settings_group)
        
        left_layout.addStretch()
        
        # Slice Button
        self.btn_slice = QPushButton("Slice")
        self.btn_slice.setFixedHeight(40)
        self.btn_slice.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.ACCENT_PRIMARY};
                color: {Theme.TEXT_PRIMARY};
                font-weight: bold;
                font-size: 16px;
                border: none;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: #2563eb;
            }}
        """)
        self.btn_slice.clicked.connect(self._on_slice_clicked)
        left_layout.addWidget(self.btn_slice)
        
        # Slicer Status Label
        self.slice_status = QLabel("")
        self.slice_status.setWordWrap(True)
        self.slice_status.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 12px; margin-top: 5px;")
        left_layout.addWidget(self.slice_status)
        
        # ==========================================
        # 2. Center Section (Toolbar + 3D Model Viewer)
        # ==========================================
        self.center_view = QFrame()
        self.center_view.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_PRIMARY};
                border: none;
            }}
        """)
        center_layout = QHBoxLayout(self.center_view)
        center_layout.setContentsMargins(10, 10, 10, 10)
        center_layout.setSpacing(10)
        
        # Main Viewer Area (Custom OpenGL Canvas)
        self.gl_viewer = SlicerCanvas3D()
        self.gl_viewer.slice_widget = self
        self.gl_viewer.setBackgroundColor(Theme.BG_PRIMARY)
        center_layout.addWidget(self.gl_viewer, stretch=1)

        # Perspective Toggle (P)
        self.btn_ortho = QPushButton("P", self.gl_viewer)
        self.btn_ortho.setFixedSize(30, 30)
        self.btn_ortho.setCheckable(True)
        self.btn_ortho.setToolTip("Toggle Orthographic / Perspective")
        self.btn_ortho.setStyleSheet("""
            QPushButton { background: #333333; color: white; border: 1px solid #555; border-radius: 15px; font-weight: bold; }
            QPushButton:checked { background: #0078D7; }
        """)
        self.btn_ortho.clicked.connect(self._toggle_ortho)
        

        
        # Navigation Cube (2D Unfolded)
        self.nav_overlay = QWidget(self.gl_viewer)
        self.nav_overlay.setStyleSheet("""
            QPushButton { background: #333333; color: white; border: 1px solid #555; font-size: 10px; border-radius: 2px; }
            QPushButton:hover { background: #555555; }
        """)
        from PyQt6.QtWidgets import QGridLayout
        nav_layout = QGridLayout(self.nav_overlay)
        nav_layout.setContentsMargins(0,0,0,0)
        nav_layout.setSpacing(2)
        
        btn_top = QPushButton("Top"); btn_top.setFixedSize(30, 30)
        btn_bottom = QPushButton("Bot"); btn_bottom.setFixedSize(30, 30)
        btn_left = QPushButton("L"); btn_left.setFixedSize(30, 30)
        btn_right = QPushButton("R"); btn_right.setFixedSize(30, 30)
        btn_front = QPushButton("F"); btn_front.setFixedSize(30, 30)
        btn_back = QPushButton("B"); btn_back.setFixedSize(30, 30)
        
        nav_layout.addWidget(btn_top, 0, 1)
        nav_layout.addWidget(btn_left, 1, 0)
        nav_layout.addWidget(btn_front, 1, 1)
        nav_layout.addWidget(btn_right, 1, 2)
        nav_layout.addWidget(btn_back, 1, 3)
        nav_layout.addWidget(btn_bottom, 2, 1)
        self.nav_overlay.resize(self.nav_overlay.sizeHint())
        
        btn_top.clicked.connect(lambda: self.gl_viewer.snap_camera('Top'))
        btn_bottom.clicked.connect(lambda: self.gl_viewer.snap_camera('Bottom'))
        btn_front.clicked.connect(lambda: self.gl_viewer.snap_camera('Front'))
        btn_back.clicked.connect(lambda: self.gl_viewer.snap_camera('Back'))
        btn_left.clicked.connect(lambda: self.gl_viewer.snap_camera('Left'))
        btn_right.clicked.connect(lambda: self.gl_viewer.snap_camera('Right'))

        # Bind resize event to keep overlays in corners
        original_resize = self.gl_viewer.resizeEvent
        def new_resize(ev):
            original_resize(ev)
            w, h = ev.size().width(), ev.size().height()
            self.btn_ortho.move(w - 40, 10)
            self.nav_overlay.move(w - self.nav_overlay.width() - 10, h - self.nav_overlay.height() - 10)
        self.gl_viewer.resizeEvent = new_resize

        # Vertical Toolbar Overlay Layout
        self.toolbar_container = QWidget(self.gl_viewer)
        self.toolbar_container.setStyleSheet("background: transparent;")
        toolbar_layout = QVBoxLayout(self.toolbar_container)
        toolbar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        toolbar_layout.setContentsMargins(10, 10, 10, 10)
        
        # Expand Button (Appears when sidebar is hidden)
        self.expand_btn = QPushButton("▶")
        self.expand_btn.setFixedSize(50, 50)
        self.expand_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.expand_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.BG_TERTIARY};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 8px;
                font-weight: bold;
                font-size: 20px;
                margin-bottom: 10px;
            }}
            QPushButton:hover {{
                background-color: {Theme.BG_ELEVATED};
            }}
        """)
        self.expand_btn.clicked.connect(self.expand_sidebar)
        self.expand_btn.hide()
        toolbar_layout.addWidget(self.expand_btn)
        
        # Machine Settings Button
        self.settings_btn = QPushButton("⚙")
        self.settings_btn.setFixedSize(50, 50)
        self.settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.settings_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.BG_TERTIARY};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 8px;
                font-weight: bold;
                font-size: 20px;
                margin-bottom: 10px;
            }}
            QPushButton:hover {{ background-color: {Theme.BG_ELEVATED}; }}
        """)
        self.settings_btn.clicked.connect(self._open_machine_settings)
        toolbar_layout.addWidget(self.settings_btn)
        self.toolbar_btns = []
        
        # Button 1: Import
        btn_import = QPushButton("1")
        btn_import.setToolTip("Import STL")
        btn_import.clicked.connect(self._on_import_clicked)
        self._style_toolbar_btn(btn_import)
        toolbar_layout.addWidget(btn_import)
        self.toolbar_btns.append(btn_import)
        
        # Partition Line
        part_line = QFrame()
        part_line.setFrameShape(QFrame.Shape.HLine)
        part_line.setFixedHeight(2)
        part_line.setStyleSheet(f"background-color: {Theme.BORDER}; margin-bottom: 5px;")
        toolbar_layout.addWidget(part_line)
        
        # Button 2, 3, 4: Transform, Rotate, Scale
        btn_labels = ["2", "3", "4", "5", "6", "7", "8"]
        for lbl in btn_labels:
            btn = QPushButton(lbl)
            self._style_toolbar_btn(btn)
            if lbl == "2":
                btn.setToolTip("Translate (Transform)")
                btn.clicked.connect(lambda: self.gl_viewer.set_interaction_mode('translate'))
            elif lbl == "3":
                btn.setToolTip("Rotate")
                btn.clicked.connect(lambda: self.gl_viewer.set_interaction_mode('rotate'))
            elif lbl == "4":
                btn.setToolTip("Scale")
                btn.clicked.connect(lambda: self.gl_viewer.set_interaction_mode('scale'))
            
            toolbar_layout.addWidget(btn)
            self.toolbar_btns.append(btn)
            
        # Resize container so it wraps the buttons properly initially
        self.toolbar_container.adjustSize()
        
        # ==========================================
        # 3. Right Section (Properties)
        # ==========================================
        self.right_sidebar = QFrame()
        self.right_sidebar.setFixedWidth(320)
        self.right_sidebar.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_SECONDARY};
                border-left: 1px solid {Theme.BORDER};
            }}
        """)
        right_layout = QVBoxLayout(self.right_sidebar)
        right_layout.setContentsMargins(12, 12, 12, 12)
        right_title = QLabel("Properties")
        right_title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-weight: bold; font-size: 16px; border: none;")
        right_layout.addWidget(right_title)
        
        # Container for properties
        self.props_container = QWidget()
        self.props_layout = QVBoxLayout(self.props_container)
        self.props_layout.setContentsMargins(0, 10, 0, 0)
        
        self.props_container.setStyleSheet(f"""
            QGroupBox {{ color: {Theme.TEXT_SECONDARY}; font-weight: bold; border: 1px solid {Theme.BORDER}; border-radius: 4px; margin-top: 10px; padding-top: 15px; }}
            QGroupBox::title {{ subcontrol-origin: margin; left: 10px; top: 0px; }}
            QLineEdit {{ background-color: {Theme.BG_TERTIARY}; color: {Theme.TEXT_PRIMARY}; border: 1px solid {Theme.BORDER}; border-radius: 4px; padding: 4px; }}
            QLabel {{ color: {Theme.TEXT_PRIMARY}; border: none; }}
        """)
        
        # Position
        pos_group = QGroupBox("Position (mm)")
        pos_layout = QHBoxLayout(pos_group)
        self.pos_x = QLineEdit(); self.pos_y = QLineEdit(); self.pos_z = QLineEdit()
        pos_layout.addWidget(QLabel("X:")); pos_layout.addWidget(self.pos_x)
        pos_layout.addWidget(QLabel("Y:")); pos_layout.addWidget(self.pos_y)
        pos_layout.addWidget(QLabel("Z:")); pos_layout.addWidget(self.pos_z)
        self.props_layout.addWidget(pos_group)
        
        # Rotation
        rot_group = QGroupBox("Rotation (°)")
        rot_layout = QHBoxLayout(rot_group)
        self.rot_x = QLineEdit(); self.rot_y = QLineEdit(); self.rot_z = QLineEdit()
        rot_layout.addWidget(QLabel("X:")); rot_layout.addWidget(self.rot_x)
        rot_layout.addWidget(QLabel("Y:")); rot_layout.addWidget(self.rot_y)
        rot_layout.addWidget(QLabel("Z:")); rot_layout.addWidget(self.rot_z)
        self.props_layout.addWidget(rot_group)
        
        # Scale
        scale_group = QGroupBox("Scale (%)")
        scale_layout = QHBoxLayout(scale_group)
        self.scale_x = QLineEdit(); self.scale_y = QLineEdit(); self.scale_z = QLineEdit()
        self.btn_scale_lock = QPushButton("🔒")
        self.btn_scale_lock.setCheckable(True)
        self.btn_scale_lock.setChecked(True)
        self.btn_scale_lock.setFixedWidth(28)
        self.btn_scale_lock.setStyleSheet(f"background-color: {Theme.BG_TERTIARY}; color: {Theme.TEXT_PRIMARY}; border: 1px solid {Theme.BORDER}; padding: 2px; font-size: 14px;")
        scale_layout.addWidget(QLabel("X:")); scale_layout.addWidget(self.scale_x)
        scale_layout.addWidget(QLabel("Y:")); scale_layout.addWidget(self.scale_y)
        scale_layout.addWidget(QLabel("Z:")); scale_layout.addWidget(self.scale_z)
        scale_layout.addWidget(self.btn_scale_lock)
        self.props_layout.addWidget(scale_group)
        
        # Dimensions
        dim_group = QGroupBox("Dimensions (mm)")
        dim_layout = QVBoxLayout(dim_group)
        self.dim_label = QLabel("-")
        dim_layout.addWidget(self.dim_label)
        self.props_layout.addWidget(dim_group)
        
        # Quick Actions
        action_group = QGroupBox("Quick Actions")
        action_layout = QHBoxLayout(action_group)
        self.btn_center = QPushButton("To Centre")
        self.btn_center.setStyleSheet(f"background-color: {Theme.BG_TERTIARY}; color: {Theme.TEXT_PRIMARY}; border: 1px solid {Theme.BORDER}; padding: 5px;")
        self.btn_lay_flat = QPushButton("Lay Flat")
        self.btn_lay_flat.setStyleSheet(f"background-color: {Theme.BG_TERTIARY}; color: {Theme.TEXT_PRIMARY}; border: 1px solid {Theme.BORDER}; padding: 5px;")
        action_layout.addWidget(self.btn_center)
        action_layout.addWidget(self.btn_lay_flat)
        self.props_layout.addWidget(action_group)
        
        self.btn_center.clicked.connect(self._center_selected)
        self.btn_lay_flat.clicked.connect(self._lay_flat_selected)
        self.btn_scale_lock.toggled.connect(self._on_scale_lock_toggled)
        
        self.props_container.hide()
        right_layout.addWidget(self.props_container)
        
        right_layout.addStretch()
        
        # Connect signals
        for le in [self.pos_x, self.pos_y, self.pos_z, self.rot_x, self.rot_y, self.rot_z, self.scale_x, self.scale_y, self.scale_z]:
            le.editingFinished.connect(self._on_properties_edited)
        
        # Add all to main layout
        layout.addWidget(self.left_sidebar)
        layout.addWidget(self.center_view, stretch=1)
        layout.addWidget(self.right_sidebar)

    def update_properties_panel(self, model):
        import numpy as np
        if not model:
            self.props_container.hide()
            return
            
        self.props_container.show()
        self._blocking_props = True
        
        pos = model.pos
        self.pos_x.setText(f"{pos[0]:.2f}")
        self.pos_y.setText(f"{pos[1]:.2f}")
        self.pos_z.setText(f"{pos[2]:.2f}")
        
        rot = getattr(model, 'rot_angles', [0.0, 0.0, 0.0])
        self.rot_x.setText(f"{rot[0]:.1f}")
        self.rot_y.setText(f"{rot[1]:.1f}")
        self.rot_z.setText(f"{rot[2]:.1f}")
        
        scale = getattr(model, 'scale_vec', [1,1,1])
        self.scale_x.setText(f"{scale[0]*100:.1f}")
        self.scale_y.setText(f"{scale[1]*100:.1f}")
        self.scale_z.setText(f"{scale[2]*100:.1f}")
        
        if hasattr(model, 'raw_vertices'):
            verts = model.raw_vertices
            scaled_verts = verts * scale
            min_b = scaled_verts.min(axis=0)
            max_b = scaled_verts.max(axis=0)
            dims = max_b - min_b
            self.dim_label.setText(f"X: {dims[0]:.1f}  Y: {dims[1]:.1f}  Z: {dims[2]:.1f}")
            
        self._blocking_props = False
        
    def _on_scale_lock_toggled(self, checked):
        if checked:
            self.btn_scale_lock.setText("🔒")
        else:
            self.btn_scale_lock.setText("🔓")
        
    def _on_properties_edited(self):
        import numpy as np
        import PyQt6.QtGui as QtGui
        if getattr(self, '_blocking_props', False) or not self.gl_viewer.selected_model: return
        try:
            model = self.gl_viewer.selected_model
            model.pos = np.array([
                float(self.pos_x.text()),
                float(self.pos_y.text()),
                float(self.pos_z.text())
            ])
            
            # Rotation
            model.rot_angles = [
                float(self.rot_x.text()),
                float(self.rot_y.text()),
                float(self.rot_z.text())
            ]
            new_rot = QtGui.QMatrix4x4()
            new_rot.rotate(model.rot_angles[0], 1, 0, 0)
            new_rot.rotate(model.rot_angles[1], 0, 1, 0)
            new_rot.rotate(model.rot_angles[2], 0, 0, 1)
            model.rot_matrix = new_rot
            
            # Scale
            new_scale = [
                float(self.scale_x.text())/100.0,
                float(self.scale_y.text())/100.0,
                float(self.scale_z.text())/100.0
            ]
            
            # Proportional scaling logic based on which field was edited
            if self.btn_scale_lock.isChecked():
                # See which axis changed relative to the model's current scale
                old_scale = getattr(model, 'scale_vec', [1,1,1])
                ratio = 1.0
                if abs(new_scale[0] - old_scale[0]) > 0.001: ratio = new_scale[0] / old_scale[0] if old_scale[0] != 0 else 1.0
                elif abs(new_scale[1] - old_scale[1]) > 0.001: ratio = new_scale[1] / old_scale[1] if old_scale[1] != 0 else 1.0
                elif abs(new_scale[2] - old_scale[2]) > 0.001: ratio = new_scale[2] / old_scale[2] if old_scale[2] != 0 else 1.0
                
                if ratio != 1.0:
                    new_scale = [old_scale[0] * ratio, old_scale[1] * ratio, old_scale[2] * ratio]
                    
            model.scale_vec = new_scale
            
            self.gl_viewer.model_center = model.pos.copy()
            self.gl_viewer.apply_transform(model)
            
            if self.gl_viewer.interaction_mode != 'none':
                self.gl_viewer.gizmo.update_position(self.gl_viewer.model_center, model.rot_matrix)
                
            self.gl_viewer.update()
            self.update_properties_panel(model)
        except ValueError:
            pass
            
    def _center_selected(self):
        model = self.gl_viewer.selected_model
        if not model: return
        model.pos[0] = 0.0
        model.pos[1] = 0.0
        self.gl_viewer.model_center = model.pos.copy()
        self.gl_viewer.apply_transform(model)
        if self.gl_viewer.interaction_mode != 'none':
            self.gl_viewer.gizmo.update_position(self.gl_viewer.model_center, model.rot_matrix)
        self.gl_viewer.update()
        self.update_properties_panel(model)
        
    def _lay_flat_selected(self):
        model = self.gl_viewer.selected_model
        if not model: return
        import numpy as np
        
        # We need to find the absolute minimum Z of the transformed vertices and move the model up by that amount
        verts = model.raw_vertices
        scale = getattr(model, 'scale_vec', [1,1,1])
        scaled_verts = verts * scale
        
        # Apply rotation
        import PyQt6.QtGui as QtGui
        rot_mat = getattr(model, 'rot_matrix', QtGui.QMatrix4x4())
        
        # Since PyQt6 QMatrix4x4 map doesn't accept full numpy arrays easily, we map bounding box?
        # No, a rotated object's lowest point could be any vertex.
        # Quick hack: we can just use the bounding box of the unrotated model? No, rotation changes Z-min.
        # We must transform all vertices to find true Z-min.
        min_z = float('inf')
        for v in scaled_verts:
            vec = QtGui.QVector3D(v[0], v[1], v[2])
            vec = rot_mat.map(vec)
            if vec.z() < min_z:
                min_z = vec.z()
                
        # The true world min Z is model.pos[2] + min_z
        # We want world min Z to be 0 -> model.pos[2] + min_z = 0 -> model.pos[2] = -min_z
        model.pos[2] = -min_z
        
        self.gl_viewer.model_center = model.pos.copy()
        self.gl_viewer.apply_transform(model)
        if self.gl_viewer.interaction_mode != 'none':
            self.gl_viewer.gizmo.update_position(self.gl_viewer.model_center, model.rot_matrix)
        self.gl_viewer.update()
        self.update_properties_panel(model)

    def _style_toolbar_btn(self, btn):
        btn.setFixedSize(50, 50)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.BG_TERTIARY};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 8px;
                font-weight: bold;
                font-size: 20px;
                margin-bottom: 5px;
            }}
            QPushButton:hover {{
                background-color: {Theme.BG_ELEVATED};
                border-color: {Theme.TEXT_MUTED};
            }}
        """)

    def collapse_sidebar(self):
        """Hide the left sidebar and show the expand button in the toolbar."""
        self.left_sidebar.hide()
        self.expand_btn.show()

    def expand_sidebar(self):
        """Show the left sidebar and hide the expand button in the toolbar."""
        self.left_sidebar.show()
        self.expand_btn.hide()

    def _open_machine_settings(self):
        dialog = MachineSettingsDialog(
            self,
            current_w=getattr(self.gl_viewer, 'machine_w', 400.0),
            current_d=getattr(self.gl_viewer, 'machine_d', 400.0),
            current_h=getattr(self.gl_viewer, 'machine_h', 400.0),
            nozzle_d=getattr(self, 'nozzle_diameter', 5.0)
        )
        if dialog.exec():
            w, d, h, nozzle = dialog.get_settings()
            self.nozzle_diameter = nozzle
            self.set_machine_dimensions(w, d, h)
            self.gl_viewer.update()

    def set_machine_dimensions(self, w: float, d: float, h: float):
        """Initializes the OpenGL viewer with a grid based on passed dimensions."""
        self.gl_viewer.machine_w = w
        self.gl_viewer.machine_d = d
        self.gl_viewer.machine_h = h
        
        # Clear existing grid if any
        items_to_remove = [item for item in self.gl_viewer.items if isinstance(item, (gl.GLGridItem, gl.GLBoxItem, gl.GLLinePlotItem))]
        for item in items_to_remove:
            self.gl_viewer.removeItem(item)
            
        grid = gl.GLGridItem()
        grid.setSize(x=w, y=d)
        grid.setSpacing(x=w/20, y=d/20)
        grid.translate(w/2, d/2, 0)
        self.gl_viewer.addItem(grid)        
        
        import PyQt6.QtGui as QtGui
        box = gl.GLBoxItem(size=QtGui.QVector3D(w, d, h), color=(1, 1, 1, 0.1))
        self.gl_viewer.addItem(box)
        
        cross_len = 10.0
        cross_data = np.array([
            [w/2 - cross_len, d/2, 0.1], [w/2 + cross_len, d/2, 0.1],
            [w/2, d/2 - cross_len, 0.1], [w/2, d/2 + cross_len, 0.1]
        ])
        crosshair = gl.GLLinePlotItem(pos=cross_data, color=(1, 0, 0, 0.8), mode='lines', width=3, antialias=True)
        crosshair.is_center_mark = True
        self.gl_viewer.addItem(crosshair)
        
        self.gl_viewer.opts['center'] = pyqtgraph.Vector(w/2, d/2, 0)
        self.gl_viewer.setCameraPosition(distance=max(w,d)*1.5, elevation=30, azimuth=-45)

    def _toggle_ortho(self, checked):
        self.gl_viewer.is_ortho = checked
        self.gl_viewer.update()

    def _on_import_clicked(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Import 3D Models",
            "",
            "STL Files (*.stl);;All Files (*)"
        )
        if file_paths:
            import os
            for file_path in file_paths:
                name = os.path.basename(file_path)
                self.gl_viewer._current_loading_name = name
                model = self.gl_viewer.load_stl(file_path)
                if model:
                    sg_item = SceneGraphItem(name, model, self.gl_viewer)
                    self.sg_layout.addWidget(sg_item)
                    sg_item.show()
            self.scene_graph_area.update()

        
    def _on_slice_clicked(self):
        import time
        import numpy as np
        import pyqtgraph.opengl as gl
        from src.slicer.engine import SlicerEngine
        
        models = getattr(self.gl_viewer, 'active_models', [])
        if not models:
            self.slice_status.setText("No models to slice.")
            return
            
        try:
            layer_height = float(self.input_layer_height.text())
            initial_height = float(self.input_initial_height.text())
            extrusion_width = float(self.input_extrusion_width.text())
            wall_count = int(self.input_wall_count.text())
        except ValueError:
            self.slice_status.setText("Invalid slice settings. Must be numbers.")
            return
            
        self.slice_status.setText("Slicing...")
        self.slice_status.repaint() # Force UI update before blocking thread
        
        # In a real app we'd use a QThread. For now, block and slice.
        engine = SlicerEngine(
            layer_height=layer_height, 
            initial_layer_height=initial_height,
            extrusion_width=extrusion_width,
            wall_count=wall_count
        )
        
        total_layers = 0
        t0 = time.time()
        
        all_lines = []
        
        for model in models:
            # Hide the 3D mesh (model is the GLMeshItem itself)
            if hasattr(model, 'setVisible'):
                model.setVisible(False)
                
            # Call slice_model on the engine
            result = engine.slice_model(
                model.raw_vertices,
                model.pos,
                model.rot_matrix,
                model.scale_vec
            )
            total_layers += len(result.layers)
            
            # Extract line segments from the sliced polygons
            for layer in result.layers:
                z = layer.z_height
                for poly in layer.perimeters:
                    pts = poly.points
                    num_pts = len(pts)
                    if num_pts < 2:
                        continue
                        
                    # Create 3D points
                    pts_3d = np.zeros((num_pts, 3))
                    pts_3d[:, :2] = pts
                    pts_3d[:, 2] = z
                    
                    # Create pairs for mode='lines': [p0, p1, p1, p2, p2, p3, ..., pN, p0]
                    idx0 = np.arange(num_pts)
                    idx1 = np.roll(idx0, -1)
                    
                    pairs = np.empty((num_pts * 2, 3))
                    pairs[0::2] = pts_3d[idx0]
                    pairs[1::2] = pts_3d[idx1]
                    
                    all_lines.append(pairs)
                    
        # Remove old preview if it exists
        if hasattr(self, 'slice_preview_item') and self.slice_preview_item:
            try:
                self.gl_viewer.removeItem(self.slice_preview_item)
            except ValueError:
                pass # Was already removed
            
        # Add new preview
        if all_lines:
            final_lines = np.vstack(all_lines)
            # Use neon green color #10b981
            self.slice_preview_item = gl.GLLinePlotItem(pos=final_lines, color=(0.063, 0.725, 0.506, 1.0), width=1.0, mode='lines', antialias=False)
            self.gl_viewer.addItem(self.slice_preview_item)
            
        t1 = time.time()
        
        self.slice_status.setText(f"Successfully sliced {total_layers} layers across {len(models)} models in {t1 - t0:.3f}s.")

class SlicerCanvas3D(gl.GLViewWidget):
    """Custom OpenGL Canvas for Slicer with specific gesture overrides and basic transform logic."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        from PyQt6.QtCore import Qt
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._last_mouse_pos = None
        self.interaction_mode = 'none' # 'none', 'translate', 'rotate', 'scale'
        self.active_models = []
        self.selected_model = None
        self.model_center = np.array([0.0, 0.0, 0.0])
        self.active_axis = None
        
        self.gizmo = TransformGizmo(self)
        
        # Default mouse tracking to get hover events for interaction
        self.setMouseTracking(True)

    def set_interaction_mode(self, mode: str):
        self.interaction_mode = mode
        if mode in ['translate', 'rotate', 'scale'] and self.selected_model:
            self.gizmo.set_mode(mode)
            rot = getattr(self.selected_model, 'rot_matrix', None)
            self.gizmo.update_position(self.model_center, rot)
        else:
            self.gizmo.set_mode('none')
            self.active_axis = None
        self.update()


    def apply_transform(self, model):
        model.resetTransform()
        model.translate(model.pos[0], model.pos[1], model.pos[2])
        if hasattr(model, "rot_matrix"):
            model.setTransform(model.transform() * model.rot_matrix)
        model.scale(model.scale_vec[0], model.scale_vec[1], model.scale_vec[2])
        
        # Collision Detection against machine bounds
        import numpy as np
        out_of_bounds = False
        if hasattr(self, 'machine_w') and hasattr(model, 'raw_vertices'):
            verts = model.raw_vertices * getattr(model, 'scale_vec', [1,1,1])
            import PyQt6.QtGui as QtGui
            rot_mat = getattr(model, 'rot_matrix', None)
            
            if rot_mat is not None:
                # Extract 3x3 rotation from QMatrix4x4
                # data() returns a list of 16 floats in column-major order
                m = rot_mat.data()
                r = np.array([
                    [m[0], m[4], m[8]],
                    [m[1], m[5], m[9]],
                    [m[2], m[6], m[10]]
                ])
                verts = np.dot(verts, r.T)
                
            verts = verts + model.pos
            min_bounds = verts.min(axis=0)
            max_bounds = verts.max(axis=0)
            
            if min_bounds[0] < 0 or max_bounds[0] > self.machine_w or \
               min_bounds[1] < 0 or max_bounds[1] > self.machine_d or \
               min_bounds[2] < 0 or max_bounds[2] > self.machine_h:
                out_of_bounds = True
                
        if out_of_bounds:
            model.opts['color'] = (1.0, 0.2, 0.2, 0.8) # Red tint
        else:
            model.opts['color'] = (0.5, 0.7, 0.9, 1.0) # Normal blue
            
        if model == self.selected_model:
            self.update_selection_outline()

    def update_selection_outline(self):
        if hasattr(self, "selection_box"):
            self.selection_box.setVisible(False)
        for model in self.active_models:
            if model == self.selected_model:
                model.opts["drawEdges"] = True
                model.opts["edgeColor"] = (1.0, 1.0, 1.0, 1.0)
            else:
                model.opts["drawEdges"] = False
            model.update()

    def select_model(self, model):
        self.selected_model = model
        self.update_selection_outline()
        
        if model:
            self.model_center = model.pos.copy()
            rot = getattr(model, 'rot_matrix', None)
            self.gizmo.update_position(self.model_center, rot)
            
            if self.interaction_mode != "none":
                self.gizmo.set_mode(self.interaction_mode)
        else:
            self.gizmo.set_mode("none")
            
        if hasattr(self, "slice_widget") and hasattr(self.slice_widget, "sg_layout"):
            for i in range(self.slice_widget.sg_layout.count()):
                item = self.slice_widget.sg_layout.itemAt(i).widget()
                if item and hasattr(item, "set_selected"):
                    item.set_selected(item.model == model)

    def load_stl(self, filepath: str):
        """Loads an STL file and adds it to the viewport."""
        try:
            stl_mesh = mesh.Mesh.from_file(filepath)
            
            # Extract vertices and faces
            # numpy-stl stores 3 vertices per face in a flat array per face
            vertices = stl_mesh.vectors.reshape(-1, 3)
            # Create face indices
            faces = np.arange(len(vertices)).reshape(-1, 3)
            
            # Create GLMeshItem
            mesh_item = gl.GLMeshItem(
                vertexes=vertices,
                faces=faces,
                color=(0.5, 0.7, 0.9, 1.0),
                smooth=False,
                computeNormals=True,
                drawEdges=True,
                edgeColor=(0, 0, 0, 1)
            )
            
            # Request unlit flat look
            mesh_item.setGLOptions('opaque')
            
            self.addItem(mesh_item)
            self.active_models.append(mesh_item)
            self.selected_model = mesh_item
            
            min_bounds = vertices.min(axis=0)
            max_bounds = vertices.max(axis=0)
            local_center = (min_bounds + max_bounds) / 2.0
            
            # Shift vertices so origin is exactly at the geometric center
            vertices = vertices - local_center
            mesh_item.setMeshData(vertexes=vertices, faces=faces)
            
            # Spawn at the absolute center of the machine bed
            machine_w = getattr(self, 'machine_w', 400.0)
            machine_d = getattr(self, 'machine_d', 400.0)
            cx = machine_w / 2.0
            cy = machine_d / 2.0
            cz = 0.0
            
            height = max_bounds[2] - min_bounds[2]
            
            import PyQt6.QtGui as QtGui
            mesh_item.pos = np.array([cx, cy, cz + height/2.0])
            mesh_item.rot_angles = [0.0, 0.0, 0.0]
            mesh_item.rot_matrix = QtGui.QMatrix4x4()
            mesh_item.scale_vec = [1.0, 1.0, 1.0]
            mesh_item.raw_vertices = vertices
            mesh_item.raw_faces = faces
            mesh_item.file_name = getattr(self, '_current_loading_name', 'Model')
            
            self.model_center = mesh_item.pos.copy()
            self.apply_transform(mesh_item)
            
            if self.interaction_mode != 'none':
                self.gizmo.set_mode(self.interaction_mode)
                self.gizmo.update_position(self.model_center, mesh_item.rot_matrix)
                
            return mesh_item
            
        except Exception as e:
            print(f"Failed to load STL: {e}")

    def delete_model(self, model):
        if model in self.active_models:
            self.active_models.remove(model)
            self.removeItem(model)
            if self.selected_model == model:
                self.select_model(None)
            
            # Remove from UI list
            if hasattr(self, "slice_widget") and hasattr(self.slice_widget, "sg_layout"):
                for i in reversed(range(self.slice_widget.sg_layout.count())):
                    item = self.slice_widget.sg_layout.itemAt(i).widget()
                    if item and item.model == model:
                        item.setParent(None)
                        item.deleteLater()
            self.update()

    def duplicate_model(self, model_data):
        import numpy as np
        import pyqtgraph.opengl as gl
        import PyQt6.QtGui as QtGui
        
        mesh_item = gl.GLMeshItem(
            vertexes=model_data['raw_vertices'],
            faces=model_data['raw_faces'],
            color=(0.5, 0.7, 0.9, 1.0),
            smooth=False, computeNormals=True, drawEdges=True, edgeColor=(0, 0, 0, 1)
        )
        mesh_item.setGLOptions('opaque')
        
        self.addItem(mesh_item)
        self.active_models.append(mesh_item)
        
        mesh_item.raw_vertices = model_data['raw_vertices']
        mesh_item.raw_faces = model_data['raw_faces']
        mesh_item.pos = model_data['pos']
        mesh_item.rot_angles = model_data.get('rot_angles', [0.0, 0.0, 0.0]).copy()
        mesh_item.rot_matrix = QtGui.QMatrix4x4(model_data['rot'])
        mesh_item.scale_vec = list(model_data['scale'])
        mesh_item.file_name = model_data.get('name', 'Copy')
        
        # Add to UI list
        if hasattr(self, "slice_widget"):
            from src.ui.widgets.slice_widget import SceneGraphItem
            sg_item = SceneGraphItem(mesh_item.file_name, mesh_item, self)
            self.slice_widget.sg_layout.addWidget(sg_item)
            sg_item.show()
            self.slice_widget.scene_graph_area.update()
            
        self.select_model(mesh_item)
        self.set_interaction_mode('translate')
        self.apply_transform(mesh_item)
        self.update()
        
    def project_to_screen(self, pos3d):
        import PyQt6.QtGui as QtGui
        vec = QtGui.QVector3D(pos3d[0], pos3d[1], pos3d[2])
        view_mat = self.viewMatrix()
        proj_mat = self.projectionMatrix()
        vec = view_mat.map(vec)
        vec = proj_mat.map(vec)
        rect = self.rect()
        x = (vec.x() + 1.0) / 2.0 * rect.width()
        y = (1.0 - vec.y()) / 2.0 * rect.height()
        return np.array([x, y])

    def point_to_segment_dist(self, p, a, b):
        l2 = np.sum((a-b)**2)
        if l2 == 0: return np.linalg.norm(p-a)
        t = max(0, min(1, np.dot(p-a, b-a) / l2))
        proj = a + t * (b-a)
        return np.linalg.norm(p - proj)

    def polyline_dist(self, p, pts_2d):
        diffs = pts_2d[1:] - pts_2d[:-1]
        l2 = np.sum(diffs**2, axis=1)
        l2[l2==0] = 1e-6
        t = np.sum((p - pts_2d[:-1]) * diffs, axis=1) / l2
        t = np.clip(t, 0, 1)
        projs = pts_2d[:-1] + t[:, None] * diffs
        dists = np.linalg.norm(p - projs, axis=1)
        return np.min(dists)

    def projectionMatrix(self, region=None):
        import PyQt6.QtGui as QtGui
        from math import tan, radians
        
        if not getattr(self, 'is_ortho', False):
            return super().projectionMatrix(region)
            
        if region is None:
            region = (0, 0, self.deviceWidth(), self.deviceHeight())
        
        x0, y0, w, h = self.getViewport()
        dist = self.opts['distance']
        
        aspect = w / h if h > 0 else 1.0
        box_h = dist * 1.15
        box_w = box_h * aspect
        
        left = -box_w/2
        right = box_w/2
        bottom = -box_h/2
        top = box_h/2
        
        nearClip = dist * 0.001
        farClip = dist * 1000.
        
        tr = QtGui.QMatrix4x4()
        tr.ortho(left, right, bottom, top, nearClip, farClip)
        return tr
        
    def snap_camera(self, view_name):
        d = self.opts['distance']
        if view_name == 'Top': self.setCameraPosition(distance=d, elevation=90, azimuth=-90)
        elif view_name == 'Bottom': self.setCameraPosition(distance=d, elevation=-90, azimuth=-90)
        elif view_name == 'Front': self.setCameraPosition(distance=d, elevation=0, azimuth=-90)
        elif view_name == 'Back': self.setCameraPosition(distance=d, elevation=0, azimuth=90)
        elif view_name == 'Left': self.setCameraPosition(distance=d, elevation=0, azimuth=180)
        elif view_name == 'Right': self.setCameraPosition(distance=d, elevation=0, azimuth=0)

    def keyPressEvent(self, ev):
        super().keyPressEvent(ev)
        import PyQt6.QtCore as QtCore
        import PyQt6.QtGui as QtGui
        import numpy as np
        
        # Clipboard handling
        if ev.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier:
            if ev.key() == QtCore.Qt.Key.Key_C and self.selected_model:
                self._clipboard = {
                    'raw_vertices': self.selected_model.raw_vertices.copy(),
                    'raw_faces': getattr(self.selected_model, 'raw_faces', None),
                    'scale': self.selected_model.scale_vec.copy(),
                    'rot': QtGui.QMatrix4x4(self.selected_model.rot_matrix),
                    'rot_angles': getattr(self.selected_model, 'rot_angles', [0.0, 0.0, 0.0]).copy(),
                    'pos': self.selected_model.pos.copy() + np.array([20, 20, 0]),
                    'name': getattr(self.selected_model, 'file_name', 'Model') + ' (Copy)'
                }
                return
            elif ev.key() == QtCore.Qt.Key.Key_V:
                if hasattr(self, '_clipboard') and self._clipboard and self._clipboard['raw_faces'] is not None:
                    self.duplicate_model(self._clipboard)
                    # Shift next paste
                    self._clipboard['pos'] += np.array([20, 20, 0])
                return

        if not self.selected_model:
            return
            
        if ev.key() in [QtCore.Qt.Key.Key_Backspace, QtCore.Qt.Key.Key_Delete]:
            self.delete_model(self.selected_model)
        elif ev.key() == QtCore.Qt.Key.Key_Q:
            self.set_interaction_mode('translate')
        elif ev.key() == QtCore.Qt.Key.Key_W:
            self.set_interaction_mode('rotate')
        elif ev.key() == QtCore.Qt.Key.Key_E:
            self.set_interaction_mode('scale')

    def mousePressEvent(self, ev):
        super().mousePressEvent(ev)
        import PyQt6.QtCore as QtCore
        import PyQt6.QtGui as QtGui
        self.active_axis = None
        self.gizmo.highlight(None)
        
        if ev.button() == QtCore.Qt.MouseButton.LeftButton and self.interaction_mode in ['translate', 'rotate', 'scale'] and self.selected_model:
            lpos = ev.position() if hasattr(ev, 'position') else ev.localPos()
            p = np.array([lpos.x(), lpos.y()])
            
            center_2d = self.project_to_screen(self.model_center)
            best_dist = 20.0
            best_axis = None
            s = self.gizmo.size
            
            if self.interaction_mode in ['translate', 'scale']:
                axes_3d = {
                    'x': np.array([s,0,0]),
                    'y': np.array([0,s,0]),
                    'z': np.array([0,0,s])
                }
                for k, local_vec in axes_3d.items():
                    if hasattr(self.selected_model, 'rot_matrix'):
                        vec3d = self.selected_model.rot_matrix.map(QtGui.QVector3D(*local_vec))
                        world_vec = np.array([vec3d.x(), vec3d.y(), vec3d.z()])
                    else:
                        world_vec = local_vec
                    
                    tip3d = self.model_center + world_vec
                    tip_2d = self.project_to_screen(tip3d)
                    dist = self.point_to_segment_dist(p, center_2d, tip_2d)
                    if dist < best_dist:
                        best_dist = dist
                        best_axis = k
            elif self.interaction_mode == 'rotate':
                for k, ring_item in self.gizmo.r_rings.items():
                    pts_3d_local = ring_item.pos
                    pts_3d_world = []
                    for pt in pts_3d_local:
                        if hasattr(self.selected_model, 'rot_matrix'):
                            vec3d = self.selected_model.rot_matrix.map(QtGui.QVector3D(*pt))
                            world_pt = self.model_center + np.array([vec3d.x(), vec3d.y(), vec3d.z()])
                        else:
                            world_pt = self.model_center + pt
                        pts_3d_world.append(world_pt)
                        
                    pts_2d = np.array([self.project_to_screen(pt) for pt in pts_3d_world])
                    dist = self.polyline_dist(p, pts_2d)
                    if dist < best_dist:
                        best_dist = dist
                        best_axis = k
                        
            self.active_axis = best_axis
            self.gizmo.highlight(self.active_axis)
            
        hit_gizmo = (self.active_axis is not None)
        
        if not hit_gizmo and ev.button() == QtCore.Qt.MouseButton.LeftButton:
            lpos = ev.position() if hasattr(ev, "position") else ev.localPos()
            
            rect = self.rect()
            ndc_x = (lpos.x() / rect.width()) * 2.0 - 1.0
            ndc_y = 1.0 - (lpos.y() / rect.height()) * 2.0
            
            vec_near = QtGui.QVector3D(ndc_x, ndc_y, -1.0)
            vec_far = QtGui.QVector3D(ndc_x, ndc_y, 1.0)
            
            view_proj = self.projectionMatrix() * self.viewMatrix()
            inv_vp, invertible = view_proj.inverted()
            
            best_model = None
            best_dist = float("inf")
            
            if invertible:
                world_near = inv_vp.map(vec_near)
                world_far = inv_vp.map(vec_far)
                
                for model in self.active_models:
                    if not model.visible(): continue
                    v = getattr(model, "raw_vertices", model.opts.get("vertexes"))
                    if v is None: continue
                    min_b = v.min(axis=0)
                    max_b = v.max(axis=0)
                    
                    mat = QtGui.QMatrix4x4()
                    mat.translate(model.pos[0], model.pos[1], model.pos[2])
                    if hasattr(model, "rot_matrix"): mat = mat * model.rot_matrix
                    mat.scale(model.scale_vec[0], model.scale_vec[1], model.scale_vec[2])
                    
                    inv_mat, mat_invertible = mat.inverted()
                    if not mat_invertible: continue
                    
                    local_near = inv_mat.map(world_near)
                    local_far = inv_mat.map(world_far)
                    
                    local_dir = local_far - local_near
                    local_dir.normalize()
                    
                    dx = local_dir.x() if local_dir.x() != 0 else 1e-6
                    dy = local_dir.y() if local_dir.y() != 0 else 1e-6
                    dz = local_dir.z() if local_dir.z() != 0 else 1e-6
                    
                    t1 = (min_b[0] - local_near.x()) / dx
                    t2 = (max_b[0] - local_near.x()) / dx
                    t3 = (min_b[1] - local_near.y()) / dy
                    t4 = (max_b[1] - local_near.y()) / dy
                    t5 = (min_b[2] - local_near.z()) / dz
                    t6 = (max_b[2] - local_near.z()) / dz
                    
                    tmin = max(max(min(t1, t2), min(t3, t4)), min(t5, t6))
                    tmax = min(min(max(t1, t2), max(t3, t4)), max(t5, t6))
                    
                    if tmax >= 0 and tmax >= tmin:
                        if tmin < best_dist:
                            best_dist = tmin
                            best_model = model
            
            if best_model:
                self.select_model(best_model)
            else:
                self.select_model(None)
                self.set_interaction_mode("none")

    def event(self, ev):
        import PyQt6.QtCore as QtCore
        if ev.type() == QtCore.QEvent.Type.NativeGesture:
            if ev.gestureType() == QtCore.Qt.NativeGestureType.ZoomNativeGesture:
                self.opts['distance'] *= (1.0 - ev.value())
                self.update()
                return True
        return super().event(ev)

    def wheelEvent(self, ev):
        px = ev.pixelDelta()
        if not px.isNull():
            self.pan(px.x(), px.y(), 0, relative='view')
            ev.accept()
            return
        super().wheelEvent(ev)

    def pan(self, dx, dy, dz, relative='global'):
        if relative == 'view-upright':
            elev = self.opts.get('elevation', 0)
            if abs(elev) >= 89.9:
                relative = 'view'
        super().pan(dx, dy, dz, relative)

    def mouseMoveEvent(self, ev):
        lpos = ev.position() if hasattr(ev, 'position') else ev.localPos()
        if self._last_mouse_pos is None:
            self._last_mouse_pos = lpos
        diff = lpos - self._last_mouse_pos
        self._last_mouse_pos = lpos
        
        import PyQt6.QtCore as QtCore
        import PyQt6.QtGui as QtGui
        if ev.buttons() == QtCore.Qt.MouseButton.LeftButton:
            if self.interaction_mode != 'none' and self.selected_model and self.active_axis:
                if self.interaction_mode in ['translate', 'scale']:
                    local_axis = QtGui.QVector3D(0,0,0)
                    if self.active_axis == 'x': local_axis = QtGui.QVector3D(1,0,0)
                    elif self.active_axis == 'y': local_axis = QtGui.QVector3D(0,1,0)
                    elif self.active_axis == 'z': local_axis = QtGui.QVector3D(0,0,1)
                    
                    if hasattr(self.selected_model, 'rot_matrix'):
                        world_axis = self.selected_model.rot_matrix.map(local_axis)
                    else:
                        world_axis = local_axis
                        
                    world_axis_np = np.array([world_axis.x(), world_axis.y(), world_axis.z()])
                    
                    center_2d = self.project_to_screen(self.model_center)
                    tip3d = self.model_center + world_axis_np
                    tip_2d = self.project_to_screen(tip3d)
                    
                    axis_vec_2d = tip_2d - center_2d
                    norm = np.linalg.norm(axis_vec_2d)
                    if norm > 0: axis_vec_2d /= norm
                    
                    mouse_diff = np.array([diff.x(), diff.y()])
                    move_amount = np.dot(mouse_diff, axis_vec_2d)
                    
                    if self.interaction_mode == 'translate':
                        move_amount *= 0.5
                        delta = world_axis_np * move_amount
                        self.selected_model.pos += delta
                        self.model_center = self.selected_model.pos.copy()
                        
                    elif self.interaction_mode == 'scale':
                        scale_factor = 1.0 + (move_amount * 0.01)
                        is_locked = False
                        if hasattr(self, 'slice_widget') and hasattr(self.slice_widget, 'btn_scale_lock'):
                            is_locked = self.slice_widget.btn_scale_lock.isChecked()
                            
                        if is_locked:
                            self.selected_model.scale_vec[0] *= scale_factor
                            self.selected_model.scale_vec[1] *= scale_factor
                            self.selected_model.scale_vec[2] *= scale_factor
                        else:
                            if self.active_axis == 'x': self.selected_model.scale_vec[0] *= scale_factor
                            elif self.active_axis == 'y': self.selected_model.scale_vec[1] *= scale_factor
                            elif self.active_axis == 'z': self.selected_model.scale_vec[2] *= scale_factor
                        
                elif self.interaction_mode == 'rotate':
                    base_angle = (diff.x() + diff.y()) * 0.5
                    if not hasattr(self.selected_model, 'rot_angles'):
                        self.selected_model.rot_angles = [0.0, 0.0, 0.0]
                        
                    if self.active_axis == 'x': self.selected_model.rot_angles[0] -= base_angle
                    elif self.active_axis == 'y': self.selected_model.rot_angles[1] += base_angle
                    elif self.active_axis == 'z': self.selected_model.rot_angles[2] += base_angle
                    
                    # Reconstruct rot_matrix from rot_angles
                    new_rot = QtGui.QMatrix4x4()
                    new_rot.rotate(self.selected_model.rot_angles[0], 1, 0, 0)
                    new_rot.rotate(self.selected_model.rot_angles[1], 0, 1, 0)
                    new_rot.rotate(self.selected_model.rot_angles[2], 0, 0, 1)
                    self.selected_model.rot_matrix = new_rot
                        
                self.apply_transform(self.selected_model)
                rot = getattr(self.selected_model, 'rot_matrix', None)
                self.gizmo.update_position(self.model_center, rot)
                self.update()
                if hasattr(self, 'slice_widget'):
                    self.slice_widget.update_properties_panel(self.selected_model)
                return
            # Default Camera Orbit (reached if not interacting with gizmo)
            if (ev.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier):
                self.pan(diff.x(), diff.y(), 0, relative='view')
            else:
                self.orbit(-diff.x(), diff.y())
        elif ev.buttons() == QtCore.Qt.MouseButton.MiddleButton:
            if (ev.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier):
                self.pan(diff.x(), 0, diff.y(), relative='view-upright')
            else:
                self.pan(diff.x(), diff.y(), 0, relative='view-upright')
        else:
            # Hover logic could go here
            pass

    def mouseReleaseEvent(self, ev):
        super().mouseReleaseEvent(ev)
        self._last_mouse_pos = None
        self.active_axis = None
        self.gizmo.highlight(None)

    def wheelEvent(self, ev):
        pixel_delta = ev.pixelDelta()
        # If we have a pixel delta, it's a smooth trackpad scroll on macOS -> use for panning
        if not pixel_delta.isNull():
            self.pan(pixel_delta.x() * 0.5, pixel_delta.y() * 0.5, 0, relative='view-upright')
            ev.accept()
        else:
            super().wheelEvent(ev)

    def event(self, ev):
        import PyQt6.QtCore as QtCore
        # Catch native gestures like macOS trackpad pinch-to-zoom
        if ev.type() == QtCore.QEvent.Type.NativeGesture:
            if ev.gestureType() == QtCore.Qt.NativeGestureType.ZoomNativeGesture:
                multiplier = 1.0 - ev.value()
                self.opts['distance'] *= multiplier
                self.update()
                return True
        return super().event(ev)

class ViewCubeWidget(gl.GLViewWidget):
    def __init__(self, main_viewer, parent=None):
        super().__init__(parent)
        self.main_viewer = main_viewer
        
        import PyQt6.QtGui as QtGui
        self.setFixedSize(100, 100)
        
        self.opts['distance'] = 40
        self.opts['fov'] = 30
        
        import numpy as np
        verts = np.array([
            [1, 1, 1], [-1, 1, 1], [-1, -1, 1], [1, -1, 1],
            [1, 1, -1], [-1, 1, -1], [-1, -1, -1], [1, -1, -1],
        ]) * 10
        
        faces = np.array([
            [0, 1, 2], [0, 2, 3], # Top (Z)
            [4, 7, 6], [4, 6, 5], # Bottom (-Z)
            [0, 3, 7], [0, 7, 4], # Right (X)
            [1, 5, 6], [1, 6, 2], # Left (-X)
            [3, 2, 6], [3, 6, 7], # Front (Y)
            [0, 4, 5], [0, 5, 1], # Back (-Y)
        ])
        
        colors = np.array([
            [0.2, 0.5, 0.8, 1], [0.2, 0.5, 0.8, 1], # Top (Blue)
            [0.1, 0.3, 0.5, 1], [0.1, 0.3, 0.5, 1], # Bottom (Dark Blue)
            [0.8, 0.3, 0.3, 1], [0.8, 0.3, 0.3, 1], # Right (Red)
            [0.5, 0.1, 0.1, 1], [0.5, 0.1, 0.1, 1], # Left (Dark Red)
            [0.4, 0.7, 0.4, 1], [0.4, 0.7, 0.4, 1], # Front (Green)
            [0.2, 0.4, 0.2, 1], [0.2, 0.4, 0.2, 1], # Back (Dark Green)
        ])
        
        self.mesh = gl.GLMeshItem(vertexes=verts, faces=faces, faceColors=colors, smooth=False, drawEdges=True, edgeColor=(1,1,1,1))
        self.mesh.setGLOptions('opaque')
        self.addItem(self.mesh)
        
    def paintGL(self, *args, **kwargs):
        self.opts['elevation'] = self.main_viewer.opts['elevation']
        self.opts['azimuth'] = self.main_viewer.opts['azimuth']
        super().paintGL(*args, **kwargs)
        
    def project_to_screen(self, pos3d):
        import PyQt6.QtGui as QtGui
        import numpy as np
        pm = self.projectionMatrix()
        vm = self.viewMatrix()
        p = QtGui.QVector4D(pos3d[0], pos3d[1], pos3d[2], 1.0)
        p = pm * vm * p
        if p.w() == 0: return None
        p /= p.w()
        x = (p.x() + 1.0) * 0.5 * self.width()
        y = (1.0 - p.y()) * 0.5 * self.height()
        return np.array([x, y])

    def mousePressEvent(self, ev):
        super().mousePressEvent(ev)
        import PyQt6.QtCore as QtCore
        import numpy as np
        if ev.button() == QtCore.Qt.MouseButton.LeftButton:
            lpos = ev.position() if hasattr(ev, 'position') else ev.localPos()
            
            face_centers = {
                'Top': np.array([0, 0, 1]),
                'Bottom': np.array([0, 0, -1]),
                'Right': np.array([1, 0, 0]),
                'Left': np.array([-1, 0, 0]),
                'Front': np.array([0, 1, 0]),
                'Back': np.array([0, -1, 0]),
            }
            best_face = None
            min_dist = float('inf')
            
            cPos = self.cameraPosition()
            cDir = -cPos.normalized() 
            
            for name, center in face_centers.items():
                dot = np.dot(center, np.array([cDir.x(), cDir.y(), cDir.z()]))
                if dot < -0.1: 
                    screen_pos = self.project_to_screen(center * 10)
                    if screen_pos is not None:
                        dist = np.linalg.norm(np.array([lpos.x(), lpos.y()]) - screen_pos)
                        if dist < min_dist:
                            min_dist = dist
                            best_face = name
            
            if best_face and min_dist < 40:
                self.main_viewer.snap_camera(best_face)
