"""DM and Combination runs save a stats row for the Statistics page (#13, #12). No Chrome is opened."""
import sqlite3

import pytest

from bot_folder.combination import combination_bot
from bot_folder.combination.combination_bot import CombinationBot
from bot_folder.dm import dm_bot
from database import db
from database.combination.combination import CombinationDM
from database.dm.dm import DMDB
from models.combination import Combination
from models.dm import DM


@pytest.fixture
def tmp_db(workdir):
    database = db.Database()
    database.save_account("n", "p", "me", "pw")
    return database


class FakeDriver:
    window_handles = [0, 1]

    def __init__(self):
        self.closed = 0
        self.switch_to = self

    def window(self, handle):
        pass

    def delete_all_cookies(self):
        pass

    def close(self):
        self.closed += 1


def _bot(cls):
    # skip __init__, which would start Chrome
    bot = cls.__new__(cls)
    bot.username = "me"
    bot.database = db.Database()
    bot.driver = FakeDriver()
    return bot


def test_dm_row_is_saved(tmp_db):
    DMDB().save_in_db(DM("me", "hi", "Friends", 10, 2, False))
    (row,) = DMDB().get_dm_data()
    # id, account, message, group_name, num_members, num_failed_members, schedule, date
    assert row[1:7] == ("me", "hi", "Friends", 10, 2, 0)


def test_dm_run_saves_stats(tmp_db, monkeypatch):
    monkeypatch.setattr(dm_bot.time, "sleep", lambda s: None)
    bot = _bot(dm_bot.DM)
    # every user fails (no Instagram page), so the run ends with 3 members and 3 failed
    monkeypatch.setattr(bot, "_nav_user", lambda user: (_ for _ in ()).throw(RuntimeError("no page")), raising=False)
    users = [("a",), ("b",), ("c",)]
    bot.send_message_to_distribution_group("hi", users, "Friends", True, False, 1, 1, 0)
    (row,) = DMDB().get_dm_data()
    assert row[1:7] == ("me", "hi", "Friends", 3, 3, 1)
    assert bot.driver.closed == 1


def test_combination_row_is_saved(tmp_db):
    CombinationDM().save_in_db(Combination("me", "", "sunset", 6, 1, 5, 2, 0, 1, "Travel", 4))
    (row,) = CombinationDM().get_account_data("me")
    # id, account, url, hashtag, num_likes, num_failed_likes, num_followers, num_failed_followers,
    # schedule, distribution, group_name, date, skip_users
    assert row[1:11] == ("me", "", "sunset", 6, 1, 5, 2, 0, 1, "Travel")
    assert row[12] == 4


class FakeButton:
    text = "Follow"

    def click(self):
        pass


@pytest.fixture
def combination_run(tmp_db, monkeypatch):
    """A Combination run where the likes list holds two users, then runs out."""
    monkeypatch.setattr(combination_bot.time, "sleep", lambda s: None)
    bot = _bot(CombinationBot)
    lists = [[("a", FakeButton()), ("b", FakeButton())]]
    likes_found = iter([object(), None, object(), object()])  # the 2nd post of "a" can't be liked
    monkeypatch.setattr(bot, "_login", lambda: True)
    monkeypatch.setattr(bot, "_get_wanted_post", lambda *a: None)
    monkeypatch.setattr(bot, "_open_likes", lambda wait: None)
    monkeypatch.setattr(bot, "_get_scroll_box", lambda wait: None)
    monkeypatch.setattr(bot, "_get_buttons", lambda box, h, wait: (lists.pop(0) if lists else [], h, box))
    monkeypatch.setattr(bot, "check_current_url", lambda: "", raising=False)
    monkeypatch.setattr(bot, "_get_followers_number", lambda user: (500, -1, 50), raising=False)
    monkeypatch.setattr(bot, "_blocked_action_popup", lambda: False, raising=False)
    monkeypatch.setattr(bot, "_nav_user_new_tab", lambda user: None, raising=False)
    monkeypatch.setattr(bot, "_go_to_next_post", lambda wait: None)
    monkeypatch.setattr(bot, "_unfollow_users", lambda users, account_id, wait: None)
    monkeypatch.setattr(combination_bot.S, "click", lambda *a, **kw: None)
    monkeypatch.setattr(combination_bot.S, "find", lambda *a, **kw: next(likes_found))
    monkeypatch.setattr(combination_bot.S, "clickable", lambda el: FakeButton())
    return bot


def test_combination_run_saves_stats(combination_run):
    # ask for 3 follows and 2 likes each: 2 users followed, 3 of their 4 posts liked
    combination_run.combination("sunset", "", 2, 3, 1, 0, "Travel", 7, 0, 0)
    (row,) = CombinationDM().get_account_data("me")
    assert row[1:11] == ("me", "", "sunset", 4, 1, 3, 1, 0, 1, "Travel")
    assert row[12] == 0
    # the Account Actions log gets a row too: 3 asked, 2 done
    with sqlite3.connect("instabot.db") as conn:
        actions = conn.execute("SELECT action, amount, amount_success FROM account_actions").fetchall()
    assert actions == [("Combination", 3, 2)]


def test_combination_saves_stats_when_the_run_breaks(combination_run, monkeypatch):
    monkeypatch.setattr(combination_run, "_get_buttons", lambda *a: (_ for _ in ()).throw(RuntimeError("gone")))
    combination_run.combination("", "https://www.instagram.com/p/x/", 0, 3, 0, 0, "", 0, 0, 0)
    (row,) = CombinationDM().get_account_data("me")
    assert row[6:8] == (3, 3)
    assert combination_run.driver.closed == 1


def test_combination_saves_nothing_when_login_fails(combination_run, monkeypatch):
    monkeypatch.setattr(combination_run, "_login", lambda: False)
    combination_run.combination("sunset", "", 0, 3, 0, 0, "", 0, 0, 0)
    assert CombinationDM().get_account_data("me") == []


def _list_users(group_id):
    with sqlite3.connect("instabot.db") as conn:
        return [u for (u,) in conn.execute("SELECT username FROM dm_users WHERE group_id = ?", (group_id,))]


def test_combination_saves_followed_users_to_the_distribution_list(combination_run, tmp_db):
    tmp_db.create_distribution_group("Travel", "me")
    group_id = tmp_db.get_group_id_by_group_name_and_id("Travel", "me")
    combination_run.combination("sunset", "", 0, 3, 1, 0, "Travel", group_id, 0, 0)
    assert _list_users(group_id) == ["a", "b"]


def test_combination_without_distribution_saves_no_list_users(combination_run, tmp_db):
    tmp_db.create_distribution_group("Travel", "me")
    group_id = tmp_db.get_group_id_by_group_name_and_id("Travel", "me")
    combination_run.combination("sunset", "", 0, 3, 0, 0, "", group_id, 0, 0)
    assert _list_users(group_id) == []


def test_combination_skips_users(combination_run, tmp_db):
    tmp_db.create_distribution_group("Travel", "me")
    group_id = tmp_db.get_group_id_by_group_name_and_id("Travel", "me")
    combination_run.combination("sunset", "", 0, 3, 1, 0, "Travel", group_id, 0, 1)
    # "a" is skipped, only "b" is followed
    with sqlite3.connect("instabot.db") as conn:
        followed = [u for (u,) in conn.execute("SELECT username FROM unfollow")]
    assert followed == ["b"]
    assert _list_users(group_id) == ["b"]
    (row,) = CombinationDM().get_account_data("me")
    assert row[6:8] == (3, 2)
    assert row[12] == 1
