from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QLineEdit, QVBoxLayout, QWidget

from ui.widgets.flow_layout import FlowLayout

MAX_CHIPS = 12


class CommentInput(QWidget):
    """Comma-separated comments, previewed as chips. The bot posts one at random per post."""

    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.edit = QLineEdit()
        self.edit.setPlaceholderText("Nice picture, Looking good, I like it")
        self.edit.setClearButtonEnabled(True)
        self.hint = QLabel("Separate comments with commas. Each post gets one of them at random.")
        self.hint.setProperty("muted", True)

        self.chips = QWidget()
        self.chips_layout = FlowLayout(self.chips)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addWidget(self.edit)
        layout.addWidget(self.chips)
        layout.addWidget(self.hint)

        self.edit.textChanged.connect(self._on_text_changed)
        self.chips.hide()

    def comments(self):
        """The comments as a list, trimmed, without empty ones."""
        return [comment.strip() for comment in self.edit.text().split(",") if comment.strip()]

    def set_text(self, text):
        self.edit.setText(text)

    def chip_texts(self):
        return [self.chips_layout.itemAt(i).widget().text() for i in range(self.chips_layout.count())]

    def _on_text_changed(self):
        while self.chips_layout.count():
            widget = self.chips_layout.takeAt(0).widget()
            widget.setParent(None)
            widget.deleteLater()

        comments = self.comments()
        shown = comments[:MAX_CHIPS]
        labels = list(shown)
        if len(comments) > len(shown):
            labels.append("+{} more".format(len(comments) - len(shown)))
        for text in labels:
            chip = QLabel(text)
            chip.setObjectName("Chip")
            self.chips_layout.addWidget(chip)
        self.chips.setVisible(bool(labels))
        self.changed.emit()
