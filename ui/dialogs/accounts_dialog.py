import qtawesome as qta
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QAbstractItemView, QDialog, QDialogButtonBox, QHBoxLayout, QHeaderView, QLabel,
                               QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout)

from database.db import Database
from ui.core import validators
from ui.core.db_helpers import (account_created, account_id, account_last_login, account_name, account_password,
                                account_phone, account_username)
from ui.theme.palette import color
from ui.widgets import confirm
from ui.widgets.card import Card
from ui.widgets.form import FormField, FormValidator
from ui.widgets.toast import Toast

COLUMNS = ("Username", "Name", "Phone", "Created", "Last login")


class AccountsDialog(QDialog):
    """Add, edit and delete the Instagram accounts the bots log in with.

    Passwords are never shown in the table.
    """

    accounts_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Accounts")
        self.resize(1000, 560)
        self._rows = []
        self._editing_row = None  # the accounts row being edited, or None when adding

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 16)
        layout.setSpacing(16)
        columns = QHBoxLayout()
        columns.setSpacing(16)
        columns.addWidget(self._build_table_card(), 3)
        columns.addWidget(self._build_form_card(), 2)
        layout.addLayout(columns, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.toast = Toast(self)
        self._reload()

    # ---------- Building ----------

    def _build_table_card(self):
        card = Card("Your accounts")
        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.verticalHeader().hide()
        self.table.verticalHeader().setDefaultSectionSize(34)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.table.itemSelectionChanged.connect(self._update_buttons)
        self.table.doubleClicked.connect(lambda _index: self._edit_selected())

        self.empty_label = QLabel("No accounts yet. Add one with the form on the right.")
        self.empty_label.setProperty("muted", True)

        self.edit_button = QPushButton("Edit")
        self.edit_button.clicked.connect(self._edit_selected)
        self.delete_button = QPushButton("Delete")
        self.delete_button.setProperty("variant", "danger")
        self.delete_button.clicked.connect(self._delete_selected)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(self.edit_button)
        row.addWidget(self.delete_button)

        card.content.addWidget(self.table, 1)
        card.content.addWidget(self.empty_label)
        card.content.addLayout(row)
        return card

    def _build_form_card(self):
        self.form_card = Card("Add account")

        self.name_edit = QLineEdit()
        self.phone_edit = QLineEdit()
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Instagram username, without @")
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.reveal_action = self.password_edit.addAction(qta.icon("fa5s.eye", color=color("muted")),
                                                          QLineEdit.TrailingPosition)
        self.reveal_action.setToolTip("Show password")
        self.reveal_action.triggered.connect(self._toggle_password)

        self.validator = FormValidator(self)
        fields = (
            (FormField("Username *", self.username_edit), self._check_username),
            (FormField("Password *", self.password_edit), self._check_password),
            (FormField("Name", self.name_edit), lambda: self._check_edit_text(self.name_edit, "Name")),
            (FormField("Phone", self.phone_edit), lambda: self._check_edit_text(self.phone_edit, "Phone")),
        )
        for field, check in fields:
            self.validator.add(field, check, field.widget.textChanged)
            self.form_card.content.addWidget(field)
        self.username_field = fields[0][0]
        self.password_field = fields[1][0]
        self.form_card.content.addStretch(1)

        self.save_button = QPushButton("Add account")
        self.save_button.setProperty("variant", "primary")
        self.save_button.clicked.connect(self._save)
        self.cancel_edit_button = QPushButton("Cancel")
        self.cancel_edit_button.clicked.connect(self._stop_editing)
        self.cancel_edit_button.hide()
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(self.cancel_edit_button)
        row.addWidget(self.save_button)
        self.form_card.content.addLayout(row)

        self.validator.bind(self.save_button)
        return self.form_card

    # ---------- Checks ----------

    def _check_username(self):
        username = self.username_edit.text().strip()
        others = [account_username(row) for row in self._rows if row is not self._editing_row]
        return validators.first_error(
            validators.required(username, "Username"),
            validators.no_spaces(username, "Username"),
            # deleting an account looks it up by username with formatted SQL
            validators.no_apostrophe(username, "Username"),
            validators.unique(username, others, "An account with this username"))

    def _check_password(self):
        password = self.password_edit.text()
        return validators.first_error(
            validators.required(password, "Password"),
            self._check_edit_text(self.password_edit, "Password"))

    def _check_edit_text(self, edit, label):
        # Adding uses a safe query; saving an edit pastes the values into the SQL.
        if self._editing_row is not None and "'" in edit.text():
            return "{} can't contain an apostrophe (') when editing. Delete the account and add it again.".format(label)
        return None

    # ---------- Actions ----------

    def _save(self):
        if not self.validator.touch_all():
            return
        name = self.name_edit.text().strip()
        phone = self.phone_edit.text().strip()
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        database = Database()
        if self._editing_row is None:
            database.save_account(name, phone, username, password)
            message = "Account @{} added".format(username)
        else:
            if not database.update_account(account_id(self._editing_row), name, phone, username, password):
                self.toast.show_message("Couldn't save @{}. See the log for details.".format(username), "error")
                return
            message = "Account @{} saved".format(username)
        self._stop_editing()
        self._reload(select_username=username)
        self.accounts_changed.emit()
        self.toast.show_message(message, "success")

    def _edit_selected(self):
        row = self._selected_row()
        if row is None:
            return
        self._editing_row = row
        self.form_card.title_label.setText("Edit @{}".format(account_username(row)))
        self.save_button.setText("Save changes")
        self.cancel_edit_button.show()
        self.name_edit.setText(account_name(row) or "")
        self.phone_edit.setText(account_phone(row) or "")
        self.username_edit.setText(account_username(row))
        self.password_edit.setText(account_password(row))
        self.validator.reset()
        self.username_edit.setFocus()

    def _stop_editing(self):
        self._editing_row = None
        self.form_card.title_label.setText("Add account")
        self.save_button.setText("Add account")
        self.cancel_edit_button.hide()
        for edit in (self.name_edit, self.phone_edit, self.username_edit, self.password_edit):
            edit.clear()
        self.validator.reset()

    def _delete_selected(self):
        row = self._selected_row()
        if row is None:
            return
        username = account_username(row)
        if not confirm.ask(self, "Delete account",
                           "Delete @{} from Instabot?\n\nThis only removes it from this app, not from Instagram. "
                           "Its unfollow list and distribution lists stay in the database.".format(username)):
            return
        if not Database().delete_account(username):
            self.toast.show_message("Couldn't delete @{}. See the log for details.".format(username), "error")
            return
        if self._editing_row is not None and account_id(self._editing_row) == account_id(row):
            self._stop_editing()
        self._reload()
        self.accounts_changed.emit()
        self.toast.show_message("Account @{} deleted".format(username), "success")

    def _toggle_password(self):
        hidden = self.password_edit.echoMode() == QLineEdit.Password
        self.password_edit.setEchoMode(QLineEdit.Normal if hidden else QLineEdit.Password)
        self.reveal_action.setIcon(qta.icon("fa5s.eye-slash" if hidden else "fa5s.eye", color=color("muted")))
        self.reveal_action.setToolTip("Hide password" if hidden else "Show password")

    # ---------- Table ----------

    def _reload(self, select_username=None):
        self._rows = Database().get_accounts()
        self.table.setRowCount(len(self._rows))
        for r, row in enumerate(self._rows):
            values = (account_username(row), account_name(row), account_phone(row), account_created(row),
                      account_last_login(row) or "Never")
            for c, value in enumerate(values):
                self.table.setItem(r, c, QTableWidgetItem(str(value or "")))
            if account_username(row) == select_username:
                self.table.selectRow(r)
        self.table.setVisible(bool(self._rows))
        self.empty_label.setVisible(not self._rows)
        self._update_buttons()
        self.validator.revalidate()

    def _selected_row(self):
        selected = self.table.selectionModel().selectedRows()
        return self._rows[selected[0].row()] if selected else None

    def _update_buttons(self):
        has_selection = self._selected_row() is not None
        self.edit_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)
