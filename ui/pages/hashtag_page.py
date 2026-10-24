from ui.pages.base_page import BasePage


class HashtagPage(BasePage):
    title = "Hashtag"
    subtitle = "Like, comment on and follow posts found through a hashtag."
    icon = "fa5s.hashtag"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.add_placeholder()
