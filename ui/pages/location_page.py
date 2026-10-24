from ui.pages.base_page import BasePage


class LocationPage(BasePage):
    title = "Location"
    subtitle = "Like, comment on and follow posts from a location page."
    icon = "fa5s.map-marker-alt"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.add_placeholder()
