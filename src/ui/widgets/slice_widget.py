from PyQt6.QtCore import Qt

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame, QPushButton, QSpacerItem, 
    QSizePolicy, QFileDialog
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
            'x': gl.GLLinePlotItem(pos=make_arrow_verts('x', 50), color=(1,0,0,1), width=4, antialias=True, mode='lines'),
            'y': gl.GLLinePlotItem(pos=make_arrow_verts('y', 50), color=(0,1,0,1), width=4, antialias=True, mode='lines'),
            'z': gl.GLLinePlotItem(pos=make_arrow_verts('z', 50), color=(0,0,1,1), width=4, antialias=True, mode='lines')
        }
        
        self.s_axes = {
            'x': gl.GLLinePlotItem(pos=np.array([[0,0,0],[50,0,0]]), color=(1,0.5,0.5,1), width=6, antialias=True, mode='lines'),
            'y': gl.GLLinePlotItem(pos=np.array([[0,0,0],[0,50,0]]), color=(0.5,1,0.5,1), width=6, antialias=True, mode='lines'),
            'z': gl.GLLinePlotItem(pos=np.array([[0,0,0],[0,0,50]]), color=(0.5,0.5,1,1), width=6, antialias=True, mode='lines')
        }
        
        r_verts = make_ring_verts(50.0)
        x_ring = r_verts.copy(); x_ring[:, [0, 2]] = x_ring[:, [2, 0]]
        y_ring = r_verts.copy(); y_ring[:, [1, 2]] = y_ring[:, [2, 1]]
        z_ring = r_verts.copy()
        
        self.r_rings = {
            'x': gl.GLLinePlotItem(pos=x_ring, color=(1,0,0,1), width=4, antialias=True, mode='line_strip'),
            'y': gl.GLLinePlotItem(pos=y_ring, color=(0,1,0,1), width=4, antialias=True, mode='line_strip'),
            'z': gl.GLLinePlotItem(pos=z_ring, color=(0,0,1,1), width=4, antialias=True, mode='line_strip')
        }
        
        self.all_items = []
        for d in [self.t_axes, self.s_axes, self.r_rings]:
            for item in d.values():
                item.setDepthValue(10)
                self.view.addItem(item)
                self.all_items.append(item)
                
        self.set_mode('none')
        self.pos = np.array([0.0, 0.0, 0.0])
        self.size = 50.0

    def set_mode(self, mode):
        self.mode = mode
        for item in self.all_items:
            item.setVisible(False)
        
        if mode == 'translate':
            for item in self.t_axes.values(): item.setVisible(True)
        elif mode == 'scale':
            for item in self.s_axes.values(): item.setVisible(True)
        elif mode == 'rotate':
            for item in self.r_rings.values(): item.setVisible(True)

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
        
        left_layout.addStretch()
        
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
        right_layout.addStretch()
        
        # Add all to main layout
        layout.addWidget(self.left_sidebar)
        layout.addWidget(self.center_view, stretch=1)
        layout.addWidget(self.right_sidebar)

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

    def set_machine_dimensions(self, w: float, d: float, h: float):
        """Initializes the OpenGL viewer with a grid based on passed dimensions."""
        # Clear existing grid if any
        items_to_remove = [item for item in self.gl_viewer.items if isinstance(item, gl.GLGridItem)]
        for item in items_to_remove:
            self.gl_viewer.removeItem(item)
            
        grid = gl.GLGridItem()
        grid.setSize(x=w, y=d)
        grid.setSpacing(x=w/20, y=d/20)
        grid.translate(w/2, d/2, 0)
        self.gl_viewer.addItem(grid)        
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
                model = self.gl_viewer.load_stl(file_path)
                if model:
                    name = os.path.basename(file_path)
                    sg_item = SceneGraphItem(name, model, self.gl_viewer)
                    self.sg_layout.addWidget(sg_item)
                    sg_item.show()
            self.scene_graph_area.update()


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
            
            cx = self.opts.get('center', pyqtgraph.Vector(0,0,0)).x()
            cy = self.opts.get('center', pyqtgraph.Vector(0,0,0)).y()
            cz = 0.0
            
            height = max_bounds[2] - min_bounds[2]
            
            import PyQt6.QtGui as QtGui
            mesh_item.pos = np.array([cx, cy, cz + height/2.0])
            mesh_item.rot_matrix = QtGui.QMatrix4x4()
            mesh_item.scale_vec = [1.0, 1.0, 1.0]
            mesh_item.raw_vertices = vertices
            
            self.model_center = mesh_item.pos.copy()
            self.apply_transform(mesh_item)
            
            if self.interaction_mode != 'none':
                self.gizmo.set_mode(self.interaction_mode)
                self.gizmo.update_position(self.model_center, mesh_item.rot_matrix)
                
            return mesh_item
            
        except Exception as e:
            print(f"Failed to load STL: {e}")

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

    def keyPressEvent(self, ev):
        super().keyPressEvent(ev)
        if not self.selected_model:
            return
            
        import PyQt6.QtCore as QtCore
        if ev.key() == QtCore.Qt.Key.Key_Q:
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
                        if self.active_axis == 'x': self.selected_model.scale_vec[0] *= scale_factor
                        elif self.active_axis == 'y': self.selected_model.scale_vec[1] *= scale_factor
                        elif self.active_axis == 'z': self.selected_model.scale_vec[2] *= scale_factor
                        
                elif self.interaction_mode == 'rotate':
                    base_angle = (diff.x() + diff.y()) * 0.5
                    new_rot = QtGui.QMatrix4x4()
                    if self.active_axis == 'x': new_rot.rotate(-base_angle, 1, 0, 0)
                    elif self.active_axis == 'y': new_rot.rotate(base_angle, 0, 1, 0)
                    elif self.active_axis == 'z': new_rot.rotate(base_angle, 0, 0, 1)
                    
                    if hasattr(self.selected_model, 'rot_matrix'):
                        self.selected_model.rot_matrix = self.selected_model.rot_matrix * new_rot
                        
                self.apply_transform(self.selected_model)
                rot = getattr(self.selected_model, 'rot_matrix', None)
                self.gizmo.update_position(self.model_center, rot)
                self.update()
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
