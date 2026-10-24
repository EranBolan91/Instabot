from ui.pages.base_page import BasePage


class FollowFollowersPage(BasePage):
    title = "Follow Followers"
    subtitle = "Follow the followers, or the following list, of another profile."
    icon = "fa5s.user-friends"

    def __init__(self, jobs=None, parent=None):
        super().__init__(jobs, parent)
        self.add_placeholder()
