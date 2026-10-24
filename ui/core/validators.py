"""Shared form checks.

Each check returns an error message to show under the field, or None when
the value is fine. They are plain functions, so they're easy to combine:
``first_error(required(name, "Name"), no_apostrophe(name, "Name"))``.
"""
import re

_URL_RE = re.compile(r"^https?://[^\s/$.?#][^\s]*$", re.IGNORECASE)


def first_error(*errors):
    return next((error for error in errors if error), None)


def required(value, label):
    return None if str(value).strip() else "{} is required".format(label)


def no_spaces(value, label):
    return "{} can't contain spaces".format(label) if re.search(r"\s", value) else None


def no_apostrophe(value, label):
    # several queries in database/ paste values straight into the SQL, so a '
    # breaks them (see PROJECT_OVERVIEW.md, known issue #23)
    return "{} can't contain an apostrophe (')".format(label) if "'" in value else None


def http_url(value):
    if not value.strip():
        return "Enter a website address"
    if not _URL_RE.match(value.strip()):
        return "Enter a full address that starts with http:// or https://"
    return None


def positive(number, label):
    return None if number > 0 else "{} must be more than 0".format(label)


def unique(value, existing, label):
    """Case-insensitive: ``existing`` must not already contain ``value``."""
    wanted = value.strip().lower()
    if wanted and wanted in {item.strip().lower() for item in existing}:
        return "{} already exists".format(label)
    return None


def proxy_pair(host, port):
    if bool(host.strip()) != bool(port):
        return "Enter both the proxy host and the port, or leave both empty"
    return None
