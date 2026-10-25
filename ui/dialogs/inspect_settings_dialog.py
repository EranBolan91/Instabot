import copy

import qtawesome as qta
import shiboken6
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QAbstractItemView, QComboBox, QDialog, QFormLayout, QHBoxLayout, QHeaderView,
                               QLabel, QLineEdit, QPushButton, QSplitter, QTableWidget, QTabWidget, QTreeWidget,
                               QTreeWidgetItem, QVBoxLayout, QWidget)

from ui.core.db_helpers import account_password, account_username
from ui.theme.palette import color
from ui.widgets import confirm
from ui.widgets.card import Card
from ui.widgets.toast import Toast
from utils.instagram_selectors import S
from utils.selector_check import MISSING, OK, check_selectors, mark_checked

WAY_TYPES = ("css", "xpath", "name", "text", "scrollable")
WAY_HELP = ("<b>css</b> / <b>xpath</b>: a normal CSS selector or XPath. <b>name</b>: a form field's name. "
            "<b>text</b>: a regular expression matched against the whole visible text of the smallest element "
            "(e.g. <code>^[\\d.,KMB]+ followers?$</code>). <b>scrollable</b>: the scrolling part inside the "
            "element matching a CSS selector. The ways are tried from top to bottom.")
LIST_TEXTS = ("row_button_texts", "restriction_urls")
KEY_ROLE = Qt.UserRole


def handle_check_results(results, selectors=S):
    """Store the dates of what was found. Runs even if the dialog was closed meanwhile."""
    if results:
        mark_checked(results, selectors)


class InspectSettingsDialog(QDialog):
    """Edit how the bots find things on Instagram (utils/instagram_selectors.json) and check it."""

    def __init__(self, parent=None, jobs=None, account=None, selectors=S):
        super().__init__(parent)
        self.setWindowTitle("Inspect Settings")
        self.resize(1150, 720)
        self.jobs = jobs
        self.account = account
        self.selectors = selectors
        self.data = copy.deepcopy(selectors.data)
        self.last_results = {}
        self.dirty = False
        self._current_key = None
        self._loading = False
        self._check_job_id = None

        banner = QLabel("How the bots find things on Instagram's pages. When Instagram changes and a bot stops "
                        "finding something, fix it here: the bots use the saved values right away. <b>Check "
                        "selectors</b> logs in as the account in the header and visits the pages the bots use. It "
                        "only looks: it never follows, likes, comments or sends anything.")
        banner.setObjectName("Banner")
        banner.setWordWrap(True)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_selectors_tab(), "Selectors")
        self.tabs.addTab(self._build_texts_tab(), "Addresses and texts")

        self.check_button = QPushButton(qta.icon("fa5s.search", color=color("text")), "Check selectors")
        self.check_button.clicked.connect(self._check)
        self.check_status = QLabel()
        self.check_status.setProperty("muted", True)
        self.revert_button = QPushButton("Revert")
        self.revert_button.clicked.connect(self._revert)
        self.save_button = QPushButton("Save")
        self.save_button.setProperty("variant", "primary")
        self.save_button.clicked.connect(self._save)
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.reject)
        buttons = QHBoxLayout()
        buttons.addWidget(self.check_button)
        buttons.addWidget(self.check_status, 1)
        buttons.addWidget(self.revert_button)
        buttons.addWidget(self.save_button)
        buttons.addWidget(close_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 16)
        layout.setSpacing(14)
        layout.addWidget(banner)
        layout.addWidget(self.tabs, 1)
        layout.addLayout(buttons)

        self.toast = Toast(self)
        self._fill_tree()
        self._fill_texts()
        self._select_first()
        self._update_buttons()

    # ---------- Selectors tab ----------

    def _build_selectors_tab(self):
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(("Selector", "Status"))
        self.tree.setRootIsDecorated(True)
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tree.header().setStretchLastSection(True)
        self.tree.currentItemChanged.connect(lambda item, _previous: self._show(item.data(0, KEY_ROLE)
                                                                                if item else None))

        details = Card()
        self.key_label = QLabel()
        self.key_label.setObjectName("CardTitle")
        self.what_label = QLabel()
        self.what_label.setWordWrap(True)
        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        self.status_label.setProperty("muted", True)

        self.ways_table = QTableWidget(0, 2)
        self.ways_table.setHorizontalHeaderLabels(("Type", "Value"))
        self.ways_table.verticalHeader().hide()
        self.ways_table.verticalHeader().setDefaultSectionSize(40)
        self.ways_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.ways_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.ways_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.ways_table.horizontalHeader().resizeSection(0, 130)
        self.ways_table.horizontalHeader().setStretchLastSection(True)

        self.add_way_button = QPushButton("Add way")
        self.add_way_button.clicked.connect(self._add_way)
        self.remove_way_button = QPushButton("Remove")
        self.remove_way_button.clicked.connect(self._remove_way)
        self.up_button = QPushButton(qta.icon("fa5s.arrow-up", color=color("text")), "")
        self.up_button.setToolTip("Try this way earlier")
        self.up_button.clicked.connect(lambda: self._move_way(-1))
        self.down_button = QPushButton(qta.icon("fa5s.arrow-down", color=color("text")), "")
        self.down_button.setToolTip("Try this way later")
        self.down_button.clicked.connect(lambda: self._move_way(1))
        way_buttons = QHBoxLayout()
        for button in (self.add_way_button, self.remove_way_button, self.up_button, self.down_button):
            way_buttons.addWidget(button)
        way_buttons.addStretch(1)
        help_label = QLabel(WAY_HELP)
        help_label.setWordWrap(True)
        help_label.setProperty("muted", True)

        details.content.addWidget(self.key_label)
        details.content.addWidget(self.what_label)
        details.content.addWidget(self.status_label)
        details.content.addWidget(self.ways_table, 1)
        details.content.addLayout(way_buttons)
        details.content.addWidget(help_label)

        splitter = QSplitter()
        splitter.addWidget(self.tree)
        splitter.addWidget(details)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([380, 720])
        return splitter

    def _fill_tree(self):
        current = self._current_key
        self.tree.clear()
        bold = QFont()
        bold.setBold(True)
        for group, entries in self.data["selectors"].items():
            parent = QTreeWidgetItem([group])
            parent.setFont(0, bold)
            parent.setFlags(parent.flags() & ~Qt.ItemIsSelectable)
            for name in entries:
                key = "{}.{}".format(group, name)
                item = QTreeWidgetItem([name])
                item.setData(0, KEY_ROLE, key)
                self._set_status(item, key)
                parent.addChild(item)
                if key == current:
                    self.tree.setCurrentItem(item)
            self.tree.addTopLevelItem(parent)
        self.tree.expandAll()

    def _status(self, key):
        """(short text, icon name, color token, long text)"""
        if key in self.last_results:
            status, note = self.last_results[key]
            if status == OK:
                return "Found just now", "fa5s.check-circle", "success", "Found in the last check."
            if status == MISSING:
                return "Missing", "fa5s.times-circle", "danger", "Not found in the last check: this needs fixing."
        checked = self._entry(key).get("checked")
        if checked:
            return "Seen {}".format(checked), "fa5s.check-circle", "muted", "Last seen working on {}.".format(checked)
        note = self.last_results.get(key, (None, ""))[1]
        return ("Not checked", "fa5s.question-circle", "warning",
                "Not checked yet: an educated guess{}.".format(" ({})".format(note) if note else ""))

    def _set_status(self, item, key):
        text, icon, token, _ = self._status(key)
        item.setText(1, text)
        item.setIcon(1, qta.icon(icon, color=color(token)))

    def _entry(self, key):
        group, name = key.split(".")
        return self.data["selectors"][group][name]

    def _select_first(self):
        first = self.tree.topLevelItem(0)
        if first is not None and first.childCount():
            self.tree.setCurrentItem(first.child(0))

    def _show(self, key):
        self._current_key = key
        self._loading = True
        self.ways_table.setRowCount(0)
        if key is None:
            self.key_label.setText("")
            self.what_label.setText("")
            self.status_label.setText("")
        else:
            entry = self._entry(key)
            self.key_label.setText(key)
            self.what_label.setText(entry.get("what", ""))
            self.status_label.setText(self._status(key)[3])
            for way in entry["find"]:
                self._append_way_row(*next(iter(way.items())))
        self._loading = False
        self._update_buttons()

    def _append_way_row(self, kind, value):
        row = self.ways_table.rowCount()
        self.ways_table.insertRow(row)
        combo = QComboBox()
        combo.addItems(WAY_TYPES)
        combo.setCurrentText(kind)
        combo.currentTextChanged.connect(self._ways_edited)
        edit = QLineEdit(value)
        edit.setCursorPosition(0)
        edit.textChanged.connect(self._ways_edited)
        self.ways_table.setCellWidget(row, 0, combo)
        self.ways_table.setCellWidget(row, 1, edit)

    def _table_ways(self):
        return [{self.ways_table.cellWidget(row, 0).currentText(): self.ways_table.cellWidget(row, 1).text()}
                for row in range(self.ways_table.rowCount())]

    def _ways_edited(self, *_):
        if self._loading or self._current_key is None:
            return
        self._entry(self._current_key)["find"] = self._table_ways()
        self._mark_dirty()

    def _add_way(self):
        self._append_way_row("css", "")
        self.ways_table.selectRow(self.ways_table.rowCount() - 1)
        self.ways_table.cellWidget(self.ways_table.rowCount() - 1, 1).setFocus()
        self._ways_edited()

    def _selected_way_row(self):
        rows = self.ways_table.selectionModel().selectedRows()
        return rows[0].row() if rows else self.ways_table.rowCount() - 1

    def _remove_way(self):
        row = self._selected_way_row()
        if row < 0:
            return
        ways = self._table_ways()
        del ways[row]
        self._entry(self._current_key)["find"] = ways
        self._show(self._current_key)
        self._mark_dirty()

    def _move_way(self, step):
        row = self._selected_way_row()
        ways = self._table_ways()
        target = row + step
        if row < 0 or not 0 <= target < len(ways):
            return
        ways[row], ways[target] = ways[target], ways[row]
        self._entry(self._current_key)["find"] = ways
        self._show(self._current_key)
        self.ways_table.selectRow(target)
        self._mark_dirty()

    # ---------- Addresses and texts tab ----------

    def _build_texts_tab(self):
        page = QWidget()
        form = QFormLayout(page)
        form.setContentsMargins(16, 16, 16, 16)
        form.setVerticalSpacing(12)
        self.url_edits = {}
        self.text_edits = {}
        for name in self.data["urls"]:
            edit = QLineEdit()
            edit.textChanged.connect(self._texts_edited)
            self.url_edits[name] = edit
            form.addRow("Address: {}".format(name), edit)
        for name in self.data["texts"]:
            edit = QLineEdit()
            if name in LIST_TEXTS:
                edit.setToolTip("Several values, separated by commas")
            edit.textChanged.connect(self._texts_edited)
            self.text_edits[name] = edit
            form.addRow("Text: {}".format(name), edit)
        note = QLabel("Addresses can use {username} and {tag}. Values marked with commas are lists.")
        note.setProperty("muted", True)
        form.addRow(note)
        return page

    def _fill_texts(self):
        self._loading = True
        for name, edit in self.url_edits.items():
            edit.setText(self.data["urls"][name])
        for name, edit in self.text_edits.items():
            value = self.data["texts"][name]
            edit.setText(", ".join(value) if isinstance(value, list) else value)
        self._loading = False

    def _texts_edited(self, *_):
        if self._loading:
            return
        for name, edit in self.url_edits.items():
            self.data["urls"][name] = edit.text().strip()
        for name, edit in self.text_edits.items():
            text = edit.text().strip()
            self.data["texts"][name] = [part.strip() for part in text.split(",") if part.strip()] \
                if name in LIST_TEXTS else text
        self._mark_dirty()

    # ---------- Saving ----------

    def _mark_dirty(self):
        self.dirty = True
        self._update_buttons()

    def _update_buttons(self):
        self.save_button.setEnabled(self.dirty)
        self.revert_button.setEnabled(self.dirty)
        has_key = self._current_key is not None
        for button in (self.add_way_button, self.remove_way_button, self.up_button, self.down_button):
            button.setEnabled(has_key)
        can_check = self.jobs is not None and self.account is not None
        checking = self._check_job_id is not None
        self.check_button.setEnabled(can_check and not self.dirty and not checking)
        if not can_check:
            self.check_button.setToolTip("Pick an account in the header first")
        elif self.dirty:
            self.check_button.setToolTip("Save or revert your changes first")
        else:
            self.check_button.setToolTip("Logs in as @{} and checks every selector".format(
                account_username(self.account)))

    def _problems(self):
        for key in self.selectors.keys():
            ways = self._entry(key)["find"]
            if not ways:
                return key, "needs at least one way to find it"
            if any(not next(iter(way.values())).strip() for way in ways):
                return key, "has an empty value"
        for name, value in self.data["urls"].items():
            if not value.startswith("https://"):
                return None, "The address \"{}\" must start with https://".format(name)
        return None

    def _save(self):
        problem = self._problems()
        if problem:
            key, text = problem
            if key:
                self._select_key(key)
                text = "{} {}".format(key, text)
            self.toast.show_message("Not saved: {}.".format(text), "error")
            return False
        self.selectors.save(copy.deepcopy(self.data))
        self.dirty = False
        self._fill_tree()
        self._update_buttons()
        self.toast.show_message("Saved. The bots use the new values from now on.", "success")
        return True

    def _revert(self):
        self.data = copy.deepcopy(self.selectors.data)
        self.dirty = False
        self._fill_tree()
        self._fill_texts()
        self._show(self._current_key)
        self._update_buttons()

    def _select_key(self, key):
        for i in range(self.tree.topLevelItemCount()):
            parent = self.tree.topLevelItem(i)
            for j in range(parent.childCount()):
                if parent.child(j).data(0, KEY_ROLE) == key:
                    self.tree.setCurrentItem(parent.child(j))
                    return

    def reject(self):
        if self.dirty and not confirm.ask(self, "Unsaved changes", "Close without saving your changes?", "Discard"):
            return
        super().reject()

    # ---------- Checking ----------

    def _check(self):
        username = account_username(self.account)
        if not confirm.ask(self, "Check selectors",
                           "Open Chrome, log in as @{} and visit the pages the bots use?\n\nIt only looks: it opens "
                           "lists, a post and a chat, and never follows, likes, comments or sends anything. "
                           "Follow the progress in the Log tab.".format(username), "Check"):
            return
        password = account_password(self.account)
        selectors = self.selectors
        dialog = self

        def make_bot():
            # imported here: building a bot opens Chrome, which only happens on the worker thread
            from bot_folder.main_bot import InstagramBot
            return InstagramBot(username, password, False, {"proxy": "", "port": ""})

        def run(bot):
            try:
                if not bot._login():
                    return None
                results = check_selectors(bot.driver, username)
                # logging in used these
                for key in ("login.username_input", "login.password_input"):
                    results[key] = (OK, "used to log in")
                return results
            finally:
                bot.driver.quit()

        def on_result(results):
            handle_check_results(results, selectors)
            if shiboken6.isValid(dialog):
                dialog.show_results(results)

        job = self.jobs.submit("Check selectors", username, "only looks, changes nothing", make_bot=make_bot,
                               run=run, on_result=on_result)
        self._check_job_id = job.id
        self.jobs.job_finished.connect(self._on_job_finished)
        self.check_status.setText("Checking… follow it in the Log tab.")
        self._update_buttons()

    def _on_job_finished(self, job):
        if job.id != self._check_job_id:
            return
        self.jobs.job_finished.disconnect(self._on_job_finished)
        self._check_job_id = None
        if job.error:
            self.check_status.setText("The check failed: {}".format(job.error))
        self._update_buttons()

    def show_results(self, results):
        if not results:
            self.check_status.setText("Couldn't log in, so nothing was checked. See the Log tab.")
            self.toast.show_message("The check couldn't log in.", "error")
            return
        self.last_results = results
        if not self.dirty:
            self.data = copy.deepcopy(self.selectors.data)
        found = sum(1 for status, _ in results.values() if status == OK)
        missing = sorted(key for key, (status, _) in results.items() if status == MISSING)
        self.check_status.setText("{} found, {} missing{}".format(
            found, len(missing), ": " + ", ".join(missing) if missing else ""))
        self._fill_tree()
        self._show(self._current_key)
        self.toast.show_message("Check finished: {} found, {} missing".format(found, len(missing)),
                                "error" if missing else "success")
