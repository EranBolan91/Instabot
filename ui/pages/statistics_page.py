from ui.pages.base_page import BasePage


class StatisticsPage(BasePage):
    title = "Statistics"
    subtitle = "Results of past runs, per feature."
    icon = "fa5s.chart-bar"

    def __init__(self, jobs=None, parent=None):
        super().__init__(jobs, parent)
        self.add_placeholder()
