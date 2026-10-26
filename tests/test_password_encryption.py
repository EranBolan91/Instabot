import sqlite3
import uuid

import pytest
from cryptography.fernet import Fernet

from database.db import Database
from database.proxy.proxy import Proxy as ProxyDB
from models.proxy import Proxy as ProxyModel
from utils import crypto


def stored_password(username):
    with sqlite3.connect("instabot.db") as conn:
        return conn.execute("SELECT password FROM accounts WHERE username = ?", (username,)).fetchone()[0]


def account(username):
    return next(row for row in Database().get_accounts() if row[3] == username)


def test_round_trip():
    token = crypto.encrypt("s3cret pässword")
    assert crypto.is_encrypted(token) and "s3cret" not in token
    assert crypto.decrypt(token) == "s3cret pässword"
    assert crypto.encrypt(token) == token  # never encrypted twice
    assert crypto.encrypt("") == "" and crypto.decrypt("") == ""
    assert crypto.decrypt("old plain") == "old plain"


def test_saved_password_is_encrypted_on_disk(workdir):
    Database().save_account("Alice", "050", "alice", "s3cret")
    assert crypto.is_encrypted(stored_password("alice"))
    assert "s3cret" not in (workdir / "instabot.db").read_bytes().decode("latin-1")
    assert account("alice")[4] == "s3cret"


def test_updated_password_is_encrypted(workdir):
    database = Database()
    database.save_account("Alice", "050", "alice", "old")
    assert database.update_account(account("alice")[0], "Alice", "050", "alice", "new")
    assert crypto.is_encrypted(stored_password("alice"))
    assert account("alice")[4] == "new"


def test_plain_text_passwords_are_migrated_on_start(workdir):
    Database()
    with sqlite3.connect("instabot.db") as conn:
        conn.execute("INSERT INTO accounts (name, phone, username, password) VALUES ('Bob', '', 'bob', 'legacy')")
        conn.execute("INSERT INTO accounts (name, phone, username, password) VALUES ('Eve', '', 'eve', '')")
    Database()
    assert crypto.is_encrypted(stored_password("bob"))
    assert stored_password("eve") == ""
    assert account("bob")[4] == "legacy"
    once = stored_password("bob")
    Database()
    assert stored_password("bob") == once  # running again changes nothing


def test_lost_key_gives_empty_password_not_a_crash(workdir, monkeypatch):
    Database().save_account("Alice", "050", "alice", "s3cret")
    monkeypatch.setenv(crypto.ENV_KEY, Fernet.generate_key().decode())
    crypto.reset()
    assert account("alice")[4] == ""


def test_key_file_used_when_no_env_key_or_password_store(workdir, monkeypatch):
    monkeypatch.delenv(crypto.ENV_KEY)
    monkeypatch.setattr(crypto, "load_dotenv", lambda: None)
    monkeypatch.setattr(crypto, "_keyring_key", lambda: None)
    crypto.reset()
    token = crypto.encrypt("pw")
    assert (workdir / crypto.KEY_FILE).exists()
    crypto.reset()
    assert crypto.decrypt(token) == "pw"  # same key read back from the file


def test_damaged_value_raises_decrypt_error():
    with pytest.raises(crypto.DecryptError):
        crypto.decrypt(crypto.PREFIX + "not-a-token")



# made up at run time, so the tests hold no hard-coded proxy credentials
HOST, OTHER_HOST = "proxy.example", "other.example"
PROXY_SECRET = uuid.uuid4().hex


def stored_proxy_value(host):
    with sqlite3.connect("instabot.db") as conn:
        return conn.execute("SELECT password FROM proxy WHERE host = ?", (host,)).fetchone()[0]


def proxy_row(host):
    return next(row for row in Database().get_proxy_data() if row[1] == host)


def save_proxy(host, secret):
    return ProxyDB().save_in_db(ProxyModel(host, "bob", secret, 8080))


def test_saved_proxy_password_is_encrypted_on_disk(workdir):
    Database()
    assert save_proxy(HOST, PROXY_SECRET)
    assert save_proxy(OTHER_HOST, "")
    assert crypto.is_encrypted(stored_proxy_value(HOST))
    assert stored_proxy_value(OTHER_HOST) == ""
    assert PROXY_SECRET not in (workdir / "instabot.db").read_bytes().decode("latin-1")
    assert proxy_row(HOST)[3] == PROXY_SECRET


def test_plain_text_proxy_passwords_are_migrated_on_start(workdir):
    Database()
    with sqlite3.connect("instabot.db") as conn:
        conn.execute("INSERT INTO proxy (host, username, password, port) VALUES (?, 'bob', ?, 80)",
                     (HOST, PROXY_SECRET))
    Database()
    assert crypto.is_encrypted(stored_proxy_value(HOST))
    assert proxy_row(HOST)[3] == PROXY_SECRET
    once = stored_proxy_value(HOST)
    Database()
    assert stored_proxy_value(HOST) == once


def test_lost_key_gives_empty_proxy_password(workdir, monkeypatch):
    Database()
    save_proxy(HOST, PROXY_SECRET)
    monkeypatch.setenv(crypto.ENV_KEY, Fernet.generate_key().decode())
    crypto.reset()
    assert proxy_row(HOST)[3] == ""
