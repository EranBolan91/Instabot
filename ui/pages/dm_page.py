from ui.pages.base_page import BasePage


class DmPage(BasePage):
    title = "DM"
    subtitle = "Send direct messages to the users in a distribution list."
    icon = "fa5s.envelope"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.add_placeholder()
