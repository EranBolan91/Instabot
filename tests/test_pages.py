"""Phase 4: every page runs its bot as a job, with the same arguments the old tabs passed.

The bot classes are replaced with a recorder, so Chrome never opens.
"""
import threading
from datetime import datetime

import pytest

from database.db import Database
from database.hashtag.hashtag import HashtagDB
from models.hashtag import Hashtag
from ui.core.jobs import DONE, SCHEDULED
from ui.pages.job_page import NO_LIMIT

WAIT_MS = 5000
NO_PROXY = {"proxy": "", "port": ""}


class Recorder:
    """Stands in for every bot class. Records the constructor and each method call."""

    def __init__(self):
        self.calls = []  # (bot class name, constructor args, method, method args)
        self.returns = {}  # method name -> return value
        self.built_on = []  # thread names the bots were built on

    def factory(self, class_name):
        recorder = self

        class FakeBot:
            def __init__(self, *args):
                self.args = args
                self.driver = None
                recorder.built_on.append(threading.current_thread().name)

            def __getattr__(self, method):
                def call(*args):
                    recorder.calls.append((class_name, self.args, method, args))
                    return recorder.returns.get(method)
                return call

        return FakeBot

    def methods(self):
        return [(call[0], call[2], call[3]) for call in self.calls]


@pytest.fixture
def bots(monkeypatch):
    recorder = Recorder()
    for module, name in (("hashtag_page", "HashTagBot"), ("location_page", "LocationBot"),
                         ("follow_followers_page", "FollowFollowersBot"), ("followers_page", "FollowersBot"),
                         ("dm_page", "DM"), ("combination_page", "CombinationBot")):
        monkeypatch.setattr("ui.pages.{}.{}".format(module, name), recorder.factory(name))
    return recorder


@pytest.fixture
def window(make_window):
    Database().save_account("Alice", "050", "alice", "pw")
    window = make_window()
    window.account_picker.refresh()
    return window


def page(window, cls_name):
    return next(p for p in window.pages if type(p).__name__ == cls_name)


def wait_for_calls(qtbot, bots, count):
    qtbot.waitUntil(lambda: len(bots.calls) >= count, timeout=WAIT_MS)


def alice_id():
    return Database().get_user_id("alice")


# ---------- Hashtag ----------

def test_hashtag_needs_an_account(make_window):
    window = make_window()
    hashtag = page(window, "HashtagPage")
    hashtag.hashtag_edit.setText("sunset")
    hashtag.actions.like_check.setChecked(True)
    assert not hashtag.run_button.isEnabled()


def test_hashtag_validation(window):
    hashtag = page(window, "HashtagPage")
    assert not hashtag.run_button.isEnabled()  # no hashtag

    hashtag.hashtag_edit.setText("#sunset")
    assert not hashtag.run_button.isEnabled()  # no action
    hashtag.actions.like_check.setChecked(True)
    assert hashtag.run_button.isEnabled()

    hashtag.actions.comment_check.setChecked(True)
    assert not hashtag.run_button.isEnabled()  # COMMENT without comments
    assert hashtag.actions.comments_field.error()
    hashtag.actions.comment_input.set_text("Nice, Cool")
    assert hashtag.run_button.isEnabled()

    hashtag.hashtag_edit.setText("two words")
    assert not hashtag.run_button.isEnabled()


def test_hashtag_runs_the_bot_like_the_old_tab(window, qtbot, bots):
    hashtag = page(window, "HashtagPage")
    hashtag.hashtag_edit.setText("#sunset")
    hashtag.posts_spin.setValue(30)
    hashtag.actions.like_check.setChecked(True)
    hashtag.actions.comment_check.setChecked(True)
    hashtag.actions.comment_input.set_text("Nice, Cool")
    hashtag.run_button.click()
    wait_for_calls(qtbot, bots, 1)

    name, init, method, args = bots.calls[0]
    assert (name, init, method) == ("HashTagBot", ("alice", "pw", False, NO_PROXY), "search_hash_tag")
    # hash_tag, amount (text), like, comment, follow, split_comment, distribution, group_name, group_id, schedule
    assert args == ("sunset", "30", 1, 1, 0, ["Nice", "Cool"], 0, "", "", 0)
    assert bots.built_on == ["job-1"]  # built on the worker thread, not the GUI
    job = window.jobs.get(1)
    qtbot.waitUntil(lambda: job.status == DONE, timeout=WAIT_MS)
    assert job.kind == "HashTag" and job.account == "alice"
    assert window.toast.isVisible()


def test_hashtag_follow_saves_to_the_chosen_list(make_window, qtbot, bots):
    Database().save_account("Alice", "050", "alice", "pw")
    Database().create_distribution_group("Travel", "alice")
    window = make_window()
    window.account_picker.refresh()
    hashtag = page(window, "HashtagPage")
    hashtag.hashtag_edit.setText("travel")
    hashtag.actions.follow_check.setChecked(True)
    hashtag.actions.distribution.check.setChecked(True)
    hashtag.run_button.click()
    wait_for_calls(qtbot, bots, 1)

    args = bots.calls[0][3]
    group_id = Database().get_group_id_by_group_name_and_id("Travel", "alice")
    assert args == ("travel", "20", 0, 0, 1, "", 1, "Travel", group_id, 0)


def test_hashtag_list_choice_needs_follow(make_window):
    Database().save_account("Alice", "050", "alice", "pw")
    Database().create_distribution_group("Travel", "alice")
    window = make_window()
    window.account_picker.refresh()
    actions = page(window, "HashtagPage").actions
    assert not actions.distribution.check.isEnabled()
    actions.follow_check.setChecked(True)
    assert actions.distribution.check.isEnabled()


def test_scheduled_job_waits_with_the_old_delay(window, qtbot, bots):
    hashtag = page(window, "HashtagPage")
    hashtag.hashtag_edit.setText("sunset")
    hashtag.actions.like_check.setChecked(True)
    hashtag.schedule.check.setChecked(True)
    hashtag.schedule.set_delay(5, 0)  # 5 minutes
    hashtag.run_button.click()

    job = window.jobs.get(1)
    assert job.status == SCHEDULED
    assert 295 <= (job.run_at - datetime.now()).total_seconds() <= 300
    assert "in 5 minutes" in window.toast.text()
    assert bots.calls == []
    window.jobs.cancel(job.id)


# ---------- Location ----------

def test_location_needs_a_location_url(window):
    location = page(window, "LocationPage")
    location.actions.like_check.setChecked(True)
    location.url_edit.setText("https://www.instagram.com/natgeo/")
    assert not location.run_button.isEnabled()
    location.url_edit.setText("https://www.instagram.com/explore/locations/212988663/new-york-new-york/")
    assert location.run_button.isEnabled()
    assert not location.name_edit.isEnabled()


def test_location_runs_the_bot_like_the_old_tab(window, qtbot, bots):
    location = page(window, "LocationPage")
    url = "https://www.instagram.com/explore/locations/212988663/new-york-new-york/"
    location.url_edit.setText(url)
    location.posts_spin.setValue(10)
    location.actions.like_check.setChecked(True)
    location.actions.follow_check.setChecked(True)
    location.run_button.click()
    wait_for_calls(qtbot, bots, 1)

    # url, amount, like, follow, comment (this order), split_comment, distribution, group_name, group_id, schedule
    assert bots.methods() == [("LocationBot", "search_location_by_url", (url, "10", 1, 1, 0, "", 0, "", "", 0))]


# ---------- Follow Followers ----------

def test_follow_followers_both_modes(window, qtbot, bots):
    follow = page(window, "FollowFollowersPage")
    url = "https://www.instagram.com/natgeo/"
    follow.url_edit.setText(url)
    follow.follow_spin.setValue(40)
    assert not follow.skip_spin.isEnabled()  # their followers: skip isn't used
    follow.run_button.click()
    wait_for_calls(qtbot, bots, 1)

    follow.mode.set_index(1)
    assert follow.skip_spin.isEnabled()
    follow.skip_spin.setValue(5)
    follow.run_button.click()
    wait_for_calls(qtbot, bots, 2)

    # user_url, account_username, num_of_following, distribution, group_name, group_id, is_schedule, num_skip
    assert sorted(bots.methods()) == sorted([
        ("FollowFollowersBot", "follow_after_followers", (url, "alice", 40, 0, "", "", 0, 0)),
        ("FollowFollowersBot", "follow_after_following", (url, "alice", 40, 0, "", "", 0, 5)),
    ])


def test_follow_followers_shows_past_runs(make_window):
    from database.follow_followers.follow_followers import FollowFollowersDB
    from models.follow_followers import FollowFollowers

    Database().save_account("Alice", "050", "alice", "pw")
    FollowFollowersDB().save_in_db(FollowFollowers("alice", "https://www.instagram.com/natgeo/", 40, 3, 0, "", 0, 5))
    window = make_window()
    window.account_picker.refresh()
    history = page(window, "FollowFollowersPage").history
    assert history.visible_rows() == 1
    assert history.cell(0, 1) == "40"


# ---------- Unfollow ----------

def test_unfollow_check_shows_results_then_unfollows_them(window, qtbot, bots, confirm_yes):
    unfollow = page(window, "FollowersPage")
    bots.returns["get_unfollowers"] = ["bob", "carol"]
    unfollow.run_button.click()
    assert not unfollow.run_button.isEnabled()  # one check at a time
    qtbot.waitUntil(lambda: unfollow.results.users() == ["bob", "carol"], timeout=WAIT_MS)
    qtbot.waitUntil(unfollow.run_button.isEnabled, timeout=WAIT_MS)
    assert unfollow.unfollow_results_button.text() == "Unfollow all 2"

    unfollow.unfollow_results_button.click()
    wait_for_calls(qtbot, bots, 2)
    # user_list, to_remove_from_db, account_id, to_login, to_reverse, limit, remove_not_found_users
    assert bots.methods()[1] == ("FollowersBot", "unfollow_users", (["bob", "carol"], 0, alice_id(), 1, 0,
                                                                     NO_LIMIT, False))


def test_unfollow_lists_the_users_the_bot_followed(window, qtbot, bots, confirm_yes):
    for user in ("bob", "carol"):
        Database().save_unfollow_users(user, "alice")
    window.account_picker.refresh()
    unfollow = page(window, "FollowersPage")
    assert unfollow.followed.users() == ["bob", "carol"]

    unfollow.limit_spin.setValue(10)
    unfollow.reverse_check.setChecked(True)
    unfollow.remove_not_found_check.setChecked(True)
    unfollow.unfollow_list_button.click()
    wait_for_calls(qtbot, bots, 1)
    assert bots.methods() == [("FollowersBot", "unfollow_users", (["bob", "carol"], 1, alice_id(), 1, 1, 10, True))]


def test_unfollow_selected_and_remove_from_list(window, qtbot, bots, confirm_yes):
    for user in ("bob", "carol"):
        Database().save_unfollow_users(user, "alice")
    window.account_picker.refresh()
    unfollow = page(window, "FollowersPage")
    assert not unfollow.unfollow_selected_button.isEnabled()

    unfollow.followed.list.setCurrentRow(0)
    unfollow.unfollow_selected_button.click()
    wait_for_calls(qtbot, bots, 1)
    assert bots.methods() == [("FollowersBot", "unfollow_user", ("bob", alice_id()))]

    unfollow.followed.list.setCurrentRow(1)
    unfollow.remove_button.click()
    assert [row[2] for row in Database().get_unfollow_users("alice")] == ["bob"]
    assert unfollow.followed.users() == ["bob"]


def test_unfollow_only_non_followers_runs_two_steps(window, qtbot, bots, confirm_yes):
    for user in ("bob", "carol"):
        Database().save_unfollow_users(user, "alice")
    window.account_picker.refresh()
    unfollow = page(window, "FollowersPage")
    bots.returns["unfollow_users_who_not_return_follow"] = ["carol"]
    unfollow.unfollow_non_followers_button.click()
    wait_for_calls(qtbot, bots, 2)
    assert bots.methods() == [
        ("FollowersBot", "unfollow_users_who_not_return_follow", (["bob", "carol"], alice_id(), 0)),
        # the old tab left out remove_not_found_users here (known issue #17)
        ("FollowersBot", "unfollow_users", (["carol"], 1, alice_id(), 1, 0, NO_LIMIT, False)),
    ]


def test_unfollow_everyone_asks_and_passes_the_limit(window, qtbot, bots, confirm_yes):
    unfollow = page(window, "FollowersPage")
    unfollow.everyone_spin.setValue(25)
    unfollow.unfollow_everyone_button.click()
    wait_for_calls(qtbot, bots, 1)
    assert confirm_yes == ["Unfollow"]
    assert bots.methods() == [("FollowersBot", "unfollow_all_users", (25,))]


def test_declined_unfollow_runs_nothing(window, qtbot, bots, monkeypatch):
    monkeypatch.setattr("ui.widgets.confirm.ask", lambda *args, **kwargs: False)
    page(window, "FollowersPage").unfollow_everyone_button.click()
    qtbot.wait(300)
    assert bots.calls == [] and window.jobs.jobs == {}


# ---------- DM ----------

def _dm_window(make_window):
    Database().save_account("Alice", "050", "alice", "pw")
    Database().create_distribution_group("Travel", "alice")
    group_id = Database().get_group_id_by_group_name_and_id("Travel", "alice")
    for user in ("bob", "carol"):
        Database().add_username_to_distribution_group(user, group_id)
    window = make_window()
    window.account_picker.refresh()
    return window, group_id


def test_dm_without_lists(window):
    dm = page(window, "DmPage")
    dm.message_edit.setPlainText("Hi")
    assert not dm.run_button.isEnabled()
    assert dm.no_lists_label.isVisibleTo(dm)


def test_dm_sends_like_the_old_tab(make_window, qtbot, bots):
    window, group_id = _dm_window(make_window)
    dm = page(window, "DmPage")
    assert dm.members.users() == ["bob", "carol"]
    assert not dm.run_button.isEnabled()  # no message yet
    dm.message_edit.setPlainText("Hi there")
    assert dm.char_count.text() == "8 characters"
    dm.run_button.click()
    wait_for_calls(qtbot, bots, 1)

    name, init, method, args = bots.calls[0]
    assert (name, init[2], method) == ("DM", True, "send_message_to_distribution_group")
    # message, dm_users, group_name, is_schedule, to_login, account_id, group_id, limit_msg
    assert args == ("Hi there", [("bob",), ("carol",)], "Travel", 0, True, alice_id(), group_id, NO_LIMIT)


def test_dm_remove_and_clear_members(make_window, confirm_yes):
    window, group_id = _dm_window(make_window)
    dm = page(window, "DmPage")
    dm.members.list.setCurrentRow(0)
    dm.remove_member_button.click()
    assert dm.members.users() == ["carol"]
    dm.clear_list_button.click()
    assert Database().get_users_from_dm_users("Travel", "alice") == []
    assert not dm.run_button.isEnabled()


# ---------- Combination ----------

def test_combination_hashtag_or_url(window, qtbot, bots):
    combination = page(window, "CombinationPage")
    combination.hashtag_edit.setText("sunset")
    combination.likes_spin.setValue(2)
    combination.run_button.click()
    wait_for_calls(qtbot, bots, 1)

    combination.source.set_index(1)
    assert not combination.run_button.isEnabled()
    url = "https://www.instagram.com/p/abc123/"
    combination.url_edit.setText(url)
    combination.skip_posts_spin.setValue(3)
    combination.run_button.click()
    wait_for_calls(qtbot, bots, 2)

    # hashtag, url, likes, followers, distribution, schedule (always 0), group_name, group_id, skip_posts, skip_users
    assert sorted(bots.methods()) == sorted([
        ("CombinationBot", "combination", ("sunset", "", 2, 100, 0, 0, "", "", 0, 0)),
        ("CombinationBot", "combination", ("", url, 2, 100, 0, 0, "", "", 3, 0)),
    ])
    assert bots.calls[0][1][3] == NO_PROXY  # no more hard-coded dummy proxy


# ---------- Statistics ----------

def test_statistics_tables_and_account_filter(make_window, qtbot):
    Database().save_account("Alice", "050", "alice", "pw")
    Database().save_account("Bob", "050", "bob", "pw")
    for account in ("alice", "bob"):
        HashtagDB().save_in_db(Hashtag(account, "sunset", 20, 1, 0, 1, 0, "", "Nice", 2, 0))
    window = make_window()
    window.account_picker.refresh()
    stats = page(window, "StatisticsPage")
    table = stats.tables["HashTag"]
    assert table.visible_rows() == 2
    assert stats.tables["Combination"].visible_rows() == 0

    table.account_check.setChecked(True)
    assert table.visible_rows() == 1
    assert table.cell(0, 0) == "alice"
    assert table.cell(0, 4) == "Yes"  # Like
    table.account_check.setChecked(False)
    table.search.setText("bob")
    assert table.visible_rows() == 1


def test_statistics_refresh_after_a_job(window, qtbot):
    stats = page(window, "StatisticsPage")
    HashtagDB().save_in_db(Hashtag("alice", "sunset", 20, 1, 0, 0, 0, "", "", 0, 0))
    assert stats.tables["HashTag"].visible_rows() == 0
    job = window.jobs.submit("Test", "alice", "fake", make_bot=lambda: None, run=lambda bot: None)
    qtbot.waitUntil(lambda: job.status == DONE, timeout=WAIT_MS)
    assert stats.tables["HashTag"].visible_rows() == 1
