from ui.pages.base_page import BasePage


class CombinationPage(BasePage):
    title = "Combination"
    subtitle = "Follow users who liked a post, then unfollow them in cycles."
    icon = "fa5s.layer-group"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.add_placeholder()
