from PySide6.QtCore import QEvent, QTimer
from PySide6.QtWidgets import QLabel

MARGIN = 16


class Toast(QLabel):
    """Small message in the bottom-right corner of its parent that hides by itself.

    ``kind`` is "info", "success", "warning" or "error" (styled in dark.qss).
    Click it to dismiss it early.
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName("Toast")
        self.setWordWrap(True)
        self.setMaximumWidth(420)
        self.hide()

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)
        parent.installEventFilter(self)

    def show_message(self, text, kind="info", msec=4500):
        self.setProperty("kind", kind)
        # re-apply the stylesheet so the new "kind" color is used
        self.style().unpolish(self)
        self.style().polish(self)
        self.setText(text)
        self.adjustSize()
        self._place()
        self.show()
        self.raise_()
        self._timer.start(msec)

    def mousePressEvent(self, event):
        self.hide()

    def eventFilter(self, watched, event):
        if watched is self.parent() and event.type() == QEvent.Resize and self.isVisible():
            self._place()
        return False

    def _place(self):
        parent = self.parentWidget()
        self.move(parent.width() - self.width() - MARGIN, parent.height() - self.height() - MARGIN)
