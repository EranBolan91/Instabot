from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class Card(QFrame):
    """Titled surface that groups one section of a form.

    Add widgets to ``card.content`` (a QVBoxLayout).
    """

    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.setObjectName("Card")

        self.content = QVBoxLayout(self)
        self.content.setContentsMargins(16, 14, 16, 16)
        self.content.setSpacing(12)

        if title:
            self.title_label = QLabel(title)
            self.title_label.setObjectName("CardTitle")
            self.content.addWidget(self.title_label)
