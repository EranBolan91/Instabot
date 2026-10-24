from PySide6.QtWidgets import QLabel, QScrollArea, QVBoxLayout, QWidget

from ui.core.db_helpers import account_username
from ui.widgets.card import Card


class BasePage(QWidget):
    """Common frame for the sidebar pages: title, subtitle and a scrollable body.

    Subclasses set ``title``, ``subtitle`` and ``icon`` (a qtawesome name used
    by the sidebar) and add their cards to ``self.body_layout``.
    """

    title = ""
    subtitle = ""
    icon = ""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.account = None
        self._placeholder_account = None

        title_label = QLabel(self.title)
        title_label.setObjectName("PageTitle")
        subtitle_label = QLabel(self.subtitle)
        subtitle_label.setObjectName("PageSubtitle")
        subtitle_label.setWordWrap(True)

        self.body = QWidget()
        self.body.setObjectName("PageBody")
        self.body_layout = QVBoxLayout(self.body)
        self.body_layout.setContentsMargins(0, 16, 0, 0)
        self.body_layout.setSpacing(16)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.body)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 16)
        layout.setSpacing(4)
        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)
        layout.addWidget(scroll, 1)

    def set_account(self, row):
        """Called by MainWindow whenever the header account changes."""
        self.account = row
        if self._placeholder_account is not None:
            self._placeholder_account.setText(
                "Selected account: @{}".format(account_username(row)) if row else "No account selected")

    # Temporary content until the page is rebuilt (UI_MIGRATION.md, phase 4).
    def add_placeholder(self):
        card = Card("Coming soon")
        text = QLabel("This page is being rebuilt. Until it's ready, the old window still works: "
                      "run <code>python main_tk.py</code>.")
        text.setWordWrap(True)
        self._placeholder_account = QLabel("No account selected")
        self._placeholder_account.setProperty("muted", True)
        card.content.addWidget(text)
        card.content.addWidget(self._placeholder_account)
        self.body_layout.addWidget(card)
        self.body_layout.addStretch(1)
