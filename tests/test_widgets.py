import pytest
from PySide6.QtWidgets import QLineEdit, QPushButton

from database.db import Database
from ui.widgets.comment_input import MAX_CHIPS, CommentInput
from ui.widgets.credentials_box import CredentialsBox
from ui.widgets.distribution_picker import DistributionPicker
from ui.widgets.form import FormField, FormValidator
from ui.widgets.proxy_box import ProxyBox
from ui.widgets.schedule_box import UNITS, ScheduleBox
from ui.widgets.user_list import UserList
from utils.schedule import ScheduleCalc


def _account(username="alice"):
    Database().save_account("Alice", "050", username, "secret")
    return next(row for row in Database().get_accounts() if row[3] == username)


@pytest.mark.parametrize("unit_name, unit", UNITS)
@pytest.mark.parametrize("value", [1, 7, 45])
def test_schedule_box_matches_schedule_calc(themed, qtbot, unit_name, unit, value):
    box = ScheduleBox()
    qtbot.addWidget(box)
    box.check.setChecked(True)
    box.set_delay(value, unit)

    minutes, hours, days = (value if unit == ScheduleCalc().MINUTES else 0,
                            value if unit == ScheduleCalc().HOURS else 0,
                            value if unit == ScheduleCalc().DAYS else 0)
    assert box.delay_seconds() == ScheduleCalc().calc_schedule_time(unit, minutes, hours, days)


def test_schedule_box_off_means_no_delay(themed, qtbot):
    box = ScheduleBox()
    qtbot.addWidget(box)
    box.set_delay(5, ScheduleCalc().HOURS)
    assert box.delay_seconds() == 0
    assert not box.value_spin.isEnabled()
    assert box.error() is None


def test_schedule_box_needs_a_delay_above_zero(themed, qtbot):
    box = ScheduleBox()
    qtbot.addWidget(box)
    box.check.setChecked(True)
    box.set_delay(0, ScheduleCalc().MINUTES)
    assert box.error()
    box.set_delay(1, ScheduleCalc().HOURS)
    assert box.error() is None
    assert box.describe() == "in 1 hour"
    box.set_delay(3, ScheduleCalc().DAYS)
    assert box.describe() == "in 3 days"


def test_proxy_box_needs_both_or_neither(themed, qtbot):
    box = ProxyBox()
    qtbot.addWidget(box)
    assert box.error() is None
    assert box.proxy_dict() == {"proxy": "", "port": ""}

    box.host_edit.setText("10.0.0.1")
    assert box.error()
    assert box.host_edit.property("invalid")
    box.port_spin.setValue(8080)
    assert box.error() is None
    assert box.proxy_dict() == {"proxy": "10.0.0.1", "port": "8080"}


def test_comment_input_splits_trims_and_previews(themed, qtbot):
    widget = CommentInput()
    qtbot.addWidget(widget)
    widget.set_text(" Nice picture, Looking good,, I like it ,")
    assert widget.comments() == ["Nice picture", "Looking good", "I like it"]
    assert widget.chip_texts() == ["Nice picture", "Looking good", "I like it"]

    widget.set_text(",".join("c{}".format(i) for i in range(MAX_CHIPS + 3)))
    assert widget.chip_texts()[-1] == "+3 more"
    assert len(widget.chip_texts()) == MAX_CHIPS + 1


def test_user_list_search_and_count(themed, qtbot):
    widget = UserList()
    qtbot.addWidget(widget)
    widget.set_users(["alice", "bob", "alina"])
    assert widget.count_label.text() == "3 users"

    widget.search.setText("ali")
    assert widget.visible_users() == ["alice", "alina"]
    assert widget.count_label.text() == "2 of 3 users"

    widget.search.clear()
    widget.list.setCurrentRow(1)
    assert widget.selected_user() == "bob"
    widget.remove_user("bob")
    assert widget.users() == ["alice", "alina"]
    widget.set_users(["solo"])
    assert widget.count_label.text() == "1 user"


def test_credentials_box_is_read_only_and_masked(themed, qtbot):
    box = CredentialsBox()
    qtbot.addWidget(box)
    assert not box.has_account()
    box.set_account(_account())
    assert box.username() == "alice"
    assert box.password() == "secret"
    assert box.password_edit.echoMode() == QLineEdit.Password
    assert box.username_edit.isReadOnly() and box.password_edit.isReadOnly()


def test_distribution_picker_without_lists(themed, qtbot):
    picker = DistributionPicker()
    qtbot.addWidget(picker)
    picker.set_account(_account())
    assert not picker.check.isEnabled()
    assert picker.hint.isVisibleTo(picker)
    assert picker.selected_group() == ("", "")


def test_distribution_picker_with_lists(themed, qtbot):
    row = _account()
    Database().create_distribution_group("Travel", "alice")
    Database().create_distribution_group("Food", "alice")
    picker = DistributionPicker()
    qtbot.addWidget(picker)
    picker.set_account(row)

    assert picker.combo.count() == 2
    assert picker.selected_group() == ("", "")  # not checked yet
    picker.check.setChecked(True)
    group_id, name = picker.selected_group()
    assert name == "Travel"
    assert group_id == Database().get_group_id_by_group_name_and_id("Travel", "alice")

    # e.g. FOLLOW unchecked on the page
    picker.set_available(False)
    assert not picker.is_checked()
    assert picker.selected_group() == ("", "")


def test_form_validator_shows_errors_only_after_editing(themed, qtbot):
    edit = QLineEdit()
    button = QPushButton()
    field = FormField("Name", edit)
    qtbot.addWidget(field)
    validator = FormValidator()
    validator.add(field, lambda: None if edit.text() else "Name is required", edit.textChanged)
    validator.bind(button)

    assert not button.isEnabled()
    assert field.error() is None  # untouched: no red yet

    edit.setText("a")
    assert button.isEnabled()
    edit.clear()
    assert not button.isEnabled()
    assert field.error() == "Name is required"
    assert edit.property("invalid")
