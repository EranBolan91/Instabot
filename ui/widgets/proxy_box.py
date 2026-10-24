from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QSpinBox, QVBoxLayout, QWidget

from ui.core import validators

NOT_APPLIED_TEXT = "Optional. Known issue: the bots don't use the proxy yet."


class ProxyBox(QWidget):
    """Proxy host + port. Both or neither."""

    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.host_edit = QLineEdit()
        self.host_edit.setPlaceholderText("Proxy host")
        self.port_spin = QSpinBox()
        self.port_spin.setRange(0, 65535)
        # 0 means "no port": show the word "Port" instead of a 0
        self.port_spin.setSpecialValueText("Port")
        self.port_spin.setMinimumWidth(100)
        self.note = QLabel(NOT_APPLIED_TEXT)
        self.note.setProperty("muted", True)
        self.error_label = QLabel()
        self.error_label.setObjectName("FieldError")
        self.error_label.hide()

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(self.host_edit, 1)
        row.addWidget(self.port_spin)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addLayout(row)
        layout.addWidget(self.error_label)
        layout.addWidget(self.note)

        self.host_edit.textChanged.connect(self._update)
        self.port_spin.valueChanged.connect(self._update)

    def host(self):
        return self.host_edit.text().strip()

    def port(self):
        return self.port_spin.value()

    def error(self):
        return validators.proxy_pair(self.host(), self.port())

    def proxy_dict(self):
        """The dict the bots take: {"proxy": host, "port": port}, as strings like the old tabs."""
        return {"proxy": self.host(), "port": str(self.port()) if self.port() else ""}

    def _update(self):
        error = self.error()
        for widget in (self.host_edit, self.port_spin):
            widget.setProperty("invalid", bool(error))
            widget.style().unpolish(widget)
            widget.style().polish(widget)
        self.error_label.setText(error or "")
        self.error_label.setVisible(bool(error))
        self.changed.emit()
