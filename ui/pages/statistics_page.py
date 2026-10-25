from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QTabWidget, QVBoxLayout, QWidget

from database.combination.combination import CombinationDM
from database.dm.dm import DMDB
from database.follow_back.follow_back import FollowBackDB
from database.follow_followers.follow_followers import FollowFollowersDB
from database.hashtag.hashtag import HashtagDB
from database.location.location import LocationDB
from ui.core.db_helpers import account_username
from ui.pages.base_page import BasePage
from ui.widgets.records_table import BOOL, DATE, NUMBER, Column, RecordsTable

C = Column

# Column positions are the schema in PROJECT_OVERVIEW.md section 6.1 (the id column is left out).
POST_ACTIONS = (C("Posts", 3, NUMBER), C("Failed", 4, NUMBER), C("Like", 5, BOOL), C("Follow", 6, BOOL),
                C("Comment", 7, BOOL), C("Saved to list", 8, BOOL), C("List", 9), C("Comments", 10),
                C("Scheduled", 11, BOOL), C("Date", 12, DATE))

# (tab title, load function, columns, index of the account in the row, note)
SECTIONS = (
    ("HashTag", lambda: HashtagDB().get_hashtag_data(),
     (C("Account", 1), C("Hashtag", 2)) + POST_ACTIONS, 1, None),
    ("Location", lambda: LocationDB().get_location_data(),
     (C("Account", 1), C("Location", 2)) + POST_ACTIONS, 1, None),
    ("Follow Followers", lambda: FollowFollowersDB().get_follow_followers_data(),
     (C("Account", 1), C("Profile", 2), C("Followed", 3, NUMBER), C("Failed", 4, NUMBER), C("Saved to list", 5, BOOL),
      C("List", 6), C("Scheduled", 7, BOOL), C("Date", 8, DATE), C("Skipped", 9, NUMBER)), 1, None),
    ("DM", lambda: DMDB().get_dm_data(),
     (C("Account", 1), C("Message", 2), C("List", 3), C("Members", 4, NUMBER), C("Failed", 5, NUMBER),
      C("Scheduled", 6, BOOL), C("Date", 7, DATE)), 1, None),
    ("Follow back", lambda: FollowBackDB().get_follow_back_data(),
     (C("Account", 2), C("Followed back", 3, NUMBER), C("Date", 4, DATE)), 2,
     "After each unfollow run: how many of the unfollowed users were following you."),
    ("Combination", lambda: CombinationDM().get_combination_data(),
     (C("Account", 1), C("Post", 2), C("Hashtag", 3), C("Likes", 4, NUMBER), C("Failed likes", 5, NUMBER),
      C("Followed", 6, NUMBER), C("Failed follows", 7, NUMBER), C("Scheduled", 8, BOOL), C("Saved to list", 9, BOOL),
      C("List", 10), C("Date", 11, DATE), C("Skipped users", 12, NUMBER)), 1, None),
)


class StatisticsPage(BasePage):
    title = "Statistics"
    subtitle = "Results of past runs, per feature. Refreshes by itself when a job finishes."
    icon = "fa5s.chart-bar"

    def __init__(self, jobs=None, parent=None):
        super().__init__(jobs, parent)
        self.tabs = QTabWidget()
        self.tables = {}
        self._loaders = {}
        for title, load, columns, account_index, note in SECTIONS:
            page = QWidget()
            layout = QVBoxLayout(page)
            layout.setContentsMargins(12, 12, 12, 12)
            if note:
                label = QLabel(note)
                label.setProperty("muted", True)
                layout.addWidget(label)
            table = RecordsTable(columns, "No runs yet.", account_index=account_index, searchable=True)
            layout.addWidget(table, 1)
            self.tabs.addTab(page, title)
            self.tables[title] = table
            self._loaders[title] = load

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(self.refresh_button)
        self.body_layout.addLayout(row)
        self.body_layout.addWidget(self.tabs, 1)

        if jobs is not None:
            jobs.job_finished.connect(lambda _job: self.refresh())
        self.refresh()

    def set_account(self, row):
        super().set_account(row)
        for table in self.tables.values():
            table.set_account(account_username(row) if row else None)

    def refresh(self):
        for title, table in self.tables.items():
            table.set_rows(self._loaders[title]())
