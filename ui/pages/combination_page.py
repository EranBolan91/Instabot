from PySide6.QtWidgets import QGridLayout, QLabel, QLineEdit, QSpinBox

from bot_folder.combination.combination_bot import CombinationBot
from database.combination.combination import CombinationDM
from ui.core import validators
from ui.pages.job_page import JobPage
from ui.widgets.card import Card
from ui.widgets.distribution_picker import DistributionPicker
from ui.widgets.form import FormField
from ui.widgets.records_table import DATE, NUMBER, Column, RecordsTable
from ui.widgets.segmented import Segmented

HASHTAG, POST_URL = 0, 1

# combination row: id, account, url, hashtag, num_likes, num_failed_likes, num_followers,
# num_failed_followers, schedule, distribution, group_name, date, skip_users
HISTORY_COLUMNS = (Column("Date", 11, DATE), Column("Followed", 6, NUMBER), Column("Failed", 7, NUMBER),
                   Column("Skipped users", 12, NUMBER), Column("Hashtag", 3), Column("Post", 2))


def _spin(minimum, maximum, value):
    spin = QSpinBox()
    spin.setRange(minimum, maximum)
    spin.setValue(value)
    return spin


class CombinationPage(JobPage):
    title = "Combination"
    subtitle = "Follow users who liked a post, then unfollow them in cycles."
    icon = "fa5s.layer-group"
    kind = "Combination"
    run_text = "Run combination"
    # the old tab passed a hard-coded dummy proxy; the bots don't use proxies anyway
    uses_proxy = False

    def __init__(self, jobs=None, parent=None):
        super().__init__(jobs, parent)

        info = QLabel("Follows about 100 users over 12 hours, then unfollows them all, and repeats.")
        info.setObjectName("Banner")
        info.setWordWrap(True)

        source = Card("Posts")
        self.source = Segmented(("Hashtag", "Post URL"))
        self.hashtag_edit = QLineEdit()
        self.hashtag_edit.setPlaceholderText("e.g. sunset")
        self.hashtag_field = FormField("Hashtag", self.hashtag_edit, "The bot opens the hashtag's first post.")
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("https://www.instagram.com/p/…")
        self.url_field = FormField("Post or page address", self.url_edit)
        source.content.addWidget(self.source)
        source.content.addWidget(self.hashtag_field)
        source.content.addWidget(self.url_field)

        amounts = Card("How much")
        self.follow_spin = _spin(1, 10000, 100)
        self.likes_spin = _spin(0, 50, 0)
        self.skip_posts_spin = _spin(0, 1000, 0)
        self.skip_users_spin = _spin(0, 100000, 0)
        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(12)
        grid.addWidget(FormField("Users to follow", self.follow_spin), 0, 0)
        grid.addWidget(FormField("Posts to like per followed user", self.likes_spin), 0, 1)
        grid.addWidget(FormField("Skip posts", self.skip_posts_spin, "Start this many posts in."), 1, 0)
        grid.addWidget(FormField("Skip users", self.skip_users_spin,
                                 "Pass over this many users at the top of the likes list."), 1, 1)
        amounts.content.addLayout(grid)
        self.distribution = DistributionPicker()
        amounts.content.addWidget(self.distribution)

        history = Card("Past runs")
        self.history = RecordsTable(HISTORY_COLUMNS, "No runs saved yet for this account.")
        self.history.setMinimumHeight(140)
        history.content.addWidget(self.history)

        self.body_layout.addWidget(info)
        for card in (self.account_card(), source, amounts, self.run_card(), history):
            self.body_layout.addWidget(card)

        self.validator.add(self.hashtag_field, lambda: validators.hashtag(self.hashtag_edit.text())
                           if self.source.index() == HASHTAG else None, self.hashtag_edit.textChanged)
        self.validator.add(self.url_field, lambda: validators.instagram_url(
            self.url_edit.text(), "https://www.instagram.com/p/…") if self.source.index() == POST_URL else None,
            self.url_edit.textChanged)
        self.validator.watch(self.source.changed)
        self.source.changed.connect(self._on_source_changed)
        self._on_source_changed(self.source.index())
        self.finish_form()

    def _on_source_changed(self, index):
        self.hashtag_field.setVisible(index == HASHTAG)
        self.url_field.setVisible(index == POST_URL)

    def on_account_changed(self, row):
        self.distribution.set_account(row)
        self.reload_history()

    def on_account_job_finished(self, job):
        if job.kind == self.kind:
            self.reload_history()

    def reload_history(self):
        self.history.set_rows(CombinationDM().get_account_data(self.username()) if self.account else [])

    def run_job(self):
        username, password, proxy = self.login()
        # exactly one of the two, like the old tab required
        hashtag = self.hashtag_edit.text().strip().lstrip("#") if self.source.index() == HASHTAG else ""
        url = self.url_edit.text().strip() if self.source.index() == POST_URL else ""
        likes = self.likes_spin.value()
        follow = self.follow_spin.value()
        distribution = int(self.distribution.is_checked())
        group_id, group_name = self.distribution.selected_group()
        skip_posts = self.skip_posts_spin.value()
        skip_users = self.skip_users_spin.value()

        source = "#" + hashtag if hashtag else url.rstrip("/").split("/")[-1]
        # the old tab always passed 0 as "schedule"
        self.submit("{} · follow {} · like {}".format(source, follow, likes),
                    make_bot=lambda: CombinationBot(username, password, False, proxy),
                    run=lambda bot: bot.combination(hashtag, url, likes, follow, distribution, 0, group_name,
                                                    group_id, skip_posts, skip_users))
