from ui.pages.base_page import BasePage


class FollowersPage(BasePage):
    title = "Unfollow"
    subtitle = "Find who doesn't follow you back, and unfollow the users the bot followed."
    icon = "fa5s.user-minus"

    def __init__(self, jobs=None, parent=None):
        super().__init__(jobs, parent)
        self.add_placeholder()
