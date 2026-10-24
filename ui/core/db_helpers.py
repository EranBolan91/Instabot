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
