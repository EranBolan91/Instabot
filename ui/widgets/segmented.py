from PySide6.QtCore import Signal
from PySide6.QtWidgets import QButtonGroup, QHBoxLayout, QPushButton, QWidget


class Segmented(QWidget):
    """A row of joined toggle buttons where exactly one is selected."""

    changed = Signal(int)

    def __init__(self, options, parent=None):
        super().__init__(parent)
        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        for index, text in enumerate(options):
            button = QPushButton(text)
            button.setObjectName("Segment")
            button.setCheckable(True)
            position = "first" if index == 0 else "last" if index == len(options) - 1 else "middle"
            button.setProperty("segment", position)
            self.group.addButton(button, index)
            layout.addWidget(button)
        layout.addStretch(1)
        self.group.button(0).setChecked(True)
        self.group.idClicked.connect(self.changed.emit)

    def index(self):
        return self.group.checkedId()

    def set_index(self, index):
        self.group.button(index).setChecked(True)
        self.changed.emit(index)
