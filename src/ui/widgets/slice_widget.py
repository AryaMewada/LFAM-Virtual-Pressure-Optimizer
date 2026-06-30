from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame, QPushButton, QSpacerItem, 
    QSizePolicy, QFileDialog
)
from PyQt6.QtCore import Qt
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


class TransformGizmo:
    """3D Transform Gizmo with X, Y, Z axes for translate, rotate, scale."""
    def __init__(self, view):
        self.view = view
        self.mode = 'none'
        
        self.t_axes = {
            'x': gl.GLLinePlotItem(color=(1,0,0,1), width=4, antialias=True),
            'y': gl.GLLinePlotItem(color=(0,1,0,1), width=4, antialias=True),
            'z': gl.GLLinePlotItem(color=(0,0,1,1), width=4, antialias=True)
        }
        
        self.s_axes = {
            'x': gl.GLLinePlotItem(color=(1,0.5,0.5,1), width=6, antialias=True),
            'y': gl.GLLinePlotItem(color=(0.5,1,0.5,1), width=6, antialias=True),
            'z': gl.GLLinePlotItem(color=(0.5,0.5,1,1), width=6, antialias=True)
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
        self.center = np.array([0.0, 0.0, 0.0])
        self.size = 100.0

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

    def update_position(self, center):
        self.center = center
        s = self.size
        for d in [self.t_axes, self.s_axes]:
            d['x'].setData(pos=np.array([center, center + [s,0,0]]))
            d['y'].setData(pos=np.array([center, center + [0,s,0]]))
            d['z'].setData(pos=np.array([center, center + [0,0,s]]))
            
        r_verts = make_ring_verts(s * 0.75)
        x_ring = r_verts.copy(); x_ring[:, [0, 2]] = x_ring[:, [2, 0]]
        y_ring = r_verts.copy(); y_ring[:, [1, 2]] = y_ring[:, [2, 1]]
        z_ring = r_verts.copy()
        
        self.r_rings['x'].setData(pos=x_ring + center)
        self.r_rings['y'].setData(pos=y_ring + center)
        self.r_rings['z'].setData(pos=z_ring + center)

    def highlight(self, axis):
        colors = {'x': (1,0,0,1), 'y': (0,1,0,1), 'z': (0,0,1,1)}
        active_dict = None
        if self.mode == 'translate': active_dict = self.t_axes
        elif self.mode == 'scale': active_dict = self.s_axes
        elif self.mode == 'rotate': active_dict = self.r_rings
        
        if not active_dict: return
        
        for k, item in active_dict.items():
            if axis and k == axis:
                item.setData(color=(1,1,0,1), width=6)
            else:
                item.setData(color=colors[k], width=4)


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
            self.gizmo.update_position(self.model_center)
        else:
            self.gizmo.set_mode('none')
            self.active_axis = None
        self.update()

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
            
            # Center the model on the bed
            min_bounds = vertices.min(axis=0)
            max_bounds = vertices.max(axis=0)
            
            delta = -min_bounds
            mesh_item.translate(delta[0], delta[1], delta[2])
            
            self.model_center = (min_bounds + max_bounds)/2.0 + delta
            
            if self.interaction_mode == 'translate':
                self.gizmo.set_visible(True)
                self.gizmo.update_position(self.model_center)
            
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

    def mousePressEvent(self, ev):
        super().mousePressEvent(ev)
        import PyQt6.QtCore as QtCore
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
                    'x': self.model_center + [s,0,0],
                    'y': self.model_center + [0,s,0],
                    'z': self.model_center + [0,0,s]
                }
                for k, tip3d in axes_3d.items():
                    tip_2d = self.project_to_screen(tip3d)
                    dist = self.point_to_segment_dist(p, center_2d, tip_2d)
                    if dist < best_dist:
                        best_dist = dist
                        best_axis = k
            elif self.interaction_mode == 'rotate':
                for k, ring_item in self.gizmo.r_rings.items():
                    pts_3d = ring_item.pos
                    pts_2d = np.array([self.project_to_screen(pt) for pt in pts_3d])
                    dist = self.polyline_dist(p, pts_2d)
                    if dist < best_dist:
                        best_dist = dist
                        best_axis = k
                        
            self.active_axis = best_axis
            self.gizmo.highlight(self.active_axis)

    def mouseMoveEvent(self, ev):
        # Invert the default PyQtGraph orbit movement for standard CAD feel
        lpos = ev.position() if hasattr(ev, 'position') else ev.localPos()
        if self._last_mouse_pos is None:
            self._last_mouse_pos = lpos
        diff = lpos - self._last_mouse_pos
        self._last_mouse_pos = lpos
        
        import PyQt6.QtCore as QtCore
        if ev.buttons() == QtCore.Qt.MouseButton.LeftButton:
            if self.interaction_mode != 'none' and self.selected_model and self.active_axis:
                if self.interaction_mode in ['translate', 'scale']:
                    # Calculate vector
                    center_2d = self.project_to_screen(self.model_center)
                    tip3d = self.model_center.copy()
                    if self.active_axis == 'x': tip3d[0] += 1
                    elif self.active_axis == 'y': tip3d[1] += 1
                    elif self.active_axis == 'z': tip3d[2] += 1
                    tip_2d = self.project_to_screen(tip3d)
                    
                    axis_vec_2d = tip_2d - center_2d
                    norm = np.linalg.norm(axis_vec_2d)
                    if norm > 0:
                        axis_vec_2d /= norm
                        
                    mouse_diff = np.array([diff.x(), diff.y()])
                    move_amount = np.dot(mouse_diff, axis_vec_2d)
                    
                    if self.interaction_mode == 'translate':
                        move_amount *= 0.5
                        delta = [0.0, 0.0, 0.0]
                        if self.active_axis == 'x': delta[0] = move_amount
                        elif self.active_axis == 'y': delta[1] = move_amount
                        elif self.active_axis == 'z': delta[2] = move_amount
                        
                        self.selected_model.translate(*delta)
                        self.model_center += delta
                        self.gizmo.update_position(self.model_center)
                        
                    elif self.interaction_mode == 'scale':
                        scale_factor = 1.0 + (move_amount * 0.01)
                        # Pivot math: translate to origin, scale, translate back
                        self.selected_model.translate(-self.model_center[0], -self.model_center[1], -self.model_center[2])
                        sx = scale_factor if self.active_axis == 'x' else 1.0
                        sy = scale_factor if self.active_axis == 'y' else 1.0
                        sz = scale_factor if self.active_axis == 'z' else 1.0
                        self.selected_model.scale(sx, sy, sz)
                        self.selected_model.translate(self.model_center[0], self.model_center[1], self.model_center[2])
                        
                elif self.interaction_mode == 'rotate':
                    # Rotate around axis
                    angle = (diff.x() + diff.y()) * 0.5
                    ax, ay, az = 0, 0, 0
                    if self.active_axis == 'x': ax = 1
                    elif self.active_axis == 'y': ay = 1
                    elif self.active_axis == 'z': az = 1
                    
                    self.selected_model.translate(-self.model_center[0], -self.model_center[1], -self.model_center[2])
                    self.selected_model.rotate(angle, ax, ay, az)
                    self.selected_model.translate(self.model_center[0], self.model_center[1], self.model_center[2])
                    
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
