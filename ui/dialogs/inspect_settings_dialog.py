from PySide6.QtWidgets import (QDialog, QDialogButtonBox, QGridLayout, QLabel, QLineEdit, QPushButton,
                               QVBoxLayout)

from ui.widgets.card import Card
from ui.widgets.form import FormField
from utils.utils import Utils

# What the bots use today, from utils/utils.py. Editing them here is planned
# (the inspect_settings table exists) but not built yet.
SECTIONS = (
    ("Block settings", (("Block URL", Utils.BLOCK_RESTRICTION),
                        ("Block change-password URL", Utils.BLOCK_CHANGE_PASSWORD))),
    ("Scroll box", (("Scroll box XPath", Utils.SCROLL_BOX),
                    ("Scroll box close button XPath", Utils.CLOSE_BUTTON_SCROLL_BOX))),
    ("Likes link", (("Likes link XPath", Utils.LIKES_TEXT),
                    ("Second likes link XPath", Utils.SECOND_LIKES_BUTTON))),
    ("Page not available", (("Page not available text", Utils.NOT_FOUND_USER_TITLE),
                            ("User not found text", Utils.NOT_FOUND_USER_PARA))),
)


class InspectSettingsDialog(QDialog):
    """Instagram selectors and texts the bots look for. Read-only for now."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Inspect Settings")
        self.resize(1000, 560)

        banner = QLabel("<b>Coming soon.</b> Editing these isn't possible yet. These are the values the bots use "
                        "now (from utils/utils.py). When Instagram changes its page, they have to be updated there.")
        banner.setObjectName("Banner")
        banner.setWordWrap(True)

        grid = QGridLayout()
        grid.setSpacing(16)
        self.fields = {}
        for index, (title, entries) in enumerate(SECTIONS):
            card = Card(title)
            for label, value in entries:
                edit = QLineEdit(value)
                edit.setReadOnly(True)
                edit.setCursorPosition(0)
                edit.setToolTip(value)
                self.fields[label] = edit
                card.content.addWidget(FormField(label, edit))
            grid.addWidget(card, index // 2, index % 2)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        self.save_button = QPushButton("Save")
        self.save_button.setProperty("variant", "primary")
        self.save_button.setEnabled(False)
        self.save_button.setToolTip("Coming soon")
        buttons.addButton(self.save_button, QDialogButtonBox.ActionRole)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 16)
        layout.setSpacing(16)
        layout.addWidget(banner)
        layout.addLayout(grid)
        layout.addStretch(1)
        layout.addWidget(buttons)
