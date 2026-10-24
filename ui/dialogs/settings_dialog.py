from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QAbstractItemView, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QGridLayout,
                               QHBoxLayout, QHeaderView, QLabel, QLineEdit, QListWidget, QListWidgetItem,
                               QPushButton, QSpinBox, QTableWidget, QTableWidgetItem, QTabWidget, QVBoxLayout,
                               QWidget)

from database.db import Database
from database.proxy.proxy import Proxy as ProxyDB
from database.website.website import Website as WebsiteDB
from models.proxy import Proxy as ProxyModel
from models.website import Website as WebsiteModel
from ui.core import validators
from ui.core.db_helpers import (PROXY_HOST, PROXY_ID, PROXY_PORT, PROXY_USERNAME, SETTINGS_FOLLOWERS,
                                SETTINGS_HEADLESS, SETTINGS_IS_SCHEDULE, SETTINGS_LIKES, SETTINGS_POSTS,
                                SETTINGS_SCHEDULE_HOUR, WEBSITE_ID, WEBSITE_URL, account_username, as_int, group_name)
from ui.widgets import confirm
from ui.widgets.card import Card
from ui.widgets.form import FormField, FormValidator
from ui.widgets.toast import Toast

TAB_GENERAL, TAB_LISTS, TAB_PROXIES, TAB_WEBSITES = range(4)


def _count_spin():
    spin = QSpinBox()
    spin.setRange(0, 100_000_000)
    spin.setGroupSeparatorShown(True)
    spin.setMinimumWidth(160)
    return spin


def _note(text):
    label = QLabel(text)
    label.setProperty("muted", True)
    label.setWordWrap(True)
    return label


def _page(*widgets):
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(16, 16, 16, 16)
    layout.setSpacing(16)
    for widget in widgets:
        layout.addWidget(widget)
    layout.addStretch(1)
    return page


class SettingsDialog(QDialog):
    """Thresholds, headless mode, distribution lists, proxies and warm-up websites."""

    lists_changed = Signal()  # a distribution list was added or removed

    def __init__(self, parent=None, username=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(920, 640)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_general(), "General")
        self.tabs.addTab(self._build_lists(username), "Distribution lists")
        self.tabs.addTab(self._build_proxies(), "Proxies")
        self.tabs.addTab(self._build_websites(), "Warm-up websites")

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 16)
        layout.setSpacing(16)
        layout.addWidget(self.tabs, 1)
        layout.addWidget(buttons)

        self.toast = Toast(self)
        self._load_general()
        self._reload_lists()
        self._reload_proxies()
        self._reload_websites()

    # ---------- General ----------

    def _build_general(self):
        thresholds = Card("Thresholds")
        self.likes_spin = _count_spin()
        self.posts_spin = _count_spin()
        self.followers_spin = _count_spin()
        grid = QGridLayout()
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(16)
        grid.addWidget(FormField("Only act on posts with more likes than", self.likes_spin,
                                 "Known issue: not enforced yet, the likes check is switched off in the bots."), 0, 0)
        grid.addWidget(FormField("Only follow users with at least this many followers", self.followers_spin,
                                 "Used by every feature that follows users."), 0, 1)
        grid.addWidget(FormField("Only follow users with at least this many posts", self.posts_spin,
                                 "Used by Combination."), 1, 0)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        thresholds.content.addLayout(grid)
        thresholds.content.addWidget(_note("A value left at 0 keeps its current value, like before."))

        browser = Card("Browser")
        self.headless_check = QCheckBox("Run Chrome hidden (headless)")
        browser.content.addWidget(self.headless_check)
        browser.content.addWidget(_note("Known issue: desktop Chrome ignores this for now. "
                                        "Only the DM bot's mobile mode uses it."))

        self.general_note = _note("No settings saved yet, so the defaults are shown.")
        self.save_general_button = QPushButton("Save")
        self.save_general_button.setProperty("variant", "primary")
        self.save_general_button.clicked.connect(self._save_general)
        row = QHBoxLayout()
        row.addWidget(self.general_note)
        row.addStretch(1)
        row.addWidget(self.save_general_button)
        footer = QWidget()
        footer.setLayout(row)
        return _page(thresholds, browser, footer)

    def _load_general(self):
        data = Database().get_data_from_settings()
        # the row is only created when the first account is added
        self.general_note.setVisible(data is None)
        if data is None:
            data = (None, 0, 0, 0, 0, None, 0, 0)
        self.likes_spin.setValue(as_int(data[SETTINGS_LIKES]))
        self.followers_spin.setValue(as_int(data[SETTINGS_FOLLOWERS]))
        self.posts_spin.setValue(as_int(data[SETTINGS_POSTS]))
        self.headless_check.setChecked(bool(as_int(data[SETTINGS_HEADLESS])))

    def _save_general(self):
        database = Database()
        data = database.get_data_from_settings()
        if data is None:
            database._init_settings()
            data = database.get_data_from_settings()
        likes = self.likes_spin.value() or as_int(data[SETTINGS_LIKES])
        followers = self.followers_spin.value() or as_int(data[SETTINGS_FOLLOWERS])
        posts = self.posts_spin.value() or as_int(data[SETTINGS_POSTS])
        # save_settings(likes, followers, schedule_hours, is_active, headless, posts). The old window passed
        # the two schedule columns the other way round, which swapped them on every save.
        saved = database.save_settings(likes, followers, data[SETTINGS_SCHEDULE_HOUR], data[SETTINGS_IS_SCHEDULE],
                                       int(self.headless_check.isChecked()), posts)
        self._load_general()
        if saved:
            self.toast.show_message("Settings saved", "success")
        else:
            self.toast.show_message("Couldn't save the settings. See the log for details.", "error")

    # ---------- Distribution lists ----------

    def _build_lists(self, username):
        card = Card("Distribution lists")
        card.content.addWidget(_note("While following, the Hashtag, Location and Follow Followers pages can save "
                                     "each followed user to a list. The DM page then messages a list."))

        self.lists_account_combo = QComboBox()
        self.lists_account_combo.setMinimumWidth(220)
        usernames = [account_username(row) for row in Database().get_accounts()]
        self.lists_account_combo.addItems(["@" + name for name in usernames])
        if username in usernames:
            self.lists_account_combo.setCurrentIndex(usernames.index(username))
        self.lists_account_combo.setEnabled(bool(usernames))
        self.lists_account_combo.currentIndexChanged.connect(lambda _index: self._reload_lists())
        card.content.addWidget(FormField("Account", self.lists_account_combo))

        self.lists_widget = QListWidget()
        self.lists_widget.setMinimumHeight(180)
        self.lists_widget.itemSelectionChanged.connect(self._update_list_buttons)
        self.lists_empty = _note("No lists for this account yet.")
        self.remove_list_button = QPushButton("Delete list")
        self.remove_list_button.setProperty("variant", "danger")
        self.remove_list_button.clicked.connect(self._remove_list)

        self.list_name_edit = QLineEdit()
        self.list_name_edit.setPlaceholderText("e.g. Travel followers")
        self.add_list_button = QPushButton("Add list")
        self.list_name_field = FormField("New list", self.list_name_edit, trailing=self.add_list_button)
        self.add_list_button.clicked.connect(self._add_list)
        self.list_name_edit.returnPressed.connect(self.add_list_button.click)
        self._group_names = []
        self.lists_validator = FormValidator(self)
        self.lists_validator.add(self.list_name_field, self._check_list_name, self.list_name_edit.textChanged)
        self.lists_validator.bind(self.add_list_button)

        list_buttons = QHBoxLayout()
        list_buttons.addStretch(1)
        list_buttons.addWidget(self.remove_list_button)

        card.content.addWidget(self.lists_widget)
        card.content.addWidget(self.lists_empty)
        card.content.addLayout(list_buttons)
        card.content.addWidget(self.list_name_field)
        if not usernames:
            card.content.addWidget(_note("Add an account first (Accounts in the header)."))
            self.list_name_edit.setEnabled(False)
        return _page(card)

    def _lists_username(self):
        return self.lists_account_combo.currentText()[1:] or None

    def _reload_lists(self):
        username = self._lists_username()
        database = Database()
        groups = database.get_distribution_lists_by_username(username) if username else []
        self._group_names = [group_name(group) for group in groups]
        self.lists_widget.clear()
        for name in self._group_names:
            members = len(database.get_users_from_dm_users(name, username))
            item = QListWidgetItem("{}   ·   {} user{}".format(name, members, "" if members == 1 else "s"))
            item.setData(Qt.UserRole, name)
            self.lists_widget.addItem(item)
        self.lists_widget.setVisible(bool(groups))
        self.lists_empty.setVisible(not groups)
        self.remove_list_button.setVisible(bool(groups))
        self._update_list_buttons()
        self.lists_validator.revalidate()

    def _check_list_name(self):
        if not self._lists_username():
            return "Add an account first"
        name = self.list_name_edit.text().strip()
        return validators.first_error(
            validators.required(name, "List name"),
            # removing a list and reading its users paste the name into the SQL
            validators.no_apostrophe(name, "List name"),
            validators.unique(name, self._group_names, "A list with this name"))

    def _add_list(self):
        if not self.lists_validator.touch_all():
            return
        name = self.list_name_edit.text().strip()
        if not Database().create_distribution_group(name, self._lists_username()):
            self.toast.show_message("Couldn't create the list. See the log for details.", "error")
            return
        self.list_name_edit.clear()
        self.lists_validator.reset()
        self._reload_lists()
        self.lists_changed.emit()
        self.toast.show_message("List \"{}\" created".format(name), "success")

    def _remove_list(self):
        item = self.lists_widget.currentItem()
        if item is None:
            return
        name = item.data(Qt.UserRole)
        if not confirm.ask(self, "Delete list", "Delete the list \"{}\" of @{}?\n\nNobody is unfollowed or messaged."
                           .format(name, self._lists_username())):
            return
        if not Database().remove_group_from_distribution_list(name, self._lists_username()):
            self.toast.show_message("Couldn't delete the list. See the log for details.", "error")
            return
        self._reload_lists()
        self.lists_changed.emit()
        self.toast.show_message("List \"{}\" deleted".format(name), "success")

    def _update_list_buttons(self):
        self.remove_list_button.setEnabled(self.lists_widget.currentItem() is not None
                                           and self.lists_widget.currentItem().isSelected())

    # ---------- Proxies ----------

    def _build_proxies(self):
        card = Card("Proxies")
        card.content.addWidget(_note("Known issue: saved proxies aren't applied by the bots yet."))

        self.proxy_table = QTableWidget(0, 3)
        self.proxy_table.setHorizontalHeaderLabels(("Host", "Username", "Port"))
        self.proxy_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.proxy_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.proxy_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.proxy_table.setShowGrid(False)
        self.proxy_table.verticalHeader().hide()
        self.proxy_table.setMinimumHeight(160)
        header = self.proxy_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.proxy_table.itemSelectionChanged.connect(self._update_proxy_buttons)
        self.proxies_empty = _note("No proxies saved.")
        self.remove_proxy_button = QPushButton("Delete proxy")
        self.remove_proxy_button.setProperty("variant", "danger")
        self.remove_proxy_button.clicked.connect(self._remove_proxy)
        remove_row = QHBoxLayout()
        remove_row.addStretch(1)
        remove_row.addWidget(self.remove_proxy_button)

        self.proxy_host_edit = QLineEdit()
        self.proxy_port_spin = QSpinBox()
        self.proxy_port_spin.setRange(0, 65535)
        self.proxy_username_edit = QLineEdit()
        self.proxy_password_edit = QLineEdit()
        self.proxy_password_edit.setEchoMode(QLineEdit.Password)
        host_field = FormField("Host *", self.proxy_host_edit)
        port_field = FormField("Port *", self.proxy_port_spin)
        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(12)
        # top-aligned, so an error under one field doesn't shift its neighbour
        grid.addWidget(host_field, 0, 0, Qt.AlignTop)
        grid.addWidget(port_field, 0, 1, Qt.AlignTop)
        grid.addWidget(FormField("Username", self.proxy_username_edit), 1, 0, Qt.AlignTop)
        grid.addWidget(FormField("Password", self.proxy_password_edit), 1, 1, Qt.AlignTop)
        grid.setColumnStretch(0, 2)
        grid.setColumnStretch(1, 1)

        self.save_proxy_button = QPushButton("Save proxy")
        self.save_proxy_button.clicked.connect(self._save_proxy)
        save_row = QHBoxLayout()
        save_row.addStretch(1)
        save_row.addWidget(self.save_proxy_button)

        self.proxy_validator = FormValidator(self)
        host = lambda: self.proxy_host_edit.text().strip()
        self.proxy_validator.add(host_field, lambda: validators.first_error(
            validators.required(host(), "Host"), validators.no_spaces(host(), "Host")),
            self.proxy_host_edit.textChanged)
        self.proxy_validator.add(port_field, lambda: validators.positive(self.proxy_port_spin.value(), "Port"),
                                 self.proxy_port_spin.valueChanged)
        self.proxy_validator.bind(self.save_proxy_button)

        card.content.addWidget(self.proxy_table)
        card.content.addWidget(self.proxies_empty)
        card.content.addLayout(remove_row)
        card.content.addLayout(grid)
        card.content.addLayout(save_row)
        return _page(card)

    def _reload_proxies(self):
        self._proxies = Database().get_proxy_data() or []
        self.proxy_table.setRowCount(len(self._proxies))
        for r, proxy in enumerate(self._proxies):
            for c, index in enumerate((PROXY_HOST, PROXY_USERNAME, PROXY_PORT)):
                self.proxy_table.setItem(r, c, QTableWidgetItem(str(proxy[index] or "")))
        self.proxy_table.setVisible(bool(self._proxies))
        self.proxies_empty.setVisible(not self._proxies)
        self.remove_proxy_button.setVisible(bool(self._proxies))
        self._update_proxy_buttons()

    def _save_proxy(self):
        if not self.proxy_validator.touch_all():
            return
        proxy = ProxyModel(self.proxy_host_edit.text().strip(), self.proxy_username_edit.text().strip(),
                           self.proxy_password_edit.text(), self.proxy_port_spin.value())
        # the old window only saved when every field was empty (inverted check, known issue #5)
        if not ProxyDB().save_in_db(proxy):
            self.toast.show_message("Couldn't save the proxy. See the log for details.", "error")
            return
        for edit in (self.proxy_host_edit, self.proxy_username_edit, self.proxy_password_edit):
            edit.clear()
        self.proxy_port_spin.setValue(0)
        self.proxy_validator.reset()
        self._reload_proxies()
        self.toast.show_message("Proxy {} saved".format(proxy.host), "success")

    def _remove_proxy(self):
        selected = self.proxy_table.selectionModel().selectedRows()
        if not selected:
            return
        proxy = self._proxies[selected[0].row()]
        if not confirm.ask(self, "Delete proxy", "Delete the proxy {}:{}?".format(proxy[PROXY_HOST], proxy[PROXY_PORT])):
            return
        if not ProxyDB().remove_from_db(proxy[PROXY_ID]):
            self.toast.show_message("Couldn't delete the proxy. See the log for details.", "error")
            return
        self._reload_proxies()
        self.toast.show_message("Proxy deleted", "success")

    def _update_proxy_buttons(self):
        self.remove_proxy_button.setEnabled(bool(self.proxy_table.selectionModel().selectedRows()))

    # ---------- Warm-up websites ----------

    def _build_websites(self):
        card = Card("Warm-up websites")
        card.content.addWidget(_note("Before each login, the bot opens one of these at random first, "
                                     "so it looks less like a bot."))

        self.websites_widget = QListWidget()
        self.websites_widget.setMinimumHeight(180)
        self.websites_widget.itemSelectionChanged.connect(self._update_website_buttons)
        self.websites_empty = _note("No websites saved. The bot goes straight to Instagram.")
        self.remove_website_button = QPushButton("Delete website")
        self.remove_website_button.setProperty("variant", "danger")
        self.remove_website_button.clicked.connect(self._remove_website)
        remove_row = QHBoxLayout()
        remove_row.addStretch(1)
        remove_row.addWidget(self.remove_website_button)

        self.website_edit = QLineEdit()
        self.website_edit.setPlaceholderText("https://www.example.com")
        self.add_website_button = QPushButton("Add website")
        self.website_field = FormField("New website", self.website_edit, trailing=self.add_website_button)
        self.add_website_button.clicked.connect(self._add_website)
        self.website_edit.returnPressed.connect(self.add_website_button.click)

        self.website_validator = FormValidator(self)
        self.website_validator.add(self.website_field, lambda: validators.first_error(
            validators.http_url(self.website_edit.text()),
            validators.unique(self.website_edit.text(), [w[WEBSITE_URL] for w in self._websites], "This website")),
            self.website_edit.textChanged)

        card.content.addWidget(self.websites_widget)
        card.content.addWidget(self.websites_empty)
        card.content.addLayout(remove_row)
        card.content.addWidget(self.website_field)
        self._websites = []
        self.website_validator.bind(self.add_website_button)
        return _page(card)

    def _reload_websites(self):
        self._websites = Database().get_websites_data() or []
        self.websites_widget.clear()
        for website in self._websites:
            item = QListWidgetItem(website[WEBSITE_URL])
            item.setData(Qt.UserRole, website[WEBSITE_ID])
            self.websites_widget.addItem(item)
        self.websites_widget.setVisible(bool(self._websites))
        self.websites_empty.setVisible(not self._websites)
        self.remove_website_button.setVisible(bool(self._websites))
        self._update_website_buttons()
        self.website_validator.revalidate()

    def _add_website(self):
        if not self.website_validator.touch_all():
            return
        link = self.website_edit.text().strip()
        if not WebsiteDB().save_in_db(WebsiteModel(link)):
            self.toast.show_message("Couldn't save the website. See the log for details.", "error")
            return
        self.website_edit.clear()
        self.website_validator.reset()
        self._reload_websites()
        self.toast.show_message("Website added", "success")

    def _remove_website(self):
        item = self.websites_widget.currentItem()
        if item is None:
            return
        if not confirm.ask(self, "Delete website", "Delete {}?".format(item.text())):
            return
        if not WebsiteDB().remove_from_db(item.data(Qt.UserRole)):
            self.toast.show_message("Couldn't delete the website. See the log for details.", "error")
            return
        self._reload_websites()
        self.toast.show_message("Website deleted", "success")

    def _update_website_buttons(self):
        item = self.websites_widget.currentItem()
        self.remove_website_button.setEnabled(item is not None and item.isSelected())
