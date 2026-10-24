from PySide6.QtWidgets import QLabel, QScrollArea, QVBoxLayout, QWidget


class BasePage(QWidget):
    """Common frame for the sidebar pages: title, subtitle and a scrollable body.

    Subclasses set ``title``, ``subtitle`` and ``icon`` (a qtawesome name used
    by the sidebar) and add their cards to ``self.body_layout``. Bot runs go
    through ``self.jobs`` (the JobManager), never straight to a thread.
    """

    title = ""
    subtitle = ""
    icon = ""

    def __init__(self, jobs=None, parent=None):
        super().__init__(parent)
        self.jobs = jobs
        self.account = None

        title_label = QLabel(self.title)
        title_label.setObjectName("PageTitle")
        subtitle_label = QLabel(self.subtitle)
        subtitle_label.setObjectName("PageSubtitle")
        subtitle_label.setWordWrap(True)

        self.body = QWidget()
        self.body.setObjectName("PageBody")
        self.body_layout = QVBoxLayout(self.body)
        self.body_layout.setContentsMargins(0, 16, 0, 0)
        self.body_layout.setSpacing(16)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.body)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 16)
        layout.setSpacing(4)
        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)
        layout.addWidget(scroll, 1)

    def set_account(self, row):
        """Called by MainWindow whenever the header account changes."""
        self.account = row
