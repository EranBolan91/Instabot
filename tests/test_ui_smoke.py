import re

from database.db import Database
from ui.core.db_helpers import account_username
from ui.theme.palette import TOKENS, load_stylesheet
from ui.widgets.account_picker import NO_ACCOUNTS_TEXT

PAGE_TITLES = ["Hashtag", "Unfollow", "Location", "Follow Followers", "DM", "Combination", "Statistics"]


def _add_accounts(*usernames):
    for username in usernames:
        Database().save_account("Name", "050", username, "secret")


def test_stylesheet_has_no_unresolved_tokens():
    rules = re.sub(r"/\*.*?\*/", "", load_stylesheet("dark"), flags=re.DOTALL)
    assert "@" not in rules
    assert TOKENS["bg"] == "#111318"
    assert TOKENS["accent"] == "#7C5CFF"
    assert TOKENS["danger"] == "#F04438"


def test_window_has_the_app_icon(make_window):
    window = make_window()
    assert not window.windowIcon().isNull()
    assert window.windowIcon().pixmap(64, 64).width() == 64


def test_sidebar_lists_every_page_in_old_tab_order(make_window):
    window = make_window()
    titles = [window.sidebar.item(i).text() for i in range(window.sidebar.count())]
    assert titles == PAGE_TITLES
    assert window.stack.count() == len(PAGE_TITLES)


def test_sidebar_switches_pages(make_window):
    window = make_window()
    for row in range(window.sidebar.count()):
        window.sidebar.setCurrentRow(row)
        assert window.stack.currentIndex() == row


def test_empty_database_disables_account_picker(make_window):
    window = make_window()
    picker = window.account_picker
    assert picker.current_account() is None
    assert not picker.combo.isEnabled()
    assert picker.combo.currentText() == NO_ACCOUNTS_TEXT
    assert all(page.account is None for page in window.pages)


def test_account_change_reaches_every_page(make_window, qtbot):
    window = make_window()
    _add_accounts("alice", "bob")
    window.account_picker.refresh()

    assert window.account_picker.combo.isEnabled()
    assert all(account_username(page.account) == "alice" for page in window.pages)

    with qtbot.waitSignal(window.account_picker.account_changed):
        window.account_picker.select_username("bob")
    assert all(account_username(page.account) == "bob" for page in window.pages)
    assert "@bob" in window.status_label.text()


def test_menu_shortcuts(make_window):
    window = make_window()
    assert window.settings_action.shortcut().toString() == "Ctrl+,"
    assert window.exit_action.shortcut().toString() == "Ctrl+Q"


def test_header_actions_open_each_dialog(make_window):
    from ui.dialogs.accounts_dialog import AccountsDialog
    from ui.dialogs.inspect_settings_dialog import InspectSettingsDialog
    from ui.dialogs.settings_dialog import SettingsDialog

    window = make_window()
    for action, dialog_class in ((window.accounts_action, AccountsDialog), (window.settings_action, SettingsDialog),
                                 (window.inspect_action, InspectSettingsDialog)):
        action.trigger()
        assert isinstance(window.current_dialog, dialog_class)
        assert window.current_dialog.isVisible()
        window.current_dialog.reject()
        assert window.current_dialog is None


def test_window_state_is_remembered(make_window):
    _add_accounts("alice", "bob")
    window = make_window()
    window.sidebar.setCurrentRow(3)
    window.account_picker.select_username("bob")
    window.close()

    reopened = make_window()
    assert reopened.stack.currentIndex() == 3
    assert reopened.account_picker.current_username() == "bob"


def test_status_bar_shows_running_count(make_window):
    window = make_window()
    assert window.running_label.text() == "0 running"
    window.set_running_count(2)
    assert window.running_label.text() == "2 running"
