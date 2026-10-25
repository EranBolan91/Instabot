"""Chrome options, secrets read from the environment, and SQL with apostrophes."""
import zipfile

import pytest

from bot_folder import main_bot, proxy
from database import db


@pytest.fixture
def tmp_db(tmp_path, monkeypatch):
    # Database() opens "instabot.db" in the current folder
    monkeypatch.chdir(tmp_path)
    return db.Database()


@pytest.fixture
def chrome_calls(tmp_db, monkeypatch):
    calls = []

    class FakeManager:
        def install(self):
            return "chromedriver"

    monkeypatch.setattr(main_bot, "ChromeDriverManager", FakeManager)
    monkeypatch.setattr(main_bot.webdriver, "Chrome", lambda *a, **kw: calls.append((a, kw)) or object())
    return calls


def _make_bot(headless, is_mobile):
    db.Database().save_account("n", "p", "u", "pw")
    db.Database().save_settings(1, 1, 0, False, headless, 1)
    main_bot.InstagramBot("u", "pw", is_mobile, {"proxy": "", "port": ""})


@pytest.mark.parametrize("is_mobile", [False, True])
def test_chrome_gets_its_options(chrome_calls, is_mobile):
    _make_bot(headless=True, is_mobile=is_mobile)
    (_args, kwargs), = chrome_calls
    caps = kwargs["options"].to_capabilities()["goog:chromeOptions"]
    assert "--headless" in caps["args"]
    assert kwargs["desired_capabilities"]["pageLoadStrategy"] == "eager"
    assert "chrome_options" not in kwargs
    has_desktop_agent = any(a.startswith("user-agent=") for a in caps["args"])
    assert has_desktop_agent is not is_mobile
    assert ("mobileEmulation" in caps.get("experimentalOptions", caps)) is is_mobile


def test_chrome_not_headless_when_setting_is_off(chrome_calls):
    _make_bot(headless=False, is_mobile=False)
    (_args, kwargs), = chrome_calls
    assert "--headless" not in kwargs["options"].arguments


def test_proxy_plugin_reads_env(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    for name, value in {"PROXY_HOST": "h.example", "PROXY_PORT": "1234",
                        "PROXY_USER": "me", "PROXY_PASS": "secret"}.items():
        monkeypatch.setenv(name, value)
    with zipfile.ZipFile(proxy.get_proxy_plugin()) as zp:
        js = zp.read("background.js").decode()
    assert 'host: "h.example"' in js and 'password: "secret"' in js


def test_proxy_plugin_needs_env(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("PROXY_HOST", raising=False)
    with pytest.raises(RuntimeError, match="PROXY_HOST"):
        proxy.get_proxy_plugin()


def test_no_email_without_env(monkeypatch):
    for name in ("MAILGUN_DOMAIN", "MAILGUN_API", "ALERT_EMAIL"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(main_bot.requests, "post", lambda *a, **kw: pytest.fail("sent an e-mail"))
    bot = main_bot.InstagramBot.__new__(main_bot.InstagramBot)
    bot._send_email("u", 0, "now", "Test")


def test_names_with_apostrophes(tmp_db):
    name = "o'brien"
    tmp_db.save_account("n", "p", name, "pw")
    user_id = tmp_db.get_user_id(name)
    assert user_id

    tmp_db.create_distribution_group("it's a group", name)
    assert [g for g in tmp_db.get_distribution_lists_by_username(name) if "it's a group" in g]
    assert tmp_db.get_users_from_dm_users("it's a group", name) == []
    assert tmp_db.remove_group_from_distribution_list("it's a group", name) is not False
    assert not [g for g in tmp_db.get_distribution_lists_by_username(name) if "it's a group" in g]

    assert tmp_db.update_account(user_id, "n", "p", "d'arcy", "pw")
    assert tmp_db.get_user_id("d'arcy") == user_id
    assert tmp_db.delete_account("d'arcy")
    assert tmp_db.get_accounts() == []


def test_injection_does_not_delete_everything(tmp_db):
    tmp_db.save_account("n", "p", "a", "pw")
    tmp_db.save_account("n", "p", "b", "pw")
    tmp_db.delete_account("x' OR '1'='1")
    assert len(tmp_db.get_accounts()) == 2
