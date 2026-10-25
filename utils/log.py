"""One place to set up logging for the app and the bots.

Usage in a module:

    from utils.log import get_logger
    log = get_logger(__name__)
    ...
    except Exception:
        log.exception("DM: could not send to %s", username)

Errors and warnings go to stderr, which the app's log panel shows in red,
and everything (debug too) goes to logs/instabot.log with a timestamp.
"""
import logging
import os
import sys
from logging.handlers import RotatingFileHandler

ROOT = "instabot"
LOG_DIR = "logs"
LOG_FILE = "instabot.log"

_FILE_FORMAT = "%(asctime)s %(levelname)-7s [%(threadName)s] %(name)s: %(message)s"
_CONSOLE_FORMAT = "%(levelname)s: %(message)s"


def get_logger(name):
    """A logger under the app's root logger, e.g. instabot.bot_folder.dm.dm_bot."""
    if name == ROOT or name.startswith(ROOT + "."):
        return logging.getLogger(name)
    return logging.getLogger("{}.{}".format(ROOT, name))


class _CurrentStderrHandler(logging.StreamHandler):
    """Writes to whatever sys.stderr is at the time of the call.

    The UI swaps sys.stderr for its log bridge after start-up, so a handler
    that kept the original stream would skip the log panel.
    """

    def __init__(self):
        super().__init__(sys.stderr)

    @property
    def stream(self):
        return sys.stderr

    @stream.setter
    def stream(self, value):
        pass  # always follow sys.stderr


def setup_logging(log_dir=LOG_DIR, console_level=logging.WARNING):
    """Call once at start-up. Safe to call again: it doesn't add handlers twice."""
    logger = logging.getLogger(ROOT)
    if getattr(logger, "_instabot_configured", False):
        return logger
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    console = _CurrentStderrHandler()
    console.setLevel(console_level)
    console.setFormatter(logging.Formatter(_CONSOLE_FORMAT))
    logger.addHandler(console)

    try:
        os.makedirs(log_dir, exist_ok=True)
        file_handler = RotatingFileHandler(os.path.join(log_dir, LOG_FILE), maxBytes=2 * 1024 * 1024,
                                           backupCount=3, encoding="utf-8")
    except OSError as e:
        logger.warning("Logging to a file is off: %s", e)
    else:
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(_FILE_FORMAT))
        logger.addHandler(file_handler)

    logger._instabot_configured = True
    return logger
