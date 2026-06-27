"""
File upload widget with drag-and-drop support for G-code files.
Provides a visual drop zone with three states: empty, loading, and loaded.
"""

import os

from PyQt6.QtCore import Qt, pyqtSignal, QRect, QPoint
from PyQt6.QtGui import QPainter, QPen, QColor, QFont, QPolygon, QPainterPath
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar, QPushButton, QFileDialog, QSizePolicy
)

from src.ui.theme import Theme


SUPPORTED_EXTENSIONS = {'.gcode', '.nc', '.ngc', '.g'}


class FileUploadWidget(QFrame):
    """
    A drag-and-drop file upload widget for G-code files.

    Supports three visual states:
    - 'empty': Dashed border drop zone with upload icon and instructional text.
    - 'loading': Centered progress bar.
    - 'loaded': Displays file info (name, size, line count) with a clear button.

    Signals:
        file_loaded(str): Emitted with the absolute file path when a file is loaded.
    """

    file_loaded = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('FileUploadWidget')
        self.setAcceptDrops(True)
        self.setMinimumHeight(200)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        # State management
        self._state = 'empty'  # 'empty', 'loading', 'loaded'
        self._drag_hovering = False

        # File info
        self._file_path = ''
        self._file_size = 0
        self._line_count = 0

        # Loaded state widgets (created lazily, added to layout)
        self._loaded_layout = QVBoxLayout(self)
        self._loaded_layout.setContentsMargins(20, 20, 20, 20)
        self._loaded_layout.setSpacing(12)

        # --- File info row ---
        self._info_container = QFrame(self)
        self._info_container.setVisible(False)
        info_h_layout = QHBoxLayout(self._info_container)
        info_h_layout.setContentsMargins(0, 0, 0, 0)
        info_h_layout.setSpacing(14)

        # File icon label (drawn with unicode)
        self._file_icon_label = QLabel('📄', self._info_container)
        self._file_icon_label.setFixedSize(40, 40)
        self._file_icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._file_icon_label.setStyleSheet(
            f'background-color: {Theme.BG_TERTIARY}; border-radius: 8px; font-size: 20px;'
        )
        info_h_layout.addWidget(self._file_icon_label)

        # Text info column
        info_text_layout = QVBoxLayout()
        info_text_layout.setContentsMargins(0, 0, 0, 0)
        info_text_layout.setSpacing(2)

        self._file_name_label = QLabel('', self._info_container)
        self._file_name_label.setStyleSheet(
            f'color: {Theme.TEXT_PRIMARY}; font-size: 13px; font-weight: 600; background: transparent;'
        )
        info_text_layout.addWidget(self._file_name_label)

        self._file_details_label = QLabel('', self._info_container)
        self._file_details_label.setStyleSheet(
            f'color: {Theme.TEXT_SECONDARY}; font-size: 11px; background: transparent;'
        )
        info_text_layout.addWidget(self._file_details_label)

        info_h_layout.addLayout(info_text_layout)
        info_h_layout.addStretch()

        # Clear button
        self._clear_button = QPushButton('Clear', self._info_container)
        self._clear_button.setFixedHeight(32)
        self._clear_button.setFixedWidth(80)
        self._clear_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._clear_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.BG_TERTIARY};
                color: {Theme.TEXT_SECONDARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
                font-size: 12px;
                font-weight: 500;
                padding: 4px 16px;
            }}
            QPushButton:hover {{
                background-color: {Theme.DANGER};
                color: {Theme.TEXT_PRIMARY};
                border-color: {Theme.DANGER};
            }}
        """)
        self._clear_button.clicked.connect(self._clear_file)
        info_h_layout.addWidget(self._clear_button)

        self._loaded_layout.addWidget(self._info_container)

        # --- Progress bar (for loading state) ---
        self._progress_bar = QProgressBar(self)
        self._progress_bar.setVisible(False)
        self._progress_bar.setMinimum(0)
        self._progress_bar.setMaximum(0)  # Indeterminate
        self._progress_bar.setFixedHeight(6)
        self._progress_bar.setTextVisible(False)
        self._progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {Theme.BG_TERTIARY};
                border: none;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: {Theme.ACCENT_PRIMARY};
                border-radius: 3px;
            }}
        """)
        self._loaded_layout.addWidget(self._progress_bar, alignment=Qt.AlignmentFlag.AlignCenter)

        # --- Browse button (for empty state) ---
        self._browse_button = QPushButton("Browse G-Code...", self)
        self._browse_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._browse_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.ACCENT_PRIMARY};
                color: {Theme.TEXT_PRIMARY};
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 600;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {Theme.ACCENT_SECONDARY};
            }}
        """)
        self._browse_button.clicked.connect(self._open_file_dialog)
        self._loaded_layout.addWidget(self._browse_button, alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom)

        self._loaded_layout.addStretch()

        # Base stylesheet
        self.setStyleSheet(f"""
            #FileUploadWidget {{
                background-color: {Theme.BG_SECONDARY};
                border-radius: 12px;
            }}
        """)

    # ─── State Management ───────────────────────────────────────────

    def _set_state(self, state: str):
        """Transition to a new widget state."""
        self._state = state
        self._info_container.setVisible(state == 'loaded')
        self._progress_bar.setVisible(state == 'loading')
        self._browse_button.setVisible(state == 'empty')
        if state == 'empty':
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        self.update()

    # ─── File Operations ────────────────────────────────────────────

    def _load_file_info(self, path: str):
        """Read file metadata: size and estimate line count."""
        self._file_path = os.path.abspath(path)
        self._file_size = os.path.getsize(self._file_path)
        # Estimate line count based on average 30 bytes per line for G-code
        # This avoids blocking the UI for large files
        self._line_count = self._file_size // 30

    def _format_size(self, size_bytes: int) -> str:
        """Format file size as human-readable string."""
        if size_bytes < 1024:
            return f'{size_bytes} B'
        elif size_bytes < 1024 * 1024:
            return f'{size_bytes / 1024:.1f} KB'
        else:
            return f'{size_bytes / (1024 * 1024):.2f} MB'

    def _process_file(self, path: str):
        """Load file info, update UI, transition to loaded state, emit signal."""
        self._set_state('loading')

        # Load file info (synchronous for typical G-code file sizes)
        self._load_file_info(path)

        # Update labels
        self._file_name_label.setText(os.path.basename(self._file_path))
        size_str = self._format_size(self._file_size)
        self._file_details_label.setText(
            f'{size_str}  •  {self._line_count:,} lines'
        )

        self._set_state('loaded')
        self.file_loaded.emit(self._file_path)

    def _clear_file(self):
        """Reset widget to empty state."""
        self._file_path = ''
        self._file_size = 0
        self._line_count = 0
        self._file_name_label.setText('')
        self._file_details_label.setText('')
        self._set_state('empty')

    def _is_valid_extension(self, path: str) -> bool:
        """Check if the file has a supported extension."""
        _, ext = os.path.splitext(path)
        return ext.lower() in SUPPORTED_EXTENSIONS

    # ─── Mouse Events ───────────────────────────────────────────────

    def _open_file_dialog(self):
        ext_filter = 'G-code Files (*.gcode *.nc *.ngc *.g);;All Files (*)'
        path, _ = QFileDialog.getOpenFileName(
            self, 'Open G-code File', '', ext_filter
        )
        if path and self._is_valid_extension(path):
            self._process_file(path)

    def mousePressEvent(self, event):
        """Open file dialog on click when in empty state."""
        if self._state == 'empty' and event.button() == Qt.MouseButton.LeftButton:
            self._open_file_dialog()
        super().mousePressEvent(event)

    # ─── Drag and Drop Events ───────────────────────────────────────

    def dragEnterEvent(self, event):
        """Accept drag if it contains a file with a valid extension."""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                path = urls[0].toLocalFile()
                if self._is_valid_extension(path):
                    event.acceptProposedAction()
                    self._drag_hovering = True
                    self.update()
                    return
        event.ignore()

    def dragLeaveEvent(self, event):
        """Reset drag hover state."""
        self._drag_hovering = False
        self.update()
        super().dragLeaveEvent(event)

    def dropEvent(self, event):
        """Process the dropped file."""
        self._drag_hovering = False
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                path = urls[0].toLocalFile()
                if self._is_valid_extension(path):
                    event.acceptProposedAction()
                    self._process_file(path)
                    return
        event.ignore()

    # ─── Paint Event ────────────────────────────────────────────────

    def paintEvent(self, event):
        """Custom paint for empty and drag-hovering states."""
        super().paintEvent(event)

        if self._state != 'empty':
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect().adjusted(8, 8, -8, -8)

        # Determine colors based on hover state
        if self._drag_hovering:
            border_color = QColor(Theme.ACCENT_SECONDARY)
            bg_color = QColor(Theme.BG_TERTIARY)
            bg_color.setAlpha(80)
        else:
            border_color = QColor(Theme.ACCENT_PRIMARY)
            bg_color = QColor(Theme.BG_SECONDARY)
            bg_color.setAlpha(0)

        # Draw background fill when hovering
        if self._drag_hovering:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(bg_color)
            path = QPainterPath()
            path.addRoundedRect(float(rect.x()), float(rect.y()),
                                float(rect.width()), float(rect.height()), 10.0, 10.0)
            painter.drawPath(path)

        # Draw dashed border
        pen = QPen(border_color, 2.0, Qt.PenStyle.CustomDashLine)
        pen.setDashPattern([8, 6])
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect, 10, 10)

        # --- Draw upload arrow icon ---
        center_x = rect.center().x()
        icon_top = rect.top() + 35

        icon_color = QColor(Theme.ACCENT_SECONDARY) if self._drag_hovering else QColor(Theme.ACCENT_PRIMARY)
        painter.setPen(QPen(icon_color, 2.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # Vertical line of the arrow (shaft)
        shaft_bottom = icon_top + 32
        shaft_top = icon_top + 8
        painter.drawLine(center_x, shaft_bottom, center_x, shaft_top)

        # Arrowhead (chevron pointing up)
        arrow_size = 10
        painter.drawLine(center_x, shaft_top, center_x - arrow_size, shaft_top + arrow_size)
        painter.drawLine(center_x, shaft_top, center_x + arrow_size, shaft_top + arrow_size)

        # Horizontal base line (tray)
        tray_y = shaft_bottom + 6
        tray_half_width = 18
        painter.drawLine(center_x - tray_half_width, tray_y, center_x - tray_half_width, shaft_bottom)
        painter.drawLine(center_x + tray_half_width, tray_y, center_x + tray_half_width, shaft_bottom)
        painter.drawLine(center_x - tray_half_width, tray_y, center_x + tray_half_width, tray_y)

        # --- Draw text ---
        text_y = icon_top + 58

        # Main text
        main_font = QFont('Segoe UI', 13)
        main_font.setWeight(QFont.Weight.DemiBold)
        painter.setFont(main_font)
        painter.setPen(QColor(Theme.TEXT_PRIMARY))
        main_text_rect = QRect(rect.left(), text_y, rect.width(), 24)
        painter.drawText(main_text_rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                         'Drop G-code file here')

        # Sub text
        sub_font = QFont('Segoe UI', 11)
        painter.setFont(sub_font)
        painter.setPen(QColor(Theme.TEXT_SECONDARY))
        sub_text_rect = QRect(rect.left(), text_y + 28, rect.width(), 20)
        painter.drawText(sub_text_rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                         'or click to browse')

        # Formats text
        format_font = QFont('Segoe UI', 9)
        painter.setFont(format_font)
        painter.setPen(QColor(Theme.TEXT_MUTED))
        format_text_rect = QRect(rect.left(), text_y + 54, rect.width(), 18)
        painter.drawText(format_text_rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                         'Supported: .gcode  .nc  .ngc  .g')

        painter.end()
