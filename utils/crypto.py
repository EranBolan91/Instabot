"""Encrypts the passwords saved in instabot.db (Instagram accounts and proxies).

Passwords are stored as "enc:v1:<Fernet token>" (AES with an HMAC check, from
the cryptography package). The key never goes in the database. It comes from,
in order:

1. the INSTABOT_SECRET_KEY environment variable (or .env), if set
2. the operating system's password store (Windows Credential Manager, macOS
   Keychain, Linux Secret Service), through the keyring package
3. a file named instabot.key next to instabot.db, if there is no password store

The key is made on first use. If it is lost, the saved passwords can't be read
any more and have to be typed in again in Main → Accounts (and the proxies
added again in Settings → Proxies).
"""
import os
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from dotenv import load_dotenv

from utils.log import get_logger

log = get_logger(__name__)

PREFIX = "enc:v1:"
ENV_KEY = "INSTABOT_SECRET_KEY"
KEYRING_SERVICE = "Instabot"
KEYRING_NAME = "password-key"
KEY_FILE = "instabot.key"

_fernet = None


class DecryptError(Exception):
    """A saved password could not be decrypted (wrong or lost key, or damaged data)."""


def _keyring_key():
    """The key from the OS password store, made there if missing. None if there is no usable store."""
    try:
        import keyring
        from keyring.backends.fail import Keyring as NoKeyring

        if isinstance(keyring.get_keyring(), NoKeyring):
            return None
        key = keyring.get_password(KEYRING_SERVICE, KEYRING_NAME)
        if not key:
            key = Fernet.generate_key().decode()
            keyring.set_password(KEYRING_SERVICE, KEYRING_NAME, key)
            if keyring.get_password(KEYRING_SERVICE, KEYRING_NAME) != key:
                return None
            log.info("Made a new password key in the system password store")
        return key
    except Exception:
        log.warning("Could not use the system password store, using %s instead", KEY_FILE, exc_info=True)
        return None


def _file_key():
    path = Path(KEY_FILE)
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    key = Fernet.generate_key().decode()
    path.write_text(key, encoding="utf-8")
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    log.info("Made a new password key in %s. Keep it with instabot.db, and out of git.", path.resolve())
    return key


def _get_fernet():
    global _fernet
    if _fernet is None:
        load_dotenv()
        key = os.getenv(ENV_KEY) or _keyring_key() or _file_key()
        _fernet = Fernet(key.encode())
    return _fernet


def reset():
    """Forget the cached key (tests use this after changing where the key comes from)."""
    global _fernet
    _fernet = None


def is_encrypted(value):
    return isinstance(value, str) and value.startswith(PREFIX)


def encrypt(password):
    """The value to store for a password. Empty stays empty, already-encrypted stays as is."""
    if not password or is_encrypted(password):
        return password
    return PREFIX + _get_fernet().encrypt(password.encode("utf-8")).decode("ascii")


def decrypt(value):
    """The password from a stored value. Old plain-text values are returned unchanged."""
    if not is_encrypted(value):
        return value
    try:
        return _get_fernet().decrypt(value[len(PREFIX):].encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError) as error:
        raise DecryptError("saved password can't be decrypted with this key") from error
