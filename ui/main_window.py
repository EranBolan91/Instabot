from pathlib import Path

import qtawesome as qta
from PySide6.QtCore import QSettings, QSize, Qt
from PySide6.QtGui import QAction, QIcon, QKeySequence
from PySide6.QtWidgets import (QDockWidget, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMainWindow,
                               QPlainTextEdit, QStackedWidget, QToolButton, QVBoxLayout, QWidget)

from ui.core.db_helpers import account_username
from ui.pages.combination_page import CombinationPage
from ui.pages.dm_page import DmPage
from ui.pages.follow_followers_page import FollowFollowersPage
from ui.pages.followers_page import FollowersPage
from ui.pages.hashtag_page import HashtagPage
from ui.pages.location_page import LocationPage
from ui.pages.statistics_page import StatisticsPage
from ui.theme.palette import color
from ui.widgets.account_picker import AccountPicker

# Same order as the old Tkinter tabs.
PAGE_CLASSES = (HashtagPage, FollowersPage, LocationPage, FollowFollowersPage, DmPage, CombinationPage,
                StatisticsPage)

APP_ICON = Path(__file__).resolve().parent.parent / "insta_bot.ico"


def _icon(name):
    return qta.icon(name, color=color("muted"), color_active=color("text"), color_selected="#FFFFFF")


class MainWindow(QMainWindow):
    """Header + sidebar + page stack, with Jobs and Log docks at the bottom."""

    def __init__(self, settings=None):
        super().__init__()
        self.settings = settings if settings is not None else QSettings()
        self._geometry_restored = False

        self.setWindowTitle("Instabot")
        if APP_ICON.exists():
            self.setWindowIcon(QIcon(str(APP_ICON)))
        self.setMinimumSize(1000, 640)

        self.pages = [page_class() for page_class in PAGE_CLASSES]

        self._create_actions()
        self._build_menu()
        self._build_central()
        self._build_docks()
        self._build_status_bar()

        self.sidebar.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.account_picker.account_changed.connect(self._on_account_changed)

        self._restore_state()

    # ---------- Building ----------

    def _create_actions(self):
        self.accounts_action = QAction(_icon("fa5s.user-cog"), "Accounts…", self)
        self.accounts_action.setToolTip("Manage accounts")
        self.accounts_action.triggered.connect(self._open_accounts)

        self.settings_action = QAction(_icon("fa5s.cog"), "Settings…", self)
        self.settings_action.setShortcut(QKeySequence("Ctrl+,"))
        self.settings_action.setToolTip("Settings (Ctrl+,)")
        self.settings_action.triggered.connect(self._open_settings)

        self.inspect_action = QAction(_icon("fa5s.search"), "Inspect Settings…", self)
        self.inspect_action.triggered.connect(self._open_inspect_settings)

        self.exit_action = QAction("Exit", self)
        self.exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        self.exit_action.triggered.connect(self.close)

    def _build_menu(self):
        main_menu = self.menuBar().addMenu("&Main")
        main_menu.addAction(self.accounts_action)
        main_menu.addAction(self.settings_action)
        main_menu.addAction(self.inspect_action)
        main_menu.addSeparator()
        main_menu.addAction(self.exit_action)

        # filled in _build_docks, once the docks exist
        self.view_menu = self.menuBar().addMenu("&View")

    def _build_central(self):
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._build_header())

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        self.sidebar = QListWidget()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(210)
        self.sidebar.setIconSize(QSize(18, 18))
        self.stack = QStackedWidget()
        for page in self.pages:
            item = QListWidgetItem(_icon(page.icon), page.title)
            # QSS item padding isn't counted in the row height, so set it here
            item.setSizeHint(QSize(0, 40))
            self.sidebar.addItem(item)
            self.stack.addWidget(page)

        body.addWidget(self.sidebar)
        body.addWidget(self.stack, 1)
        layout.addLayout(body, 1)
        self.setCentralWidget(central)

    def _build_header(self):
        header = QWidget()
        header.setObjectName("Header")
        # needed for a plain QWidget to paint its stylesheet background
        header.setAttribute(Qt.WA_StyledBackground, True)

        title = QLabel("Instabot")
        title.setObjectName("HeaderTitle")

        account_label = QLabel("Account")
        account_label.setProperty("muted", True)
        self.account_picker = AccountPicker()

        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 10, 16, 10)
        layout.setSpacing(8)
        layout.addWidget(title)
        layout.addStretch(1)
        layout.addWidget(account_label)
        layout.addWidget(self.account_picker)
        layout.addSpacing(8)
        for action in (self.accounts_action, self.settings_action):
            button = QToolButton()
            button.setDefaultAction(action)
            button.setIconSize(QSize(18, 18))
            layout.addWidget(button)
        return header

    def _build_docks(self):
        jobs_placeholder = QLabel("No jobs yet. Jobs you run or schedule will show up here.")
        jobs_placeholder.setProperty("muted", True)
        jobs_placeholder.setAlignment(Qt.AlignCenter)
        self.jobs_dock = self._make_dock("Jobs", "JobsDock", jobs_placeholder)

        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setPlaceholderText("Bot output will appear here.")
        self.log_dock = self._make_dock("Log", "LogDock", self.log_view)

        self.addDockWidget(Qt.BottomDockWidgetArea, self.jobs_dock)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.log_dock)
        self.tabifyDockWidget(self.jobs_dock, self.log_dock)
        self.jobs_dock.raise_()
        self.resizeDocks([self.jobs_dock], [200], Qt.Vertical)

        self.view_menu.addAction(self.jobs_dock.toggleViewAction())
        self.view_menu.addAction(self.log_dock.toggleViewAction())

    def _make_dock(self, title, object_name, widget):
        dock = QDockWidget(title, self)
        # saveState() needs an object name to remember the dock
        dock.setObjectName(object_name)
        dock.setAllowedAreas(Qt.BottomDockWidgetArea)
        dock.setWidget(widget)
        return dock

    def _build_status_bar(self):
        self.status_label = QLabel("Ready")
        self.running_label = QLabel()
        self.statusBar().addWidget(self.status_label, 1)
        self.statusBar().addPermanentWidget(self.running_label)
        self.set_running_count(0)

    # ---------- Status ----------

    def set_status(self, text):
        self.status_label.setText(text)

    def set_running_count(self, count):
        self.running_label.setText("{} running".format(count))

    # ---------- Account ----------

    def _on_account_changed(self, row):
        for page in self.pages:
            page.set_account(row)
        if row:
            self.set_status("Account: @{}".format(account_username(row)))
        else:
            self.set_status("No accounts yet. Add one in Accounts.")

    # ---------- Dialogs (built in phase 3) ----------

    def _open_accounts(self):
        self._dialog_not_ready("Accounts")

    def _open_settings(self):
        self._dialog_not_ready("Settings")

    def _open_inspect_settings(self):
        self._dialog_not_ready("Inspect Settings")

    def _dialog_not_ready(self, name):
        self.set_status("The {} window isn't rebuilt yet. Use the old window for now: python main_tk.py".format(name))

    # ---------- Window state ----------

    def show_initial(self):
        if self._geometry_restored:
            self.show()
        else:
            self.showMaximized()

    def _restore_state(self):
        geometry = self.settings.value("window/geometry")
        if geometry is not None:
            self._geometry_restored = self.restoreGeometry(geometry)
        state = self.settings.value("window/state")
        if state is not None:
            self.restoreState(state)

        page = int(self.settings.value("window/page", 0))
        self.sidebar.setCurrentRow(page if 0 <= page < len(self.pages) else 0)
        self.account_picker.refresh(prefer_username=self.settings.value("account/username"))

    def closeEvent(self, event):
        self.settings.setValue("window/geometry", self.saveGeometry())
        self.settings.setValue("window/state", self.saveState())
        self.settings.setValue("window/page", self.sidebar.currentRow())
        username = self.account_picker.current_username()
        if username:
            self.settings.setValue("account/username", username)
        self.settings.sync()
        super().closeEvent(event)
