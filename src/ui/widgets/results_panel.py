"""Results panel widget for displaying optimization results."""

from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QWidget, QPushButton, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPainter, QColor, QLinearGradient, QPen, QFont, QBrush

from src.ui.theme import Theme


class ResultCard(QFrame):
    """A single result summary card with custom painted background."""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self._value = '—'
        self._title = title
        self._color = Theme.TEXT_PRIMARY
        self.setFixedHeight(100)
        self.setMinimumWidth(130)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

    def set_value(self, value: str, color: str = None):
        """Update the displayed value and optionally the value color."""
        self._value = value
        if color is not None:
            self._color = color
        self.update()

    def paintEvent(self, event):
        try:
            self._safe_paintEvent(event)
        except Exception as e:
            import traceback
            with open('paintevent_error.txt', 'a') as errf:
                errf.write(f'Error in src/ui/widgets/results_panel.py: {str(e)}\n{traceback.format_exc()}\n')

    def _safe_paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect().adjusted(0, 0, -1, -1)
        radius = 12.0

        # Gradient background from BG_TERTIARY to BG_ELEVATED
        gradient = QLinearGradient(0, 0, 0, rect.height())
        gradient.setColorAt(0.0, QColor(Theme.BG_TERTIARY))
        gradient.setColorAt(1.0, QColor(Theme.BG_ELEVATED))
        painter.setBrush(QBrush(gradient))

        # 1px border
        painter.setPen(QPen(QColor(Theme.BORDER), 1.0))
        painter.drawRoundedRect(rect, radius, radius)

        # Draw value text (24pt bold, centered-top, y=45)
        value_font = QFont('Inter', 24, QFont.Weight.Bold)
        painter.setFont(value_font)
        painter.setPen(QColor(self._color))
        value_rect = rect.adjusted(8, 0, -8, 0)
        value_rect.setTop(10)
        value_rect.setBottom(55)
        painter.drawText(value_rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom, self._value)

        # Draw title text (10pt, TEXT_SECONDARY, below value, y=72)
        title_font = QFont('Inter', 10)
        painter.setFont(title_font)
        painter.setPen(QColor(Theme.TEXT_SECONDARY))
        title_rect = rect.adjusted(8, 0, -8, 0)
        title_rect.setTop(60)
        title_rect.setBottom(90)
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, self._title)

        painter.end()


class ModificationEntry(QFrame):
    """A single modification log entry with type badge, move ID, and reason."""

    # Color mapping for modification types
    TYPE_COLORS = {
        'corner': Theme.WARNING,
        'ramp': Theme.ACCENT_PRIMARY,
        'taper': Theme.ACCENT_SECONDARY,
        'smoothing': Theme.SUCCESS,
    }

    def __init__(self, mod_type: str, move_id: str, reason: str, parent=None):
        super().__init__(parent)
        self.setFixedHeight(36)
        self.setStyleSheet(f'background: transparent; border: none;')

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(8)

        # Type badge
        color = self.TYPE_COLORS.get(mod_type, Theme.TEXT_MUTED)
        type_label = QLabel(mod_type.capitalize())
        type_label.setFixedWidth(90)
        type_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        type_label.setStyleSheet(
            f'background-color: {color}22; '
            f'color: {color}; '
            f'border-radius: 4px; '
            f'font-size: 8pt; '
            f'font-weight: bold; '
            f'padding: 2px 4px; '
            f'border: 1px solid {color}44;'
        )
        layout.addWidget(type_label)

        # Move ID label
        move_label = QLabel(str(move_id))
        move_label.setFixedWidth(80)
        move_label.setStyleSheet(
            f'color: {Theme.TEXT_PRIMARY}; '
            f'font-size: 10pt; '
            f'background: transparent; '
            f'border: none;'
        )
        layout.addWidget(move_label)

        # Reason label
        reason_label = QLabel(reason)
        reason_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        reason_label.setStyleSheet(
            f'color: {Theme.TEXT_SECONDARY}; '
            f'font-size: 10pt; '
            f'background: transparent; '
            f'border: none;'
        )
        layout.addWidget(reason_label)


class ResultsPanel(QFrame):
    """Panel displaying optimization results with summary cards and modification log."""

    save_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setVisible(False)
        self._max_display = 100
        self._show_all = False
        self._modifications = []

        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(16)

        # Title label
        title_label = QLabel('Optimization Results')
        title_label.setStyleSheet(
            f'color: {Theme.TEXT_PRIMARY}; '
            f'font-size: 14pt; '
            f'font-weight: bold; '
            f'background: transparent; '
            f'border: none;'
        )
        main_layout.addWidget(title_label)

        # Summary cards row
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(12)

        self._card_pressure = ResultCard('Pressure Reduction')
        self._card_modifications = ResultCard('Modifications Made')
        self._card_corners = ResultCard('Corners Fixed')
        self._card_ramps = ResultCard('Ramps Added')

        cards_layout.addWidget(self._card_pressure)
        cards_layout.addWidget(self._card_modifications)
        cards_layout.addWidget(self._card_corners)
        cards_layout.addWidget(self._card_ramps)

        main_layout.addLayout(cards_layout)

        # Modifications log accordion toggle
        self._log_toggle_btn = QPushButton('▶ Show Optimization Logs')
        self._log_toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._log_toggle_btn.setStyleSheet(
            f'QPushButton {{ '
            f'  color: {Theme.TEXT_SECONDARY}; '
            f'  font-size: 12pt; '
            f'  font-weight: bold; '
            f'  background: transparent; '
            f'  border: none; '
            f'  text-align: left; '
            f'}}'
            f'QPushButton:hover {{ color: {Theme.TEXT_PRIMARY}; }}'
        )
        self._log_toggle_btn.clicked.connect(self._toggle_logs_accordion)
        main_layout.addWidget(self._log_toggle_btn)

        # Scroll area for modification entries
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll_area.setStyleSheet(
            f'QScrollArea {{ background: transparent; border: none; }}'
            f'QScrollBar:vertical {{ '
            f'  background: {Theme.BG_SECONDARY}; width: 8px; border-radius: 4px; '
            f'}}'
            f'QScrollBar::handle:vertical {{ '
            f'  background: {Theme.BG_TERTIARY}; border-radius: 4px; min-height: 30px; '
            f'}}'
            f'QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}'
        )
        self._scroll_area.setMinimumHeight(150)
        self._scroll_area.setMaximumHeight(350)

        self._entries_container = QWidget()
        self._entries_container.setStyleSheet('background: transparent; border: none;')
        self._entries_layout = QVBoxLayout(self._entries_container)
        self._entries_layout.setContentsMargins(0, 0, 0, 0)
        self._entries_layout.setSpacing(4)
        self._entries_layout.addStretch()

        self._scroll_area.setWidget(self._entries_container)
        self._scroll_area.setVisible(False) # Hidden by default (accordion)
        main_layout.addWidget(self._scroll_area)

        # Show all button
        self._show_all_btn = QPushButton('Show All')
        self._show_all_btn.setVisible(False)
        self._show_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._show_all_btn.setStyleSheet(
            f'QPushButton {{ '
            f'  background: {Theme.BG_TERTIARY}; '
            f'  color: {Theme.ACCENT_PRIMARY}; '
            f'  border: 1px solid {Theme.ACCENT_PRIMARY}44; '
            f'  border-radius: 6px; '
            f'  padding: 8px 16px; '
            f'  font-size: 10pt; '
            f'  font-weight: bold; '
            f'}} '
            f'QPushButton:hover {{ '
            f'  background: {Theme.ACCENT_PRIMARY}22; '
            f'}}'
        )
        self._show_all_btn.clicked.connect(self._toggle_show_all)
        main_layout.addWidget(self._show_all_btn)

        # Save button removed as per user request
    
    def _toggle_logs_accordion(self):
        """Toggle the visibility of the logs scroll area."""
        is_visible = self._scroll_area.isVisible()
        self._scroll_area.setVisible(not is_visible)
        self._show_all_btn.setVisible(not is_visible and len(self._modifications) > self._max_display)
        if is_visible:
            self._log_toggle_btn.setText('▶ Show Optimization Logs')
        else:
            self._log_toggle_btn.setText('▼ Hide Optimization Logs')

    def _toggle_show_all(self):
        """Toggle between showing limited and all modification entries."""
        self._show_all = not self._show_all
        self._populate_entries()

    def _clear_entries(self):
        """Remove all existing modification entries from the layout."""
        while self._entries_layout.count() > 1:
            item = self._entries_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _populate_entries(self):
        """Populate the entries layout based on current state."""
        self._clear_entries()

        if self._show_all:
            display_mods = self._modifications
        else:
            display_mods = self._modifications[:self._max_display]

        for mod in display_mods:
            entry = ModificationEntry(
                mod_type=mod.get('type', 'unknown'),
                move_id=str(mod.get('move_id', '—')),
                reason=mod.get('reason', ''),
                parent=self._entries_container
            )
            self._entries_layout.insertWidget(self._entries_layout.count() - 1, entry)

        # Update show all button
        total = len(self._modifications)
        if total > self._max_display and self._scroll_area.isVisible():
            remaining = total - self._max_display
            if self._show_all:
                self._show_all_btn.setText(f'Show Less (showing all {total})')
            else:
                self._show_all_btn.setText(f'Show All ({remaining} more)')
            self._show_all_btn.setVisible(True)
        else:
            self._show_all_btn.setVisible(False)

    def update_results(self, summary: dict, modifications: list):
        """Update the results panel with optimization summary and modifications.

        Args:
            summary: Dict with keys 'pressure_reduction', 'modifications_made',
                     'corners_fixed', 'ramps_added'.
            modifications: List of dicts with keys 'type', 'move_id', 'reason'.
        """
        # Update summary cards
        pressure = summary.get('pressure_reduction', 0)
        self._card_pressure.set_value(f'{pressure}%', Theme.SUCCESS)
        self._card_modifications.set_value(str(summary.get('modifications_made', 0)))
        self._card_corners.set_value(str(summary.get('corners_fixed', 0)))
        self._card_ramps.set_value(str(summary.get('ramps_added', 0)))

        # Store modifications and populate entries
        self._modifications = modifications
        self._show_all = False
        self._populate_entries()

        self.setVisible(True)
