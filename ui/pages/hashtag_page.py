from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QSpinBox

from bot_folder.hash_tag.hash_tag_bot import HashTagBot
from ui.core import validators
from ui.pages.job_page import JobPage
from ui.widgets.card import Card
from ui.widgets.form import FormField
from ui.widgets.post_actions import PostActions


class HashtagPage(JobPage):
    title = "Hashtag"
    subtitle = "Like, comment on and follow posts found through a hashtag."
    icon = "fa5s.hashtag"
    kind = "HashTag"
    run_text = "Run hashtag job"

    def __init__(self, jobs=None, parent=None):
        super().__init__(jobs, parent)

        search = Card("Posts")
        self.hashtag_edit = QLineEdit()
        self.hashtag_edit.setPlaceholderText("e.g. sunset")
        self.posts_spin = QSpinBox()
        self.posts_spin.setRange(1, 10000)
        self.posts_spin.setValue(20)
        self.hashtag_field = FormField("Hashtag", self.hashtag_edit, "With or without the #.")
        row = QHBoxLayout()
        row.setSpacing(16)
        row.addWidget(self.hashtag_field, 2, Qt.AlignTop)
        row.addWidget(FormField("Number of posts", self.posts_spin), 1, Qt.AlignTop)
        search.content.addLayout(row)

        actions = Card("Actions")
        self.actions = PostActions()
        actions.content.addWidget(self.actions)

        for card in (self.account_card(), search, actions, self.run_card()):
            self.body_layout.addWidget(card)

        self.validator.add(self.hashtag_field, lambda: validators.hashtag(self.hashtag_edit.text()),
                           self.hashtag_edit.textChanged)
        self.validator.add(self.actions.actions_field, self.actions.actions_error, self.actions.like_check.toggled,
                           self.actions.follow_check.toggled, self.actions.comment_check.toggled)
        self.validator.add(self.actions.comments_field, self.actions.comments_error,
                           self.actions.comment_input.changed, self.actions.comment_check.toggled)
        self.finish_form()

    def on_account_changed(self, row):
        self.actions.set_account(row)

    def hashtag(self):
        return self.hashtag_edit.text().strip().lstrip("#")

    def run_job(self):
        username, password, proxy = self.login()
        hashtag = self.hashtag()
        # the old tab passed the amount as text; the bot converts it with int()
        amount = str(self.posts_spin.value())
        like, comment, follow = self.actions.like(), self.actions.comment(), self.actions.follow()
        split_comment = self.actions.split_comment()
        distribution = int(self.actions.distribution.is_checked())
        group_id, group_name = self.actions.distribution.selected_group()
        is_schedule = self.is_schedule()

        self.submit(
            "#{} · {} posts · {}".format(hashtag, amount, self.actions.describe()),
            make_bot=lambda: HashTagBot(username, password, False, proxy),
            run=lambda bot: bot.search_hash_tag(hashtag, amount, like, comment, follow, split_comment, distribution,
                                                group_name, group_id, is_schedule))
