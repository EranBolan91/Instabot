from ui.pages.base_page import BasePage


class StatisticsPage(BasePage):
    title = "Statistics"
    subtitle = "Results of past runs, per feature."
    icon = "fa5s.chart-bar"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.add_placeholder()
