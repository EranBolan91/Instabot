from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QSpinBox

from bot_folder.follow_followers.follow_followers_bot import FollowFollowersBot
from database.follow_followers.follow_followers import FollowFollowersDB
from ui.core import validators
from ui.pages.job_page import JobPage
from ui.widgets.card import Card
from ui.widgets.distribution_picker import DistributionPicker
from ui.widgets.form import FormField
from ui.widgets.records_table import DATE, NUMBER, Column, RecordsTable
from ui.widgets.segmented import Segmented

THEIR_FOLLOWERS, THEIR_FOLLOWING = 0, 1

# follow_followers row: id, account, url, num_follow, num_failed_follow, distribution, group_name, schedule, date, skip
HISTORY_COLUMNS = (Column("Date", 8, DATE), Column("Followed", 3, NUMBER), Column("Failed", 4, NUMBER),
                   Column("Skipped", 9, NUMBER), Column("Profile", 2))


class FollowFollowersPage(JobPage):
    title = "Follow Followers"
    subtitle = "Follow the followers of another profile, or the accounts it follows."
    icon = "fa5s.user-friends"
    kind = "Follow Followers"
    run_text = "Start following"

    def __init__(self, jobs=None, parent=None):
        super().__init__(jobs, parent)

        target = Card("Who to follow")
        self.mode = Segmented(("Their followers", "Who they follow"))
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("https://www.instagram.com/natgeo/")
        self.url_field = FormField("Profile address", self.url_edit)
        self.follow_spin = QSpinBox()
        self.follow_spin.setRange(1, 10000)
        self.follow_spin.setValue(50)
        self.skip_spin = QSpinBox()
        self.skip_spin.setRange(0, 100000)
        self.skip_field = FormField("Skip the first", self.skip_spin)
        self.distribution = DistributionPicker()
        row = QHBoxLayout()
        row.setSpacing(16)
        row.addWidget(FormField("Number of people to follow", self.follow_spin), 1, Qt.AlignTop)
        row.addWidget(self.skip_field, 1, Qt.AlignTop)
        target.content.addWidget(self.mode)
        target.content.addWidget(self.url_field)
        target.content.addLayout(row)
        target.content.addWidget(self.distribution)

        history = Card("Past runs")
        self.history = RecordsTable(HISTORY_COLUMNS, "No runs for this account yet.")
        self.history.setMinimumHeight(180)
        history.content.addWidget(self.history)

        for card in (self.account_card(), target, self.run_card(), history):
            self.body_layout.addWidget(card)

        self.validator.add(self.url_field, lambda: validators.instagram_url(
            self.url_edit.text(), "https://www.instagram.com/natgeo/"), self.url_edit.textChanged)
        self.mode.changed.connect(self._on_mode_changed)
        self._on_mode_changed(self.mode.index())
        self.finish_form()

    def _on_mode_changed(self, mode):
        # only follow_after_following uses the skip count; follow_after_followers ignores it
        following = mode == THEIR_FOLLOWING
        self.skip_spin.setEnabled(following)
        self.skip_field.message.setText("" if following else "Only used for \"Who they follow\".")
        self.skip_field.message.setVisible(not following)

    def on_account_changed(self, row):
        self.distribution.set_account(row)
        self.reload_history()

    def on_account_job_finished(self, job):
        if job.kind == self.kind:
            self.reload_history()

    def reload_history(self):
        self.history.set_rows(FollowFollowersDB().get_account_data(self.username()) if self.account else [])

    def run_job(self):
        username, password, proxy = self.login()
        url = self.url_edit.text().strip()
        count = self.follow_spin.value()
        distribution = int(self.distribution.is_checked())
        group_id, group_name = self.distribution.selected_group()
        is_schedule = self.is_schedule()
        skip = self.skip_spin.value()
        profile = url.rstrip("/").split("/")[-1]

        if self.mode.index() == THEIR_FOLLOWERS:
            description = "followers of @{} · {} users".format(profile, count)
            run = lambda bot: bot.follow_after_followers(url, username, count, distribution, group_name, group_id,
                                                         is_schedule, skip)
        else:
            description = "followed by @{} · {} users · skip {}".format(profile, count, skip)
            run = lambda bot: bot.follow_after_following(url, username, count, distribution, group_name, group_id,
                                                         is_schedule, skip)
        self.submit(description, make_bot=lambda: FollowFollowersBot(username, password, False, proxy), run=run)
