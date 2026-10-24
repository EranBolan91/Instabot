"""Named access to DB rows.

The database layer returns plain tuples and the old UI read them by index
(``account[3]``). These helpers give those indexes names. The column order
is the schema in PROJECT_OVERVIEW.md section 6.1 and must not change.
"""

# accounts: id, name, phone, username, password, creation_date, last_login
ACCOUNT_ID = 0
ACCOUNT_NAME = 1
ACCOUNT_PHONE = 2
ACCOUNT_USERNAME = 3
ACCOUNT_PASSWORD = 4
ACCOUNT_CREATED = 5
ACCOUNT_LAST_LOGIN = 6


def account_id(row):
    return row[ACCOUNT_ID]


def account_name(row):
    return row[ACCOUNT_NAME]


def account_phone(row):
    return row[ACCOUNT_PHONE]


def account_username(row):
    return row[ACCOUNT_USERNAME]


def account_password(row):
    return row[ACCOUNT_PASSWORD]


def account_created(row):
    return row[ACCOUNT_CREATED]


def account_last_login(row):
    return row[ACCOUNT_LAST_LOGIN]


# settings (one row, id=1): id, amount_likes, amount_followers, is_schedule,
# schedule_hour, modify, headless, amount_posts
SETTINGS_LIKES = 1
SETTINGS_FOLLOWERS = 2
SETTINGS_IS_SCHEDULE = 3
SETTINGS_SCHEDULE_HOUR = 4
SETTINGS_HEADLESS = 6
SETTINGS_POSTS = 7

# groups (distribution lists): id, group_name, user_id
GROUP_ID = 0
GROUP_NAME = 1

# proxy: id, host, username, password, port
PROXY_ID = 0
PROXY_HOST = 1
PROXY_USERNAME = 2
PROXY_PASSWORD = 3
PROXY_PORT = 4

# website: id, website, modify
WEBSITE_ID = 0
WEBSITE_URL = 1


def group_id(row):
    return row[GROUP_ID]


def group_name(row):
    return row[GROUP_NAME]


def as_int(value):
    """Settings columns hold ints, numeric text ('0') or booleans; read any of them."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return 1 if str(value).strip().lower() == "true" else 0
