from PySide6.QtCore import Signal
from PySide6.QtWidgets import QCheckBox, QComboBox, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from database.db import Database
from ui.core.db_helpers import account_username, group_id, group_name

NO_LISTS_TEXT = "This account has no distribution lists yet. Create one in Settings > Distribution lists."


class DistributionPicker(QWidget):
    """"Save followed users to a distribution list" checkbox + the account's lists.

    Pages call set_available(False) while FOLLOW is off, like the old tabs.
    """

    changed = Signal()

    def __init__(self, text="Save followed users to a distribution list", parent=None):
        super().__init__(parent)
        self._groups = []
        self._available = True

        self.check = QCheckBox(text)
        self.combo = QComboBox()
        self.combo.setMinimumWidth(200)
        self.hint = QLabel(NO_LISTS_TEXT)
        self.hint.setProperty("muted", True)
        self.hint.setWordWrap(True)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(self.check)
        row.addWidget(self.combo)
        row.addStretch(1)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addLayout(row)
        layout.addWidget(self.hint)

        self.check.toggled.connect(self._update)
        self.combo.currentIndexChanged.connect(lambda _index: self.changed.emit())
        self._update()

    def set_account(self, row):
        self._groups = Database().get_distribution_lists_by_username(account_username(row)) if row else []
        self.combo.blockSignals(True)
        self.combo.clear()
        for group in self._groups:
            self.combo.addItem(group_name(group), group_id(group))
        self.combo.blockSignals(False)
        self._update()

    def set_available(self, available):
        self._available = available
        self._update()

    def is_checked(self):
        """True when followed users will be saved to the selected list."""
        return self.check.isEnabled() and self.check.isChecked()

    def selected_group(self):
        """(group id, group name), or ("", "") when not saving, like the old tabs passed."""
        if not self.is_checked() or self.combo.currentIndex() < 0:
            return "", ""
        return self.combo.currentData(), self.combo.currentText()

    def _update(self):
        has_groups = bool(self._groups)
        self.check.setEnabled(self._available and has_groups)
        self.combo.setEnabled(self._available and has_groups and self.check.isChecked())
        self.combo.setVisible(has_groups)
        self.hint.setVisible(not has_groups)
        self.changed.emit()
