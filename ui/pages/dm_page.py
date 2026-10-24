from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QSpinBox

from bot_folder.dm.dm_bot import DM
from database.db import Database
from database.dm.dm import DMDB
from ui.core.db_helpers import group_id, group_name
from ui.pages.job_page import JobPage, limit_arg
from ui.widgets import confirm
from ui.widgets.card import Card
from ui.widgets.form import FormField
from ui.widgets.user_list import UserList


class DmPage(JobPage):
    title = "DM"
    subtitle = "Send a direct message to the users in a distribution list."
    icon = "fa5s.envelope"
    kind = "DM"
    run_text = "Send messages"

    def __init__(self, jobs=None, parent=None):
        super().__init__(jobs, parent)
        self._groups = []

        recipients = Card("Recipients")
        self.list_combo = QComboBox()
        self.list_combo.setMinimumWidth(240)
        self.list_combo.currentIndexChanged.connect(lambda _index: self.reload_members())
        self.list_field = FormField("Distribution list", self.list_combo)
        self.no_lists_label = QLabel("This account has no distribution lists yet. Create one in "
                                     "Settings > Distribution lists, then save users to it while following.")
        self.no_lists_label.setProperty("muted", True)
        self.no_lists_label.setWordWrap(True)
        self.members = UserList()
        self.members.setMinimumHeight(220)
        self.members.list.itemSelectionChanged.connect(self._update_member_buttons)
        self.remove_member_button = QPushButton("Remove user")
        self.remove_member_button.setProperty("variant", "danger")
        self.remove_member_button.clicked.connect(self._remove_member)
        self.clear_list_button = QPushButton("Clear list")
        self.clear_list_button.setProperty("variant", "danger")
        self.clear_list_button.clicked.connect(self._clear_list)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(self.remove_member_button)
        row.addWidget(self.clear_list_button)
        recipients.content.addWidget(self.list_field)
        recipients.content.addWidget(self.no_lists_label)
        recipients.content.addWidget(self.members)
        recipients.content.addLayout(row)

        message = Card("Message")
        self.message_edit = QPlainTextEdit()
        self.message_edit.setPlaceholderText("Hi! Thanks for following…")
        self.message_edit.setFixedHeight(120)
        self.char_count = QLabel()
        self.char_count.setProperty("muted", True)
        self.message_edit.textChanged.connect(self._update_char_count)
        self.message_field = FormField("Text", self.message_edit)
        self.limit_spin = QSpinBox()
        self.limit_spin.setRange(0, 100000)
        self.limit_spin.setSpecialValueText("No limit")
        message.content.addWidget(self.message_field)
        message.content.addWidget(self.char_count)
        message.content.addWidget(FormField("Send at most", self.limit_spin,
                                            "Each user gets the message once, then leaves the list."))

        followers = Card("Message my followers")
        followers.content.addWidget(QLabel("Send one message to everyone who follows this account."))
        note = QLabel("Not working yet: the bot side of this feature is broken (known issue #14).")
        note.setProperty("muted", True)
        followers_edit = QPlainTextEdit()
        followers_edit.setFixedHeight(80)
        followers_edit.setEnabled(False)
        followers_button = QPushButton("Send to my followers")
        followers_button.setEnabled(False)
        followers_row = QHBoxLayout()
        followers_row.addWidget(note, 1)
        followers_row.addWidget(followers_button)
        followers.content.addWidget(followers_edit)
        followers.content.addLayout(followers_row)

        for card in (self.account_card(), recipients, message, self.run_card(), followers):
            self.body_layout.addWidget(card)

        self.validator.add(self.list_field, self._check_recipients, self.list_combo.currentIndexChanged)
        self.validator.add(self.message_field, lambda: None if self.message().strip() else "Write a message",
                           self.message_edit.textChanged)
        self._update_char_count()
        self.finish_form()

    def message(self):
        return self.message_edit.toPlainText()

    def _check_recipients(self):
        if not self._groups:
            return "This account has no distribution lists yet"
        if not self.members.users():
            return "This list is empty"
        return None

    # ---------- Lists ----------

    def on_account_changed(self, row):
        self._groups = Database().get_distribution_lists_by_username(self.username()) if row else []
        self.list_combo.blockSignals(True)
        self.list_combo.clear()
        for group in self._groups:
            self.list_combo.addItem(group_name(group), group_id(group))
        self.list_combo.blockSignals(False)
        self.list_combo.setEnabled(bool(self._groups))
        self.no_lists_label.setVisible(not self._groups)
        self.reload_members()

    def on_account_job_finished(self, job):
        # the bot removes each user it messaged from the list
        self.reload_members()

    def reload_members(self):
        name = self.list_combo.currentText()
        # get_users_from_dm_users returns (username,) tuples
        users = Database().get_users_from_dm_users(name, self.username()) if name else []
        self.members.set_users([user[0] for user in users])
        self._update_member_buttons()
        self.validator.revalidate()

    def _update_member_buttons(self):
        self.remove_member_button.setEnabled(self.members.selected_user() is not None)
        self.clear_list_button.setEnabled(bool(self.members.users()))

    def _remove_member(self):
        name = self.members.selected_user()
        if not name or not confirm.ask(self, "Remove user", "Remove @{} from the list \"{}\"?".format(
                name, self.list_combo.currentText()), "Remove"):
            return
        DMDB().remove_dm_user_from_list(name, self.list_combo.currentData())
        self.reload_members()

    def _clear_list(self):
        users = self.members.users()
        if not confirm.ask(self, "Clear list", "Remove all {} users from the list \"{}\"?".format(
                len(users), self.list_combo.currentText()), "Clear list"):
            return
        group = self.list_combo.currentData()
        for name in users:
            DMDB().remove_dm_user_from_list(name, group)
        self.reload_members()

    def _update_char_count(self):
        count = len(self.message())
        self.char_count.setText("{} character{}".format(count, "" if count == 1 else "s"))

    # ---------- Run ----------

    def run_job(self):
        username, password, proxy = self.login()
        message = self.message()
        list_name = self.list_combo.currentText()
        list_id = self.list_combo.currentData()
        account = self.account_id()
        limit = limit_arg(self.limit_spin.value())
        is_schedule = self.is_schedule()

        def run(bot):
            # read the list when the job starts, so a scheduled job gets the current members
            dm_users = Database().get_users_from_dm_users(list_name, username)
            return bot.send_message_to_distribution_group(message, dm_users, list_name, is_schedule, True, account,
                                                          list_id, limit)

        self.submit("\"{}\" · {} users".format(list_name, len(self.members.users())),
                    make_bot=lambda: DM(username, password, True, proxy), run=run)
