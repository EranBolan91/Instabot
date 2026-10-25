"""Errors in the bots and the database are logged instead of silently swallowed."""
import io
import logging
import sqlite3
import sys

import pytest
from selenium.common.exceptions import NoSuchElementException

from bot_folder.dm import dm_bot
from database import db
from utils import log as log_module


@pytest.fixture
def fresh_logger():
    """Undo setup_logging() afterwards, so other tests keep pytest's log capture."""
    logger = logging.getLogger(log_module.ROOT)
    yield logger
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()
    logger.propagate = True
    logger.setLevel(logging.NOTSET)
    logger._instabot_configured = False


def test_setup_logging_writes_file_and_follows_stderr(tmp_path, monkeypatch, fresh_logger):
    log_module.setup_logging(log_dir=str(tmp_path / "logs"))
    log_module.setup_logging(log_dir=str(tmp_path / "logs"))  # a second call adds nothing
    assert len(fresh_logger.handlers) == 2

    # the UI replaces sys.stderr after start-up; errors must reach the new stream
    panel = io.StringIO()
    monkeypatch.setattr(sys, "stderr", panel)
    log = log_module.get_logger("tests.example")
    log.debug("only in the file")
    try:
        raise ValueError("boom")
    except ValueError:
        log.exception("DM me: something broke")

    shown = panel.getvalue()
    assert "ERROR: DM me: something broke" in shown
    assert "ValueError: boom" in shown  # with the traceback
    assert "only in the file" not in shown

    for handler in fresh_logger.handlers:
        handler.flush()
    written = (tmp_path / "logs" / "instabot.log").read_text(encoding="utf-8")
    assert "only in the file" in written and "ValueError: boom" in written


def test_get_logger_names():
    assert log_module.get_logger("database.db").name == "instabot.database.db"
    assert log_module.get_logger("instabot").name == "instabot"


@pytest.fixture
def tmp_db(workdir):
    database = db.Database()
    database.save_account("n", "p", "me", "pw")
    return database


def test_database_error_is_logged(tmp_db, caplog):
    conn = sqlite3.connect(tmp_db.database_name)
    conn.execute("DROP TABLE accounts")
    conn.commit()
    conn.close()
    with caplog.at_level(logging.ERROR, logger="instabot"):
        # no Database() here: creating one would make the table again
        assert tmp_db.update_account(1, "n", "p", "me", "pw") is False
    (record,) = caplog.records
    assert record.getMessage() == "Database: could not update account me"
    assert record.exc_info is not None


class _FakeDriver:
    window_handles = [0]

    def delete_all_cookies(self):
        pass

    def close(self):
        pass


def _dm_bot():
    # skip __init__, which would start Chrome
    bot = dm_bot.DM.__new__(dm_bot.DM)
    bot.username = "me"
    bot.database = db.Database()
    bot.driver = _FakeDriver()
    return bot


class _NothingOnPage:
    """Instagram selectors that never find anything."""

    def find(self, *args, **kwargs):
        return None

    def get(self, root, key, timeout=7):
        raise NoSuchElementException("Instagram selector '{}' found nothing".format(key))

    def click(self, root, key, timeout=7):
        return self.get(root, key)


def test_dm_failed_send_is_logged(tmp_db, monkeypatch, caplog):
    monkeypatch.setattr(dm_bot.time, "sleep", lambda s: None)
    monkeypatch.setattr(dm_bot, "S", _NothingOnPage())
    bot = _dm_bot()
    monkeypatch.setattr(bot, "_nav_user", lambda user: None, raising=False)
    monkeypatch.setattr(bot, "_check_if_blocked", lambda: False, raising=False)
    with caplog.at_level(logging.DEBUG, logger="instabot"):
        bot.send_message_to_distribution_group("hi", [("a",)], "Friends", False, False, 1, 1, 5)
    warnings = [r for r in caplog.records if r.levelno >= logging.WARNING]
    assert [r.getMessage() for r in warnings] == ["DM me: could not send the message to a"]


def test_dm_run_that_breaks_is_logged(tmp_db, monkeypatch, caplog):
    monkeypatch.setattr(dm_bot.time, "sleep", lambda s: None)
    bot = _dm_bot()
    monkeypatch.setattr(bot, "_nav_user", lambda user: (_ for _ in ()).throw(RuntimeError("no page")), raising=False)
    with caplog.at_level(logging.ERROR, logger="instabot"):
        bot.send_message_to_distribution_group("hi", [("a",)], "Friends", False, False, 1, 1, 5)
    (record,) = caplog.records
    assert record.getMessage() == "DM me: sending to distribution group Friends stopped"
    assert "no page" in caplog.text
