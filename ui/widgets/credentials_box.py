from PySide6.QtWidgets import QGridLayout, QLabel, QLineEdit, QWidget

from ui.core.db_helpers import account_password, account_username


class CredentialsBox(QWidget):
    """Read-only username and masked password of the account a job will use.

    The account is picked in the header; pages show this so it's clear who
    the job runs as. The password can't be revealed or copied here.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.username_edit = QLineEdit()
        self.username_edit.setReadOnly(True)
        self.username_edit.setPlaceholderText("No account selected")
        self.password_edit = QLineEdit()
        self.password_edit.setReadOnly(True)
        self.password_edit.setEchoMode(QLineEdit.Password)

        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(8)
        for row, (text, edit) in enumerate((("Username", self.username_edit), ("Password", self.password_edit))):
            label = QLabel(text)
            label.setProperty("muted", True)
            layout.addWidget(label, row, 0)
            layout.addWidget(edit, row, 1)
        layout.setColumnStretch(1, 1)

    def set_account(self, row):
        self.username_edit.setText(account_username(row) if row else "")
        self.password_edit.setText(account_password(row) if row else "")

    def username(self):
        return self.username_edit.text()

    def password(self):
        return self.password_edit.text()

    def has_account(self):
        return bool(self.username() and self.password())
