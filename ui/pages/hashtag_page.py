from ui.pages.base_page import BasePage


class HashtagPage(BasePage):
    title = "Hashtag"
    subtitle = "Like, comment on and follow posts found through a hashtag."
    icon = "fa5s.hashtag"

    def __init__(self, jobs=None, parent=None):
        super().__init__(jobs, parent)
        self.add_placeholder()
