from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QCheckBox, QGridLayout, QHBoxLayout, QLabel, QPushButton, QSpinBox

from bot_folder.followers.followers_bot import FollowersBot
from database.db import Database
from ui.pages.job_page import JobPage, limit_arg
from ui.widgets import confirm
from ui.widgets.card import Card
from ui.widgets.form import FormField
from ui.widgets.user_list import UserList

KIND = "Unfollow"


def open_profile(username):
    """Opens the profile in the user's own browser (the old SEARCH button)."""
    QDesktopServices.openUrl(QUrl("https://www.instagram.com/{}/".format(username)))


def _button(text, variant=None):
    button = QPushButton(text)
    if variant:
        button.setProperty("variant", variant)
    return button


class FollowersPage(JobPage):
    """The unfollow center (the old "Followers" tab)."""

    title = "Unfollow"
    subtitle = "Find who doesn't follow you back, and unfollow the users the bot followed."
    icon = "fa5s.user-minus"
    kind = KIND
    run_text = "Find who doesn't follow me back"

    def __init__(self, jobs=None, parent=None):
        super().__init__(jobs, parent)
        self._check_job_id = None  # the running "who doesn't follow me back" job

        # 1. Who doesn't follow me back
        check = Card("Who doesn't follow me back")
        check.content.addWidget(self._note("Compares your following and followers lists. Chrome opens while it "
                                           "runs; the results appear here."))
        self.results = UserList()
        self.results.setMinimumHeight(220)
        self.results.user_activated.connect(open_profile)
        self.results.list.itemSelectionChanged.connect(self._update_buttons)
        self.open_profile_button = _button("Open profile")
        self.open_profile_button.clicked.connect(lambda: open_profile(self.results.selected_user()))
        self.unfollow_results_button = _button("Unfollow all", "danger")
        self.unfollow_results_button.clicked.connect(self._unfollow_results)
        row = QHBoxLayout()
        row.addWidget(self.run_button)
        row.addStretch(1)
        row.addWidget(self.open_profile_button)
        row.addWidget(self.unfollow_results_button)
        check.content.addWidget(self.results)
        check.content.addLayout(row)

        # 2. Users the bot followed (the unfollow table)
        followed = Card("Users the bot followed")
        followed.content.addWidget(self._note("Everyone the bot followed for this account, from any page."))
        self.followed = UserList()
        self.followed.setMinimumHeight(220)
        self.followed.list.itemSelectionChanged.connect(self._update_buttons)
        self.followed.user_activated.connect(open_profile)
        self.remove_button = _button("Remove from list", "danger")
        self.remove_button.setToolTip("Only removes the user from this list. Nobody is unfollowed.")
        self.remove_button.clicked.connect(self._remove_selected)
        self.unfollow_selected_button = _button("Unfollow selected")
        self.unfollow_selected_button.clicked.connect(self._unfollow_selected)
        self.unfollow_list_button = _button("Unfollow whole list", "danger")
        self.unfollow_list_button.clicked.connect(self._unfollow_list)
        self.unfollow_non_followers_button = _button("Unfollow only those not following back", "danger")
        self.unfollow_non_followers_button.clicked.connect(self._unfollow_non_followers)
        buttons = QHBoxLayout()
        for button in (self.remove_button, self.unfollow_selected_button):
            buttons.addWidget(button)
        buttons.addStretch(1)
        for button in (self.unfollow_list_button, self.unfollow_non_followers_button):
            buttons.addWidget(button)

        self.limit_spin = QSpinBox()
        self.limit_spin.setRange(0, 100000)
        self.limit_spin.setSpecialValueText("No limit")
        self.remove_not_found_check = QCheckBox("Remove users that no longer exist")
        self.reverse_check = QCheckBox("Newest first (reverse order)")
        options = QGridLayout()
        options.setHorizontalSpacing(24)
        options.addWidget(FormField("Unfollow at most", self.limit_spin), 0, 0, 2, 1)
        options.addWidget(self.remove_not_found_check, 0, 1)
        options.addWidget(self.reverse_check, 1, 1)
        options.setColumnStretch(2, 1)
        followed.content.addWidget(self.followed)
        followed.content.addLayout(buttons)
        followed.content.addLayout(options)

        # 3. Unfollow everyone
        danger = Card("Unfollow everyone")
        danger.setObjectName("DangerCard")
        danger.content.addWidget(self._note("Opens your own \"following\" list and unfollows everyone in it, "
                                            "not only the users the bot followed."))
        self.everyone_spin = QSpinBox()
        self.everyone_spin.setRange(1, 100000)
        self.everyone_spin.setValue(50)
        self.unfollow_everyone_button = _button("Unfollow everyone", "danger")
        self.unfollow_everyone_button.clicked.connect(self._unfollow_everyone)
        row = QHBoxLayout()
        row.addWidget(FormField("Unfollow at most", self.everyone_spin))
        row.addStretch(1)
        row.addWidget(self.unfollow_everyone_button)
        danger.content.addLayout(row)

        # the run button sits in the first card, next to its results
        settings = self.run_card(with_button=False)
        settings.title_label.setText("Run settings")
        settings.content.insertWidget(1, self._note("The schedule applies to the unfollow buttons. "
                                                    "\"Find who doesn't follow me back\" always starts right away."))

        for card in (self.account_card(), check, followed, danger, settings):
            self.body_layout.addWidget(card)

        self.validator.validity_changed.connect(lambda _valid: self._update_buttons())
        if jobs is not None:
            jobs.job_finished.connect(self._on_any_job_finished)
        self.finish_form()
        self._update_buttons()

    @staticmethod
    def _note(text):
        label = QLabel(text)
        label.setProperty("muted", True)
        label.setWordWrap(True)
        return label

    # ---------- Data ----------

    def on_account_changed(self, row):
        self.results.clear()
        self.reload_followed()

    def on_account_job_finished(self, job):
        if job.kind == KIND:
            self.reload_followed()

    def reload_followed(self):
        # unfollow rows: id, user_id, username
        rows = Database().get_unfollow_users(self.username()) if self.account else []
        self.followed.set_users([row[2] for row in rows])
        self._update_buttons()

    def _update_buttons(self):
        ready = self.validator.is_valid()
        selected = self.followed.selected_user() is not None
        has_followed = bool(self.followed.users())
        has_results = bool(self.results.users())
        self.run_button.setEnabled(ready and self._check_job_id is None)
        self.open_profile_button.setEnabled(self.results.selected_user() is not None)
        self.unfollow_results_button.setEnabled(ready and has_results)
        self.unfollow_results_button.setText("Unfollow all {}".format(len(self.results.users())) if has_results
                                             else "Unfollow all")
        self.remove_button.setEnabled(bool(self.account) and selected)
        self.unfollow_selected_button.setEnabled(ready and selected)
        self.unfollow_list_button.setEnabled(ready and has_followed)
        self.unfollow_non_followers_button.setEnabled(ready and has_followed)
        self.unfollow_everyone_button.setEnabled(ready)

    def _options(self):
        return (int(self.reverse_check.isChecked()), limit_arg(self.limit_spin.value()),
                self.remove_not_found_check.isChecked())

    # ---------- 1. Who doesn't follow me back ----------

    def run_job(self):
        username, password, proxy = self.login()

        def on_result(users):
            if users is False or users is None:
                self.notify.emit("The check didn't finish. See the log for details.", "error")
                return
            self.results.set_users(users)
            self._update_buttons()
            if users:
                self.notify.emit("{} users don't follow @{} back".format(len(users), username), "info")
            else:
                self.notify.emit("Everyone follows @{} back".format(username), "success")

        job = self.submit("find who doesn't follow back", delay_seconds=0, on_result=on_result,
                          make_bot=lambda: FollowersBot(username, password, False, proxy),
                          run=lambda bot: bot.get_unfollowers())
        self._check_job_id = job.id
        self._update_buttons()

    def _on_any_job_finished(self, job):
        if job.id == self._check_job_id:
            self._check_job_id = None
            self._update_buttons()

    def _unfollow_results(self):
        users = self.results.users()
        if not self._confirm("Unfollow {} users who don't follow @{} back?".format(len(users), self.username())):
            return
        self._submit_unfollow_users(users, from_db=0, description="{} non-followers".format(len(users)))

    # ---------- 2. Users the bot followed ----------

    def _remove_selected(self):
        name = self.followed.selected_user()
        if not name or not confirm.ask(self, "Remove from list",
                                       "Remove @{} from the list?\n\nNobody is unfollowed.".format(name), "Remove"):
            return
        Database().remove_username_from_unfollow_list(name, self.account_id())
        self.reload_followed()

    def _unfollow_selected(self):
        name = self.followed.selected_user()
        username, password, proxy = self.login()
        account = self.account_id()
        self.submit("@{}".format(name), make_bot=lambda: FollowersBot(username, password, False, proxy),
                    run=lambda bot: bot.unfollow_user(name, account))

    def _unfollow_list(self):
        users = self.followed.users()
        if not self._confirm("Unfollow the {} users the bot followed for @{}?".format(len(users), self.username())):
            return
        self._submit_unfollow_users(users, from_db=1, description="whole list · {} users".format(len(users)))

    def _unfollow_non_followers(self):
        users = self.followed.users()
        if not self._confirm("Check which of the {} users the bot followed don't follow @{} back, and unfollow "
                             "them?".format(len(users), self.username())):
            return
        username, password, proxy = self.login()
        account = self.account_id()
        reverse = self._options()[0]
        delay = self.schedule.delay_seconds()

        def on_result(not_following_back):
            # second step, like the old tab: unfollow the users found by the first one
            if not not_following_back:
                self.notify.emit("Everyone in the list follows @{} back".format(username), "success")
                return
            self._submit_unfollow_users(not_following_back, from_db=1, delay_seconds=delay,
                                        description="{} not following back".format(len(not_following_back)))

        # the check runs now; only the unfollowing itself is scheduled, as before
        self.submit("check {} users for follow-back".format(len(users)), delay_seconds=0, notify=False,
                    on_result=on_result, make_bot=lambda: FollowersBot(username, password, False, proxy),
                    run=lambda bot: bot.unfollow_users_who_not_return_follow(users, account, reverse))
        self.notify.emit("Checking which users follow @{} back…".format(username), "success")

    def _submit_unfollow_users(self, users, from_db, description, delay_seconds=None):
        username, password, proxy = self.login()
        account = self.account_id()
        reverse, limit, remove_not_found = self._options()
        users = list(users)
        self.submit(description, delay_seconds=delay_seconds,
                    make_bot=lambda: FollowersBot(username, password, False, proxy),
                    run=lambda bot: bot.unfollow_users(users, from_db, account, 1, reverse, limit, remove_not_found))

    # ---------- 3. Unfollow everyone ----------

    def _unfollow_everyone(self):
        limit = self.everyone_spin.value()
        if not self._confirm("Unfollow up to {} accounts that @{} follows?\n\nThis goes through your whole "
                             "\"following\" list, not only the users the bot followed.".format(limit, self.username()),
                             confirm_text="Unfollow everyone"):
            return
        username, password, proxy = self.login()
        self.submit("everyone · at most {}".format(limit),
                    make_bot=lambda: FollowersBot(username, password, False, proxy),
                    run=lambda bot: bot.unfollow_all_users(limit))

    def _confirm(self, text, confirm_text="Unfollow"):
        return confirm.ask(self, "Unfollow", text, confirm_text)
