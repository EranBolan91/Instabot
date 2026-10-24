import qtawesome as qta
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QToolButton, QWidget

from database.db import Database
from ui.core.db_helpers import account_username
from ui.theme.palette import color

NO_ACCOUNTS_TEXT = "No accounts yet: add one in Accounts"


class AccountPicker(QWidget):
    """Header combo that picks the account every page works with.

    Replaces the "Choose user" dropdown each old tab had. Emits
    ``account_changed`` with the full ``accounts`` row, or ``None`` when
    there are no accounts.
    """

    account_changed = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows = []

        self.combo = QComboBox()
        self.combo.setMinimumWidth(220)
        self.combo.setToolTip("Account used by every page")

        self.refresh_button = QToolButton()
        self.refresh_button.setIcon(qta.icon("fa5s.sync-alt", color=color("muted"), color_active=color("text")))
        self.refresh_button.setToolTip("Reload accounts")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addWidget(self.combo)
        layout.addWidget(self.refresh_button)

        self.combo.currentIndexChanged.connect(self._on_index_changed)
        self.refresh_button.clicked.connect(lambda: self.refresh())

    def refresh(self, prefer_username=None):
        """Reload accounts from the DB, keeping the current (or preferred) selection."""
        keep = prefer_username or self.current_username()
        self._rows = Database().get_accounts()

        self.combo.blockSignals(True)
        self.combo.clear()
        index = 0
        for i, row in enumerate(self._rows):
            self.combo.addItem("@" + account_username(row))
            if account_username(row) == keep:
                index = i
        if self._rows:
            self.combo.setCurrentIndex(index)
        else:
            self.combo.addItem(NO_ACCOUNTS_TEXT)
        self.combo.setEnabled(bool(self._rows))
        self.combo.blockSignals(False)

        # always emit, so pages reload account data even if the selection stayed
        self.account_changed.emit(self.current_account())

    def current_account(self):
        index = self.combo.currentIndex()
        if self._rows and 0 <= index < len(self._rows):
            return self._rows[index]
        return None

    def current_username(self):
        row = self.current_account()
        return account_username(row) if row else None

    def select_username(self, username):
        for i, row in enumerate(self._rows):
            if account_username(row) == username:
                self.combo.setCurrentIndex(i)
                return True
        return False

    def _on_index_changed(self, _index):
        self.account_changed.emit(self.current_account())
