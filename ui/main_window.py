from pathlib import Path

import qtawesome as qta
from PySide6.QtCore import QSettings, QSize, Qt
from PySide6.QtGui import QAction, QIcon, QKeySequence
from PySide6.QtWidgets import (QDockWidget, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMainWindow,
                               QMessageBox, QStackedWidget, QToolButton, QVBoxLayout, QWidget)

from ui.core.db_helpers import account_username
from ui.dialogs.accounts_dialog import AccountsDialog
from ui.dialogs.inspect_settings_dialog import InspectSettingsDialog
from ui.dialogs.settings_dialog import SettingsDialog
from ui.core.jobs import CANCELLED, DONE, FAILED, RUNNING, JobManager
from ui.pages.combination_page import CombinationPage
from ui.pages.dm_page import DmPage
from ui.pages.follow_followers_page import FollowFollowersPage
from ui.pages.followers_page import FollowersPage
from ui.pages.hashtag_page import HashtagPage
from ui.pages.location_page import LocationPage
from ui.pages.statistics_page import StatisticsPage
from ui.theme.palette import color
from ui.widgets.account_picker import AccountPicker
from ui.widgets.jobs_panel import JobsPanel
from ui.widgets.log_panel import LogPanel
from ui.widgets.toast import Toast

# Same order as the old Tkinter tabs.
PAGE_CLASSES = (HashtagPage, FollowersPage, LocationPage, FollowFollowersPage, DmPage, CombinationPage,
                StatisticsPage)

APP_ICON = Path(__file__).resolve().parent.parent / "insta_bot.ico"


def _icon(name):
    return qta.icon(name, color=color("muted"), color_active=color("text"), color_selected="#FFFFFF")


class MainWindow(QMainWindow):
    """Header + sidebar + page stack, with Jobs and Log docks at the bottom."""

    def __init__(self, settings=None, jobs=None, log_bridge=None):
        super().__init__()
        self.settings = settings if settings is not None else QSettings()
        self.jobs = jobs if jobs is not None else JobManager(parent=self)
        self._geometry_restored = False

        self.setWindowTitle("Instabot")
        if APP_ICON.exists():
            self.setWindowIcon(QIcon(str(APP_ICON)))
        self.setMinimumSize(1000, 640)
        self.current_dialog = None

        self.pages = [page_class(jobs=self.jobs) for page_class in PAGE_CLASSES]

        self._create_actions()
        self._build_menu()
        self._build_central()
        self._build_docks()
        self._build_status_bar()
        self.toast = Toast(self.centralWidget())

        self.sidebar.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.account_picker.account_changed.connect(self._on_account_changed)

        self.jobs.job_added.connect(self.log_panel.add_job)
        self.jobs.job_removed.connect(self.log_panel.remove_job)
        self.jobs.job_updated.connect(self._on_job_updated)
        self.jobs_panel.job_activated.connect(self.show_job_log)
        self.jobs_panel.summary_changed.connect(self.jobs_dock.setWindowTitle)
        self.log_panel.block_detected.connect(self._on_block_line)
        for page in self.pages:
            if hasattr(page, "notify"):
                page.notify.connect(self.show_toast)
        if log_bridge is not None:
            log_bridge.text_written.connect(self.log_panel.write)

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
        self.jobs_panel = JobsPanel(self.jobs)
        self.jobs_dock = self._make_dock("Jobs", "JobsDock", self.jobs_panel)
        self.log_panel = LogPanel()
        self.log_dock = self._make_dock("Log", "LogDock", self.log_panel)

        self.addDockWidget(Qt.BottomDockWidgetArea, self.jobs_dock)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.log_dock)
        self.tabifyDockWidget(self.jobs_dock, self.log_dock)
        self.jobs_dock.raise_()

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

    def show_toast(self, text, kind="info"):
        self.toast.show_message(text, kind)

    # ---------- Jobs ----------

    def _on_job_updated(self, job):
        self.set_running_count(self.jobs.running_count())
        if job.status == RUNNING:
            self.set_status("{} started".format(job.label))
        elif job.status == DONE:
            self.set_status("{} finished".format(job.label))
        elif job.status == CANCELLED:
            self.set_status("{} cancelled".format(job.label))
        elif job.status == FAILED:
            self.set_status("{} failed: {}".format(job.label, job.error))
            self.show_toast("{} failed. See the log for details.".format(job.label), "error")

    def _on_block_line(self, job_id, _line):
        job = self.jobs.get(job_id)
        who = "@" + job.account if job else "An account"
        self.show_toast("{} may be blocked. See the log for details.".format(who), "error")

    def show_job_log(self, job_id):
        self.log_panel.filter_to_job(job_id)
        self.log_dock.show()
        self.log_dock.raise_()

    # ---------- Account ----------

    def _on_account_changed(self, row):
        for page in self.pages:
            page.set_account(row)
        if row:
            self.set_status("Account: @{}".format(account_username(row)))
        else:
            self.set_status("No accounts yet. Add one in Accounts.")

    # ---------- Dialogs ----------

    def _open_accounts(self):
        dialog = AccountsDialog(self)
        # keep the header (and every page) in sync while the dialog is open
        dialog.accounts_changed.connect(lambda: self.account_picker.refresh())
        self._open_dialog(dialog)

    def _open_settings(self):
        dialog = SettingsDialog(self, username=self.account_picker.current_username())
        # pages show the account's distribution lists
        dialog.lists_changed.connect(lambda: self.account_picker.refresh())
        self._open_dialog(dialog)

    def _open_inspect_settings(self):
        self._open_dialog(InspectSettingsDialog(self))

    def _open_dialog(self, dialog):
        # open() is modal like exec(), but doesn't block the caller (or the tests)
        dialog.setAttribute(Qt.WA_DeleteOnClose)
        dialog.finished.connect(lambda _result: setattr(self, "current_dialog", None))
        self.current_dialog = dialog
        dialog.open()

    # ---------- Window state ----------

    def show_initial(self):
        if self._geometry_restored:
            self.show()
        else:
            self.showMaximized()
            # first launch: room for about 6 jobs (later the saved layout is used)
            self.resizeDocks([self.jobs_dock], [300], Qt.Vertical)
        # otherwise the account combo starts focused and looks highlighted
        self.sidebar.setFocus()

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
        if self.jobs.active_count():
            answer = QMessageBox.question(
                self, "Quit Instabot",
                "{} running and {} scheduled jobs.\n\nQuit anyway? Running jobs are stopped and their Chrome "
                "windows closed. Scheduled jobs are cancelled.".format(
                    self.jobs.running_count(), self.jobs.scheduled_count()))
            if answer != QMessageBox.Yes:
                event.ignore()
                return
            self.jobs.shutdown()

        self.settings.setValue("window/geometry", self.saveGeometry())
        self.settings.setValue("window/state", self.saveState())
        self.settings.setValue("window/page", self.sidebar.currentRow())
        username = self.account_picker.current_username()
        if username:
            self.settings.setValue("account/username", username)
        self.settings.sync()
        super().closeEvent(event)
