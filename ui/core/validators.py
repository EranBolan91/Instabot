"""Shared form checks.

Each check returns an error message to show under the field, or None when
the value is fine. They are plain functions, so they're easy to combine:
``first_error(required(name, "Name"), no_spaces(name, "Name"))``.
"""
import re

_URL_RE = re.compile(r"^https?://[^\s/$.?#][^\s]*$", re.IGNORECASE)


def first_error(*errors):
    return next((error for error in errors if error), None)


def required(value, label):
    return None if str(value).strip() else "{} is required".format(label)


def no_spaces(value, label):
    return "{} can't contain spaces".format(label) if re.search(r"\s", value) else None


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


_INSTAGRAM_RE = re.compile(r"^https?://(www\.)?instagram\.com/\S+$", re.IGNORECASE)


def instagram_url(value, example):
    if not value.strip():
        return "Enter the address"
    if not _INSTAGRAM_RE.match(value.strip()):
        return "Enter a full Instagram address, e.g. {}".format(example)
    return None


def instagram_location_url(value):
    error = instagram_url(value, "https://www.instagram.com/explore/locations/212988663/new-york-new-york/")
    if error:
        return error
    if "/explore/locations/" not in value:
        return "This isn't a location page. Its address contains /explore/locations/"
    return None


def hashtag(value):
    """A leading # is allowed (the page strips it)."""
    tag = value.strip().lstrip("#")
    return first_error(required(tag, "Hashtag"), no_spaces(tag, "A hashtag"),
                       "A hashtag can only contain letters, numbers and _" if re.search(r"[^\w]", tag) else None)
