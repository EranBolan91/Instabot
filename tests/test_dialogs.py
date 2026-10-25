from PySide6.QtWidgets import QLineEdit

from database.db import Database
from ui.core.db_helpers import SETTINGS_FOLLOWERS, SETTINGS_HEADLESS, SETTINGS_LIKES, SETTINGS_POSTS
from ui.dialogs.accounts_dialog import AccountsDialog
from ui.dialogs.settings_dialog import SettingsDialog


def _usernames():
    return [row[3] for row in Database().get_accounts()]


def _open(qtbot, dialog_class, **kwargs):
    dialog = dialog_class(**kwargs)
    qtbot.addWidget(dialog)
    dialog.show()
    return dialog


def _fill_account(dialog, username, password="pw", name="", phone=""):
    dialog.name_edit.setText(name)
    dialog.phone_edit.setText(phone)
    dialog.username_edit.setText(username)
    dialog.password_edit.setText(password)


# ---------- Accounts ----------

def test_add_account(themed, qtbot):
    dialog = _open(qtbot, AccountsDialog)
    changed = []
    dialog.accounts_changed.connect(lambda: changed.append(True))
    assert not dialog.save_button.isEnabled()

    _fill_account(dialog, "alice", "s3cret", "Alice", "050")
    assert dialog.save_button.isEnabled()
    dialog.save_button.click()

    assert _usernames() == ["alice"]
    assert changed == [True]
    assert dialog.table.rowCount() == 1
    assert dialog.username_edit.text() == ""  # form cleared for the next one


def test_password_is_never_in_the_table(themed, qtbot):
    Database().save_account("Alice", "050", "alice", "s3cret")
    dialog = _open(qtbot, AccountsDialog)
    cells = [dialog.table.item(0, c).text() for c in range(dialog.table.columnCount())]
    assert "s3cret" not in cells
    assert dialog.password_edit.echoMode() == QLineEdit.Password


def test_password_can_be_revealed_in_the_form(themed, qtbot):
    dialog = _open(qtbot, AccountsDialog)
    dialog.reveal_action.trigger()
    assert dialog.password_edit.echoMode() == QLineEdit.Normal
    dialog.reveal_action.trigger()
    assert dialog.password_edit.echoMode() == QLineEdit.Password


def test_duplicate_or_bad_usernames_are_rejected(themed, qtbot):
    Database().save_account("Alice", "050", "alice", "pw")
    dialog = _open(qtbot, AccountsDialog)
    for bad in ("ALICE", "my user", "o'neil"):
        _fill_account(dialog, bad)
        assert not dialog.save_button.isEnabled(), bad
        assert dialog.username_field.error()


def test_edit_account(themed, qtbot):
    Database().save_account("Alice", "050", "alice", "pw")
    dialog = _open(qtbot, AccountsDialog)
    dialog.table.selectRow(0)
    dialog.edit_button.click()
    assert dialog.form_card.title_label.text() == "Edit @alice"
    assert dialog.username_edit.text() == "alice"
    assert dialog.save_button.isEnabled()  # its own username isn't a duplicate

    dialog.password_edit.setText("new-pw")
    dialog.phone_edit.setText("052")
    dialog.save_button.click()
    row = Database().get_accounts()[0]
    assert (row[2], row[3], row[4]) == ("052", "alice", "new-pw")
    assert dialog.form_card.title_label.text() == "Add account"


def test_editing_blocks_apostrophes_the_sql_cant_store(themed, qtbot):
    Database().save_account("Alice", "050", "alice", "pw")
    dialog = _open(qtbot, AccountsDialog)
    dialog.table.selectRow(0)
    dialog.edit_button.click()
    dialog.password_edit.setText("it's")
    assert not dialog.save_button.isEnabled()
    assert "apostrophe" in dialog.password_field.error()


def test_delete_account_asks_first(themed, qtbot, confirm_yes):
    Database().save_account("Alice", "050", "alice", "pw")
    Database().save_account("Bob", "050", "bob", "pw")
    dialog = _open(qtbot, AccountsDialog)
    assert not dialog.delete_button.isEnabled()
    dialog.table.selectRow(1)
    dialog.delete_button.click()
    assert confirm_yes == ["Delete account"]
    assert _usernames() == ["alice"]


def test_declined_delete_keeps_the_account(themed, qtbot, monkeypatch):
    monkeypatch.setattr("ui.widgets.confirm.ask", lambda *args, **kwargs: False)
    Database().save_account("Alice", "050", "alice", "pw")
    dialog = _open(qtbot, AccountsDialog)
    dialog.table.selectRow(0)
    dialog.delete_button.click()
    assert _usernames() == ["alice"]


def test_accounts_dialog_updates_the_header(make_window):
    window = make_window()
    window.accounts_action.trigger()
    dialog = window.current_dialog
    _fill_account(dialog, "alice")
    dialog.save_button.click()
    assert window.account_picker.current_username() == "alice"
    assert all(page.account is not None for page in window.pages)


# ---------- Settings: general ----------

def test_settings_without_a_settings_row_shows_defaults(themed, qtbot):
    # a fresh database has no settings row until the first account is added
    assert Database().get_data_from_settings() is None
    dialog = _open(qtbot, SettingsDialog)
    assert dialog.general_note.isVisibleTo(dialog)
    assert dialog.followers_spin.value() == 0

    dialog.followers_spin.setValue(150)
    dialog.save_general_button.click()
    data = Database().get_data_from_settings()
    assert int(data[SETTINGS_FOLLOWERS]) == 150


def test_settings_zero_keeps_the_current_value(themed, qtbot):
    Database().save_account("Alice", "050", "alice", "pw")
    Database().save_settings(10, 200, 0, 0, 0, 5)
    dialog = _open(qtbot, SettingsDialog)
    assert (dialog.likes_spin.value(), dialog.followers_spin.value(), dialog.posts_spin.value()) == (10, 200, 5)

    dialog.likes_spin.setValue(0)
    dialog.posts_spin.setValue(9)
    dialog.headless_check.setChecked(True)
    dialog.save_general_button.click()

    data = Database().get_data_from_settings()
    assert int(data[SETTINGS_LIKES]) == 10
    assert int(data[SETTINGS_FOLLOWERS]) == 200
    assert int(data[SETTINGS_POSTS]) == 9
    assert data[SETTINGS_HEADLESS] == 1


def test_settings_save_keeps_the_schedule_columns_in_place(themed, qtbot):
    Database().save_account("Alice", "050", "alice", "pw")
    # save_settings(likes, followers, schedule_hours, is_active, headless, posts)
    Database().save_settings(1, 2, 7, 1, 0, 3)
    before = Database().get_data_from_settings()
    dialog = _open(qtbot, SettingsDialog)
    dialog.save_general_button.click()
    after = Database().get_data_from_settings()
    assert (after[3], after[4]) == (before[3], before[4])


# ---------- Settings: distribution lists ----------

def test_add_and_delete_distribution_list(themed, qtbot, confirm_yes):
    Database().save_account("Alice", "050", "alice", "pw")
    dialog = _open(qtbot, SettingsDialog, username="alice")
    changed = []
    dialog.lists_changed.connect(lambda: changed.append(True))

    dialog.list_name_edit.setText("Travel")
    dialog.add_list_button.click()
    assert [g[1] for g in Database().get_distribution_lists_by_username("alice")] == ["Travel"]
    assert dialog.lists_widget.count() == 1
    assert "0 users" in dialog.lists_widget.item(0).text()

    dialog.list_name_edit.setText("travel")
    assert not dialog.add_list_button.isEnabled()  # duplicate
    dialog.list_name_edit.setText("Mom's list")
    assert not dialog.add_list_button.isEnabled()  # apostrophe

    dialog.lists_widget.setCurrentRow(0)
    dialog.remove_list_button.click()
    assert Database().get_distribution_lists_by_username("alice") == []
    assert changed == [True, True]


def test_distribution_lists_follow_the_chosen_account(themed, qtbot):
    Database().save_account("Alice", "050", "alice", "pw")
    Database().save_account("Bob", "050", "bob", "pw")
    Database().create_distribution_group("Friends", "bob")
    dialog = _open(qtbot, SettingsDialog, username="bob")
    assert dialog.lists_widget.count() == 1
    dialog.lists_account_combo.setCurrentIndex(0)  # alice
    assert dialog.lists_widget.count() == 0


def test_distribution_lists_need_an_account(themed, qtbot):
    dialog = _open(qtbot, SettingsDialog)
    dialog.list_name_edit.setText("Travel")
    assert not dialog.add_list_button.isEnabled()


# ---------- Settings: proxies ----------

def test_save_and_delete_proxy(themed, qtbot, confirm_yes):
    dialog = _open(qtbot, SettingsDialog)
    assert not dialog.save_proxy_button.isEnabled()

    dialog.proxy_host_edit.setText("10.0.0.1")
    dialog.proxy_port_spin.setValue(8080)
    dialog.proxy_username_edit.setText("user")
    dialog.proxy_password_edit.setText("pass")
    assert dialog.save_proxy_button.isEnabled()
    dialog.save_proxy_button.click()

    proxies = Database().get_proxy_data()
    assert [(p[1], p[2], p[4]) for p in proxies] == [("10.0.0.1", "user", 8080)]
    assert dialog.proxy_table.rowCount() == 1
    assert "pass" not in [dialog.proxy_table.item(0, c).text() for c in range(3)]

    dialog.proxy_table.selectRow(0)
    dialog.remove_proxy_button.click()
    assert Database().get_proxy_data() == []


# ---------- Settings: websites ----------

def test_add_and_delete_website(themed, qtbot, confirm_yes):
    dialog = _open(qtbot, SettingsDialog)
    dialog.website_edit.setText("www.ynet.co.il")
    assert not dialog.add_website_button.isEnabled()  # needs http(s)://

    dialog.website_edit.setText("https://www.ynet.co.il")
    dialog.add_website_button.click()
    assert [w[1] for w in Database().get_websites_data()] == ["https://www.ynet.co.il"]

    dialog.website_edit.setText("https://www.ynet.co.il")
    assert not dialog.add_website_button.isEnabled()  # duplicate

    dialog.websites_widget.setCurrentRow(0)
    dialog.remove_website_button.click()
    assert Database().get_websites_data() == []
