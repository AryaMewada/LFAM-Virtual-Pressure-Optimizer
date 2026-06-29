"""Toast notification widget for displaying transient messages."""

from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton,
    QGraphicsDropShadowEffect, QSizePolicy
)
from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint, QRect
)
from PyQt6.QtGui import QColor, QFont

from src.ui.theme import Theme


class ToastNotification(QFrame):
    """A toast notification that slides in from the right and auto-dismisses."""

    # Class-level dict mapping parent widget id to list of active toasts
    _active_toasts: dict = {}

    # Type configuration
    TYPE_COLORS = {
        'info': '#3b82f6',
        'success': '#10b981',
        'warning': '#f59e0b',
        'error': '#ef4444',
    }

    TYPE_ICONS = {
        'info': 'ℹ',
        'success': '✓',
        'warning': '⚠',
        'error': '✕',
    }

    def __init__(self, parent, message: str, toast_type: str = 'info', duration: int = 3000):
        super().__init__(parent)
        self._toast_type = toast_type
        self._duration = duration
        self._dismissed = False

        color = self.TYPE_COLORS.get(toast_type, self.TYPE_COLORS['info'])
        icon_char = self.TYPE_ICONS.get(toast_type, self.TYPE_ICONS['info'])

        self.setFixedWidth(350)
        self.setMinimumHeight(50)

        # Styling
        self.setStyleSheet(
            f'ToastNotification {{ '
            f'  background-color: {Theme.BG_ELEVATED}; '
            f'  border: 1px solid {Theme.BORDER}; '
            f'  border-left: 4px solid {color}; '
            f'  border-radius: 10px; '
            f'}}'
        )

        # Drop shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

        # Layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 8, 10)
        layout.setSpacing(10)

        # Icon
        icon_label = QLabel(icon_char)
        icon_label.setStyleSheet(
            f'color: {color}; '
            f'font-size: 20pt; '
            f'background: transparent; '
            f'border: none;'
        )
        icon_label.setFixedWidth(30)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        # Message
        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        msg_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        msg_label.setStyleSheet(
            f'color: {Theme.TEXT_PRIMARY}; '
            f'font-size: 11pt; '
            f'background: transparent; '
            f'border: none;'
        )
        layout.addWidget(msg_label)

        # Close button
        close_btn = QPushButton('×')
        close_btn.setFixedSize(24, 24)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(
            f'QPushButton {{ '
            f'  color: {Theme.TEXT_MUTED}; '
            f'  background: transparent; '
            f'  border: none; '
            f'  font-size: 16pt; '
            f'  font-weight: bold; '
            f'  padding: 0; '
            f'}} '
            f'QPushButton:hover {{ '
            f'  color: {Theme.TEXT_PRIMARY}; '
            f'}}'
        )
        close_btn.clicked.connect(self._dismiss)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignTop)

        # Adjust size for content
        self.adjustSize()

        # Register this toast
        parent_id = id(parent)
        if parent_id not in ToastNotification._active_toasts:
            ToastNotification._active_toasts[parent_id] = []
        ToastNotification._active_toasts[parent_id].append(self)

        # Position and animate
        self._position_toast()
        self._animate_in()

        # Auto-dismiss timer
        if duration > 0:
            QTimer.singleShot(duration, self._dismiss)

    def _position_toast(self):
        """Calculate position based on active toasts stacking from bottom-right."""
        parent = self.parentWidget()
        if not parent:
            return

        parent_id = id(parent)
        active = ToastNotification._active_toasts.get(parent_id, [])

        margin_right = 20
        margin_bottom = 20
        spacing = 8

        # Calculate y offset from accumulated heights of toasts below this one
        y_offset = margin_bottom
        for toast in active:
            if toast is self:
                break
            if not toast._dismissed:
                y_offset += toast.sizeHint().height() + spacing

        x = parent.width() - self.width() - margin_right
        y = parent.height() - y_offset - self.sizeHint().height()

        self._target_pos = QPoint(x, y)
        self._start_pos = QPoint(parent.width() + 10, y)
        self.move(self._start_pos)

    def _animate_in(self):
        """Slide-in animation from right."""
        self._slide_anim = QPropertyAnimation(self, b'pos')
        self._slide_anim.setDuration(300)
        self._slide_anim.setStartValue(self._start_pos)
        self._slide_anim.setEndValue(self._target_pos)
        self._slide_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._slide_anim.start()

    def _dismiss(self):
        """Dismiss the toast with a slide-out animation."""
        if self._dismissed:
            return
        self._dismissed = True

        parent = self.parentWidget()
        if parent:
            parent_id = id(parent)
            active = ToastNotification._active_toasts.get(parent_id, [])
            if self in active:
                active.remove(self)
            # Reposition remaining toasts
            self._reposition_siblings(parent_id)

        # Slide out animation
        self._dismiss_anim = QPropertyAnimation(self, b'pos')
        self._dismiss_anim.setDuration(250)
        self._dismiss_anim.setStartValue(self.pos())
        end_pos = QPoint(self.pos().x() + 370, self.pos().y())
        self._dismiss_anim.setEndValue(end_pos)
        self._dismiss_anim.setEasingCurve(QEasingCurve.Type.InCubic)
        self._dismiss_anim.finished.connect(self.deleteLater)
        self._dismiss_anim.start()

    @staticmethod
    def _reposition_siblings(parent_id):
        """Reposition remaining active toasts after one is dismissed."""
        active = ToastNotification._active_toasts.get(parent_id, [])
        if not active:
            return

        parent = active[0].parentWidget() if active else None
        if not parent:
            return

        margin_right = 20
        margin_bottom = 20
        spacing = 8

        y_offset = margin_bottom
        for toast in active:
            if toast._dismissed:
                continue
            x = parent.width() - toast.width() - margin_right
            y = parent.height() - y_offset - toast.sizeHint().height()
            target = QPoint(x, y)

            # Animate to new position
            anim = QPropertyAnimation(toast, b'pos')
            anim.setDuration(200)
            anim.setStartValue(toast.pos())
            anim.setEndValue(target)
            anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            # Store reference to prevent garbage collection
            toast._reposition_anim = anim
            anim.start()

            y_offset += toast.sizeHint().height() + spacing


def show_toast(parent, message: str, toast_type: str = 'info', duration: int = 3000):
    """Convenience function to create and show a toast notification.

    Args:
        parent: Parent widget for the toast.
        message: The message text to display.
        toast_type: One of 'info', 'success', 'warning', 'error'.
        duration: Auto-dismiss time in milliseconds. 0 for no auto-dismiss.

    Returns:
        The created ToastNotification instance.
    """
    toast = ToastNotification(parent, message, toast_type, duration)
    toast.show()
    return toast
