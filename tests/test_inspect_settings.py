"""The Inspect Settings window: editing utils/instagram_selectors.json and checking it.

Works on a temporary copy of the selectors file; the check runs with a fake bot.
"""
import json

import pytest

from database.db import Database
from ui.core.jobs import DONE
from ui.dialogs.inspect_settings_dialog import InspectSettingsDialog
from utils.instagram_selectors import PATH, Selectors
from utils.selector_check import MISSING, OK

WAIT_MS = 5000


@pytest.fixture
def selectors(tmp_path):
    copy = tmp_path / "instagram_selectors.json"
    copy.write_text(PATH.read_text(encoding="utf-8"), encoding="utf-8")
    return Selectors(copy)


@pytest.fixture(autouse=True)
def _close_dialogs():
    yield
    # closed here, not by qtbot: a dialog with unsaved changes would ask "Discard?" and wait forever
    for dialog in _OPEN:
        dialog.dirty = False
        dialog.close()
        dialog.deleteLater()
    _OPEN.clear()


_OPEN = []


def _open(qtbot, selectors, **kwargs):
    dialog = InspectSettingsDialog(selectors=selectors, **kwargs)
    dialog.show()
    _OPEN.append(dialog)
    return dialog


def _saved(selectors):
    return json.loads(selectors.path.read_text(encoding="utf-8"))


def test_lists_every_selector_grouped_by_page(themed, qtbot, selectors):
    dialog = _open(qtbot, selectors)
    groups = [dialog.tree.topLevelItem(i).text(0) for i in range(dialog.tree.topLevelItemCount())]
    assert groups == list(selectors.data["selectors"])
    count = sum(dialog.tree.topLevelItem(i).childCount() for i in range(dialog.tree.topLevelItemCount()))
    assert count == len(selectors.keys())
    assert dialog.key_label.text() == "login.username_input"
    assert dialog.ways_table.rowCount() == 2  # name=email, name=username
    assert not dialog.save_button.isEnabled()


def test_status_shows_checked_and_unchecked(themed, qtbot, selectors):
    dialog = _open(qtbot, selectors)
    dialog._select_key("block.popup")
    assert "educated guess" in dialog.status_label.text()
    dialog._select_key("post.like_button")
    assert "Last seen working on" in dialog.status_label.text()


def test_edit_a_way_and_save(themed, qtbot, selectors):
    dialog = _open(qtbot, selectors)
    dialog._select_key("login.username_input")
    dialog.ways_table.cellWidget(0, 1).setText("user_field")
    assert dialog.save_button.isEnabled()
    dialog.save_button.click()
    assert _saved(selectors)["selectors"]["login"]["username_input"]["find"][0] == {"name": "user_field"}
    assert selectors.ways("login.username_input")[0] == {"name": "user_field"}  # bots see it at once
    assert not dialog.save_button.isEnabled()


def test_add_remove_and_reorder_ways(themed, qtbot, selectors):
    dialog = _open(qtbot, selectors)
    dialog._select_key("post.comment_input")
    before = selectors.ways("post.comment_input")
    dialog.add_way_button.click()
    dialog.ways_table.cellWidget(dialog.ways_table.rowCount() - 1, 0).setCurrentText("xpath")
    dialog.ways_table.cellWidget(dialog.ways_table.rowCount() - 1, 1).setText("//textarea")
    dialog.up_button.click()  # move the new way one place earlier
    dialog.save_button.click()
    ways = selectors.ways("post.comment_input")
    assert ways[-2] == {"xpath": "//textarea"} and len(ways) == len(before) + 1

    dialog._select_key("post.comment_input")
    dialog.ways_table.selectRow(len(ways) - 2)
    dialog.remove_way_button.click()
    dialog.save_button.click()
    assert selectors.ways("post.comment_input") == before


def test_empty_value_is_not_saved(themed, qtbot, selectors):
    dialog = _open(qtbot, selectors)
    dialog._select_key("dm.message_input")
    dialog.ways_table.cellWidget(0, 1).setText("  ")
    dialog.save_button.click()
    assert dialog.dirty
    assert "empty value" in dialog.toast.text()
    assert _saved(selectors)["selectors"]["dm"]["message_input"] == selectors.entry("dm.message_input")


def test_revert_drops_changes(themed, qtbot, selectors):
    dialog = _open(qtbot, selectors)
    dialog._select_key("login.username_input")
    dialog.ways_table.cellWidget(0, 1).setText("changed")
    dialog.revert_button.click()
    assert not dialog.dirty
    assert dialog.ways_table.cellWidget(0, 1).text() == "email"


def test_addresses_and_list_texts(themed, qtbot, selectors):
    dialog = _open(qtbot, selectors)
    dialog.text_edits["row_button_texts"].setText("Follow, Following , Requested")
    dialog.url_edits["hashtag"].setText("https://www.instagram.com/explore/search/keyword/?q=%23{tag}")
    dialog.save_button.click()
    saved = _saved(selectors)
    assert saved["texts"]["row_button_texts"] == ["Follow", "Following", "Requested"]
    assert selectors.url("hashtag", tag="sun").endswith("q=%23sun")

    dialog.url_edits["login"].setText("instagram.com/login")
    dialog.save_button.click()
    assert "https://" in dialog.toast.text()


def test_unsaved_changes_ask_before_closing(themed, qtbot, selectors, monkeypatch):
    asked = []
    monkeypatch.setattr("ui.widgets.confirm.ask", lambda *args, **kwargs: asked.append(args[1]) or False)
    dialog = _open(qtbot, selectors)
    dialog.ways_table.cellWidget(0, 1).setText("changed")
    dialog.reject()
    assert asked == ["Unsaved changes"] and dialog.isVisible()


def test_check_needs_an_account_and_no_unsaved_changes(themed, qtbot, selectors):
    dialog = _open(qtbot, selectors)
    assert not dialog.check_button.isEnabled()  # no jobs / account


def test_check_runs_as_a_job_and_records_what_was_found(make_window, qtbot, selectors, monkeypatch, confirm_yes):
    Database().save_account("Alice", "050", "alice", "pw")
    window = make_window()
    window.account_picker.refresh()

    class FakeDriver:
        quit_called = False

        def quit(self):
            FakeDriver.quit_called = True

    class FakeBot:
        def __init__(self, *args):
            self.args = args
            self.driver = FakeDriver()

        def _login(self):
            return True

    def fake_check(driver, username):
        return {"post.like_button": (OK, ""), "dm.message_input": (MISSING, ""), "block.popup": ("not checked", "x")}

    monkeypatch.setattr("bot_folder.main_bot.InstagramBot", FakeBot)
    monkeypatch.setattr("ui.dialogs.inspect_settings_dialog.check_selectors", fake_check)
    before = selectors.entry("dm.message_input")["checked"]

    dialog = _open(qtbot, selectors, jobs=window.jobs, account=window.account_picker.current_account())
    assert dialog.check_button.isEnabled()
    dialog.check_button.click()
    assert confirm_yes == ["Check selectors"]
    job = window.jobs.get(1)
    assert job.kind == "Check selectors"
    qtbot.waitUntil(lambda: job.status == DONE, timeout=WAIT_MS)

    assert FakeDriver.quit_called
    assert "1 missing: dm.message_input" in dialog.check_status.text()
    assert selectors.entry("dm.message_input")["checked"] == before  # missing: date unchanged
    assert selectors.entry("login.username_input")["checked"]  # used to log in
    dialog._select_key("dm.message_input")
    assert "needs fixing" in dialog.status_label.text()
    qtbot.waitUntil(dialog.check_button.isEnabled, timeout=WAIT_MS)
