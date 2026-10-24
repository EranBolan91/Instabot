import qtawesome as qta
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QAbstractItemView, QLabel, QLineEdit, QListWidget, QVBoxLayout, QWidget

from ui.theme.palette import color


class UserList(QWidget):
    """A list of usernames with a search box and a count ("12 users", "3 of 12 users")."""

    user_activated = Signal(str)  # double-click or Enter

    def __init__(self, noun="users", parent=None):
        super().__init__(parent)
        self._noun = noun
        self._users = []

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search")
        self.search.setClearButtonEnabled(True)
        self.search.addAction(qta.icon("fa5s.search", color=color("muted")), QLineEdit.LeadingPosition)
        self.list = QListWidget()
        self.list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.list.setUniformItemSizes(True)
        self.count_label = QLabel()
        self.count_label.setProperty("muted", True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addWidget(self.search)
        layout.addWidget(self.list, 1)
        layout.addWidget(self.count_label)

        self.search.textChanged.connect(self._refresh)
        self.list.itemActivated.connect(lambda item: self.user_activated.emit(item.text()))
        self._refresh()

    def set_users(self, users):
        self._users = list(users)
        self._refresh()

    def users(self):
        return list(self._users)

    def visible_users(self):
        return [self.list.item(i).text() for i in range(self.list.count())]

    def selected_user(self):
        item = self.list.currentItem()
        return item.text() if item is not None and item.isSelected() else None

    def remove_user(self, username):
        if username in self._users:
            self._users.remove(username)
            self._refresh()

    def clear(self):
        self.set_users([])

    def _refresh(self):
        wanted = self.search.text().strip().lower()
        shown = [user for user in self._users if wanted in user.lower()]
        self.list.clear()
        self.list.addItems(shown)
        total = len(self._users)
        noun = self._noun[:-1] if total == 1 else self._noun
        if len(shown) == total:
            self.count_label.setText("{} {}".format(total, noun))
        else:
            self.count_label.setText("{} of {} {}".format(len(shown), total, noun))
