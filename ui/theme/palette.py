"""Color tokens shared by the stylesheet and Python code.

The tokens are defined once, in the header comment of ``dark.qss``
(``@name: #RRGGBB;`` lines). This module reads them, so Python code
(icons, status chips, log colors) uses exactly the same values.
"""
import re
from pathlib import Path

THEME_DIR = Path(__file__).resolve().parent

_TOKEN_RE = re.compile(r"^\s*\*?\s*@([a-z_]+)\s*:\s*(#[0-9A-Fa-f]{6})\s*;", re.MULTILINE)


def _read(theme):
    return (THEME_DIR / "{}.qss".format(theme)).read_text(encoding="utf-8")


def load_tokens(theme="dark"):
    return dict(_TOKEN_RE.findall(_read(theme)))


def load_stylesheet(theme="dark"):
    text = _read(theme)
    tokens = load_tokens(theme)
    # longest names first, so "@accent_hover" isn't clobbered by "@accent"
    for name in sorted(tokens, key=len, reverse=True):
        text = text.replace("@" + name, tokens[name])
    return text


TOKENS = load_tokens()


def color(name):
    return TOKENS[name]
