"""Checks the Instagram selectors against the real site, without doing anything there.

Opens the pages the bots use and reports, for each selector, whether it still
finds something. It only looks: the only clicks open things (the followers
counter, a post, its likes, Message, and the "Following" menu, which is closed
again with Escape). It never clicks Follow, Unfollow, Like, Comment or Send.
Needs a driver that is already logged in.
"""
import time
from datetime import date

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from utils.instagram_selectors import S

OK, MISSING, NOT_CHECKED = "ok", "missing", "not checked"
NOT_FOLLOWED_PROFILE = "instagram"
HASHTAG = "sunset"

# found only in situations the check can't create safely (a block, a private
# profile you requested, a typed message, being logged out, ...)
CANNOT_CHECK = {
    "login.username_input": "checked when a bot logs in",
    "login.password_input": "checked when a bot logs in",
    "login.error_message": "only shown after a wrong password",
    "login.not_now_button": "only shown right after logging in",
    "profile.follow_back_button": "needs a profile that follows you and you don't follow",
    "profile.requested_button": "needs a private profile you asked to follow",
    "post.unlike_button": "needs a post you liked",
    "dm.send_button": "only shown after typing a message",
    "block.popup": "only shown when Instagram blocks an action",
    "block.popup_ok": "only shown when Instagram blocks an action",
    "search.input": "not used by the bots",
}


class _Report:
    def __init__(self, log):
        self.results = {key: (NOT_CHECKED, CANNOT_CHECK.get(key, "page not reached")) for key in S.keys()}
        self.log = log

    def check(self, root, key, timeout=5, note=""):
        found = S.find(root, key, timeout)
        self.set(key, OK if found is not None else MISSING, note)
        return found

    def set(self, key, status, note=""):
        self.results[key] = (status, note)
        self.log("  {:<9} {}{}".format(status, key, "  ({})".format(note) if note else ""))


def _escape(driver):
    driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
    time.sleep(2)


def _step(report, title, function, *args):
    report.log(title)
    try:
        return function(report, *args)
    except Exception as error:  # one broken page shouldn't stop the others
        report.log("  error on this page: {}".format(error))
        return None


def check_selectors(driver, username, log=print):
    """Visit the pages and return {selector key: (status, note)}."""
    report = _Report(log)
    _step(report, "Home", _home, driver)
    followed = _step(report, "Your profile and lists", _own_profile, driver, username)
    if followed:
        _step(report, "A profile you follow (@{})".format(followed), _followed_profile, driver, followed)
    _step(report, "A profile you don't follow (@{})".format(NOT_FOLLOWED_PROFILE), _other_profile, driver)
    _step(report, "A post (#{})".format(HASHTAG), _post, driver)
    _step(report, "A page that doesn't exist", _not_found, driver)
    return report.results


def mark_checked(results, selectors=S, today=None):
    """Store today's date as "checked" on every selector that was found."""
    today = (today or date.today()).isoformat()
    data = selectors.data
    for key, (status, _note) in results.items():
        if status == OK:
            group, name = key.split(".")
            data["selectors"][group][name]["checked"] = today
    selectors.save(data)


# ---------- Pages ----------

def _home(report, driver):
    driver.get(S.url("home"))
    time.sleep(5)
    report.check(driver, "login.logged_in_marker")


def _own_profile(report, driver, username):
    driver.get(S.url("profile", username=username))
    time.sleep(5)
    for key in ("profile.posts_counter", "profile.followers_counter", "profile.following_counter",
                "profile.picture", "profile.first_post"):
        report.check(driver, key)

    followed = None
    for counter in ("profile.followers_counter", "profile.following_counter"):
        driver.get(S.url("profile", username=username))
        time.sleep(5)
        S.click(driver, counter)
        time.sleep(5)
        report.check(driver, "dialog.box")
        report.check(driver, "dialog.scroll_area")
        report.check(driver, "dialog.close_button")
        rows = S.dialog_rows(driver)
        report.set("dialog.user_link", OK if rows else MISSING, "{} rows".format(len(rows)))
        with_button = [name for name, button in rows if button is not None]
        report.set("dialog.row_button", OK if with_button else MISSING,
                   "{} of {} rows have a button".format(len(with_button), len(rows)))
        if counter == "profile.following_counter":
            followed = next((name for name, _ in rows if name != username), None)
        _escape(driver)
    return followed


def _followed_profile(report, driver, profile):
    driver.get(S.url("profile", username=profile))
    time.sleep(5)
    report.check(driver, "profile.following_button")
    if S.exists(driver, "profile.following_button"):
        # opens the menu that holds Unfollow; closed again without choosing anything
        S.click(driver, "profile.following_button")
        time.sleep(3)
        report.check(driver, "profile.unfollow_confirm", note="menu closed again, nothing chosen")
        _escape(driver)
    driver.get(S.url("profile", username=profile))
    time.sleep(5)
    if report.check(driver, "profile.message_button") is not None:
        S.click(driver, "profile.message_button")
        time.sleep(8)
        report.check(driver, "dm.message_input", timeout=8, note="nothing typed")


def _other_profile(report, driver):
    driver.get(S.url("profile", username=NOT_FOLLOWED_PROFILE))
    time.sleep(5)
    if S.exists(driver, "profile.following_button"):
        report.set("profile.follow_button", NOT_CHECKED, "you follow @{}".format(NOT_FOLLOWED_PROFILE))
    else:
        report.check(driver, "profile.follow_button")


def _post(report, driver):
    driver.get(S.url("hashtag", tag=HASHTAG))
    time.sleep(6)
    if report.check(driver, "grid.first_post") is None:
        return
    S.click(driver, "grid.first_post")
    time.sleep(5)
    liked = S.exists(driver, "post.unlike_button")
    if liked:
        report.set("post.unlike_button", OK)
        report.set("post.like_button", NOT_CHECKED, "this post is already liked")
    else:
        report.check(driver, "post.like_button")
    for key in ("post.next_button", "post.close_button", "post.comment_input", "post.author_link"):
        report.check(driver, key)
    if S.exists(driver, "post.author_follow_button", timeout=3):
        report.set("post.author_follow_button", OK)
    else:
        report.set("post.author_follow_button", NOT_CHECKED, "you may follow this author")
    if report.check(driver, "post.likes_link") is not None:
        S.click(driver, "post.likes_link")
        time.sleep(6)
        rows = S.dialog_rows(driver)
        report.log("  the likes list shows {} rows".format(len(rows)))
        _escape(driver)


def _not_found(report, driver):
    driver.get(S.url("profile", username="this-user-does-not-exist-9f3k2"))
    time.sleep(5)
    report.check(driver, "profile.not_found_title")
