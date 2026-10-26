"""Fixes from the October 2026 code review. No Chrome is opened."""
import sqlite3

import pytest

from bot_folder import main_bot
from bot_folder.combination import combination_bot
from bot_folder.combination.combination_bot import CombinationBot
from bot_folder.dm import dm_bot
from bot_folder.hash_tag import hash_tag_bot
from bot_folder.hash_tag.hash_tag_bot import HashTagBot
from bot_folder.location import location_bot
from bot_folder.location.location_bot import LocationBot
from database import db
from database.dm.dm import DMDB
from database.hashtag.hashtag import HashtagDB


class ClosedError(Exception):
    """What Selenium raises when Chrome is already gone."""


class FakeDriver:
    """Fails like the real one when used after Chrome was closed."""

    def __init__(self, tabs=1):
        self.window_handles = list(range(tabs))
        self.current = 0
        self.quits = 0
        self.closes = 0
        self.switch_to = self
        self.current_url = "https://www.instagram.com/p/x/"
        self.scripts = []

    def _alive(self):
        if self.quits or self.current not in self.window_handles:
            raise ClosedError("no such window")

    def window(self, handle):
        if handle not in self.window_handles:
            raise ClosedError("no such window")
        self.current = handle

    def get(self, url):
        self._alive()

    def delete_all_cookies(self):
        self._alive()

    def close(self):
        self._alive()
        self.closes += 1
        self.window_handles.remove(self.current)

    def quit(self):
        self.quits += 1

    def execute_script(self, script, *args):
        self.scripts.append((script, args))

    def save_screenshot(self, path):
        return True


@pytest.fixture
def tmp_db(workdir):
    database = db.Database()
    database.save_account("n", "p", "me", "pw")
    database.save_settings(0, 0, 0, 0, 0, 0)
    return database


def _bot(cls, driver=None):
    # skip __init__, which would start Chrome
    bot = cls.__new__(cls)
    bot.username = "me"
    bot.database = db.Database()
    bot.driver = driver or FakeDriver()
    return bot


@pytest.fixture
def no_sleep(monkeypatch):
    for module in (main_bot, hash_tag_bot, location_bot, dm_bot, combination_bot):
        monkeypatch.setattr(module.time, "sleep", lambda s: None)


# ---------- 1. A post with comments turned off doesn't end the run ----------

def test_comment_failure_returns_false(no_sleep, monkeypatch):
    bot = _bot(main_bot.InstagramBot)

    monkeypatch.setattr(main_bot.S, "get", lambda *a, **kw: (_ for _ in ()).throw(LookupError("no comment box")))
    assert bot._comment_post(["nice"]) is False


def _hashtag_run(bot, monkeypatch, blocked_after=None):
    calls = {"comment": 0, "post": 0}
    monkeypatch.setattr(bot, "_login", lambda: True)
    monkeypatch.setattr(hash_tag_bot.S, "click", lambda *a, **kw: None)
    monkeypatch.setattr(bot, "_like_post", lambda: None)
    monkeypatch.setattr(bot, "_follow_user", lambda *a: None)

    def comment(split_comment):
        calls["comment"] += 1
        return main_bot.InstagramBot._comment_post(bot, split_comment)

    def check_blocked():
        calls["post"] += 1
        return blocked_after is not None and calls["post"] >= blocked_after

    monkeypatch.setattr(bot, "_comment_post", comment)
    monkeypatch.setattr(bot, "_check_if_blocked", check_blocked)
    monkeypatch.setattr(bot, "_send_email", lambda *a: None)
    # the comment box is never there: comments are turned off on every post
    monkeypatch.setattr(main_bot.S, "get", lambda *a, **kw: (_ for _ in ()).throw(LookupError("no comment box")))
    return calls


def test_hashtag_goes_on_when_comments_are_off(tmp_db, no_sleep, monkeypatch):
    bot = _bot(HashTagBot)
    calls = _hashtag_run(bot, monkeypatch)
    bot.search_hash_tag("sunset", "3", 0, 1, 0, ["nice"], 0, "", 0, 0)
    assert calls["comment"] == 3
    assert bot.driver.quits == 1


def test_location_goes_on_when_comments_are_off(tmp_db, no_sleep, monkeypatch):
    bot = _bot(LocationBot)
    calls = _hashtag_run(bot, monkeypatch)
    monkeypatch.setattr(location_bot.S, "click", lambda *a, **kw: None)
    bot.search_location_by_url("https://www.instagram.com/explore/locations/1/", "3", 0, 0, 1, ["nice"], 0, "", 0, 0)
    assert calls["comment"] == 3


# ---------- 3. A block doesn't crash the run ----------

def test_hashtag_block_ends_cleanly_and_saves_stats(tmp_db, no_sleep, monkeypatch):
    bot = _bot(HashTagBot)
    calls = _hashtag_run(bot, monkeypatch, blocked_after=2)
    # no exception: the job ends as done, not failed
    bot.search_hash_tag("sunset", "5", 1, 0, 0, [], 0, "", 0, 0)
    assert calls["post"] == 2
    assert bot.driver.quits == 1
    assert len(HashtagDB().get_hashtag_data()) == 1


def test_close_browser_is_safe_when_chrome_is_gone():
    bot = _bot(main_bot.InstagramBot)
    bot.driver.quit()
    bot._close_browser()  # no exception
    assert bot.driver.quits == 2


def test_combination_unfollow_block_closes_one_tab_and_reports_it(tmp_db, no_sleep, monkeypatch):
    bot = _bot(CombinationBot, FakeDriver(tabs=2))
    monkeypatch.setattr(bot, "_unfollow", lambda user, account_id, wait: (False, True))
    monkeypatch.setattr(bot, "_send_email", lambda *a: None)
    blocked = bot._unfollow_users([(1, 1, "a"), (2, 1, "b")], 1, None)
    assert blocked is True
    # only the unfollow tab was closed; the likes list tab is still there
    assert bot.driver.window_handles == [0]
    assert bot.driver.closes == 1


def test_combination_stops_when_blocked_while_unfollowing(tmp_db, no_sleep, monkeypatch):
    bot = _bot(CombinationBot)
    monkeypatch.setattr(bot, "_login", lambda: True)
    monkeypatch.setattr(bot, "_get_wanted_post", lambda *a: None)
    monkeypatch.setattr(bot, "_open_likes", lambda wait: None)
    monkeypatch.setattr(bot, "_get_scroll_box", lambda wait: None)
    lists = [[("a", None)]]
    monkeypatch.setattr(bot, "_get_buttons", lambda box, h, wait: (lists.pop(0) if lists else [], h, box))
    rounds = []
    monkeypatch.setattr(bot, "_unfollow_users", lambda users, account_id, wait: rounds.append(1) or True)
    # 'a' has no Follow button, so the likes list runs out; then the unfollow round reports a block
    bot.combination("sunset", "", 0, 3, 0, 0, "", 0, 0, 0)
    assert rounds == [1]
    assert bot.driver.quits == 1


# ---------- 2. DM messages each user once ----------

def test_distribution_list_holds_each_user_once(tmp_db):
    tmp_db.create_distribution_group("Friends", "me")
    group_id = tmp_db.get_group_id_by_group_name_and_id("Friends", "me")
    tmp_db.add_username_to_distribution_group("a", group_id)
    tmp_db.add_username_to_distribution_group("a", group_id)
    assert tmp_db.get_users_from_dm_users("Friends", "me") == [("a",)]


def test_dm_messages_a_duplicate_user_once(tmp_db, no_sleep, monkeypatch):
    bot = _bot(dm_bot.DM)
    visited = []
    monkeypatch.setattr(bot, "_nav_user", visited.append)
    monkeypatch.setattr(dm_bot.S, "click", lambda *a, **kw: None)
    box = type("Box", (), {"send_keys": lambda self, *keys: None})()
    monkeypatch.setattr(dm_bot.S, "get", lambda *a, **kw: box)
    monkeypatch.setattr(dm_bot.S, "find", lambda *a, **kw: None)
    monkeypatch.setattr(bot, "_type_message", lambda box, message: None)
    monkeypatch.setattr(bot, "_check_if_blocked", lambda: False)
    # an older database can still hold the same user twice
    users = [("a",), ("b",), ("a",)]
    bot.send_message_to_distribution_group("hi", users, "Friends", 0, False, 1, 1, -1)
    assert sorted(visited) == ["a", "b"]
    (row,) = DMDB().get_dm_data()
    assert row[4:6] == (2, 0)
    assert bot.driver.quits == 1


# ---------- 7. The alert e-mail can't hang the job ----------

def test_email_has_a_time_limit_and_works_without_a_screenshot(workdir, monkeypatch):
    for name, value in {"MAILGUN_DOMAIN": "mg.example", "MAILGUN_API": "k", "ALERT_EMAIL": "a@example.com"}.items():
        monkeypatch.setenv(name, value)
    sent = []

    class Response:
        def raise_for_status(self):
            pass

    monkeypatch.setattr(main_bot.requests, "post", lambda *a, **kw: sent.append(kw) or Response())
    bot = _bot(main_bot.InstagramBot)
    bot._send_email("me", 0, "now", "Test")
    (kwargs,) = sent
    assert kwargs["timeout"] == main_bot.EMAIL_TIMEOUT
    assert kwargs["files"] == []


def test_email_failure_does_not_stop_the_job(workdir, monkeypatch):
    for name in ("MAILGUN_DOMAIN", "MAILGUN_API", "ALERT_EMAIL"):
        monkeypatch.setenv(name, "x")
    monkeypatch.setattr(main_bot.requests, "post",
                        lambda *a, **kw: (_ for _ in ()).throw(main_bot.requests.Timeout("no answer")))
    _bot(main_bot.InstagramBot)._send_email("me", 0, "now", "Test")  # no exception


# ---------- Smaller hardening ----------

def test_new_tab_passes_the_address_as_an_argument():
    bot = _bot(main_bot.InstagramBot)
    bot._nav_user_new_tab("o'brien")
    ((script, args),) = bot.driver.scripts
    assert "o'brien" not in script
    assert args and "o'brien" in args[0]


def test_main_works_from_its_own_folder():
    # instabot.db and instabot.key must not depend on the folder the app is started from
    import pathlib

    source = (pathlib.Path(__file__).parent.parent / "main.py").read_text()
    assert "os.chdir(os.path.dirname(os.path.abspath(__file__)))" in source
    assert source.index("os.chdir(") < source.index("from ui.app import")
