from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QSpinBox

from bot_folder.location.location_bot import LocationBot
from ui.core import validators
from ui.pages.job_page import JobPage
from ui.widgets.card import Card
from ui.widgets.form import FormField
from ui.widgets.post_actions import PostActions


class LocationPage(JobPage):
    title = "Location"
    subtitle = "Like, comment on and follow posts from a location page."
    icon = "fa5s.map-marker-alt"
    kind = "Location"
    run_text = "Run location job"

    def __init__(self, jobs=None, parent=None):
        super().__init__(jobs, parent)

        search = Card("Posts")
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("https://www.instagram.com/explore/locations/212988663/new-york-new-york/")
        self.url_field = FormField("Location page address", self.url_edit,
                                   "Open the location on Instagram and copy the address.")
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g. New York")
        self.name_edit.setEnabled(False)
        # search_location_by_name is broken (known issue #19), so it isn't wired up
        name_field = FormField("Or search by name", self.name_edit, "Not available yet.")
        self.posts_spin = QSpinBox()
        self.posts_spin.setRange(1, 10000)
        self.posts_spin.setValue(20)
        row = QHBoxLayout()
        row.setSpacing(16)
        row.addWidget(name_field, 2, Qt.AlignTop)
        row.addWidget(FormField("Number of posts", self.posts_spin), 1, Qt.AlignTop)
        search.content.addWidget(self.url_field)
        search.content.addLayout(row)

        actions = Card("Actions")
        self.actions = PostActions()
        actions.content.addWidget(self.actions)

        for card in (self.account_card(), search, actions, self.run_card()):
            self.body_layout.addWidget(card)

        self.validator.add(self.url_field, lambda: validators.instagram_location_url(self.url_edit.text()),
                           self.url_edit.textChanged)
        self.validator.add(self.actions.actions_field, self.actions.actions_error, self.actions.like_check.toggled,
                           self.actions.follow_check.toggled, self.actions.comment_check.toggled)
        self.validator.add(self.actions.comments_field, self.actions.comments_error,
                           self.actions.comment_input.changed, self.actions.comment_check.toggled)
        self.finish_form()

    def on_account_changed(self, row):
        self.actions.set_account(row)

    def run_job(self):
        username, password, proxy = self.login()
        url = self.url_edit.text().strip()
        amount = str(self.posts_spin.value())
        like, follow, comment = self.actions.like(), self.actions.follow(), self.actions.comment()
        split_comment = self.actions.split_comment()
        distribution = int(self.actions.distribution.is_checked())
        group_id, group_name = self.actions.distribution.selected_group()
        is_schedule = self.is_schedule()
        place = url.rstrip("/").split("/")[-1]

        # note the order: this bot takes like, follow, comment (the hashtag bot takes like, comment, follow)
        self.submit(
            "{} · {} posts · {}".format(place, amount, self.actions.describe()),
            make_bot=lambda: LocationBot(username, password, False, proxy),
            run=lambda bot: bot.search_location_by_url(url, amount, like, follow, comment, split_comment,
                                                       distribution, group_name, group_id, is_schedule))
