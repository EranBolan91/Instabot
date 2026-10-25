from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from utils.utils import Utils as utils
from utils.instagram_selectors import S
#from seleniumwire import webdriver
from selenium import webdriver
import time, random, requests
from database import db
import os
from utils.log import get_logger

log = get_logger(__name__)

class InstagramBot:
    def __init__(self, username, password, is_mobile, proxy_dict):
        self.database = db.Database()
        self.username = username
        self.password = password
        self.base_url = 'https://www.instagram.com'

        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument("--disable-notifications")
        headless = db.Database().get_data_from_settings()[6]
        if headless:
            options.add_argument("--headless")
        if is_mobile:
            options.add_experimental_option("mobileEmulation", {"deviceName": "Nexus 5"})
        else:
            # the phone emulation sets its own user-agent, so only the desktop gets this one
            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36")

        options.page_load_strategy = "eager"

        # Selenium Manager (built into Selenium 4) finds the installed Chrome and downloads the matching driver
        self.driver = webdriver.Chrome(options=options)

        self.wait = WebDriverWait(self.driver, 7)

    def get_username(self):
        return self.username

    def get_password(self):
        return self.password

    def _login(self):
        websites = self.database.get_websites_data()
        if websites:
            random_website_num = random.randint(0, len(websites) - 1)
            self.driver.get(websites[random_website_num][1])
            time.sleep(3.5)
        self.driver.get(S.url("login"))
        S.get(self.driver, "login.username_input", timeout=10).send_keys(self.username)
        S.get(self.driver, "login.password_input").send_keys(self.password + Keys.RETURN)
        time.sleep(2.0)

        is_login_successful = self.is_login_successful()
        if not is_login_successful: # if its False, means  it didn't logged in
            log.error("%s: login failed", self.username)
            return False
        self._dismiss_popups()
        return True

    # "Save your login info?" and "Turn on notifications" after logging in
    def _dismiss_popups(self):
        for _ in range(2):
            button = S.find(self.driver, "login.not_now_button", timeout=4)
            if button is None:
                return
            S.clickable(button).click()
            time.sleep(1.5)

    def _nav_user(self, user):
        self.driver.get(S.url("profile", username=user))

    def _nav_user_new_tab(self, username):
        self.driver.execute_script("window.open('{}');".format(S.url("profile", username=username)))

    def _like_post(self):
        try:
            S.click(self.driver, "post.like_button")
        except Exception:
            log.exception("%s: could not like the post", self.username)
            self._screen_shot(self.username)

    def _get_like_amount_text(self):
        time.sleep(1)
        likes = S.count(self.driver, "post.likes_link", timeout=3)
        return utils().clean_number(likes) if likes else 0

    # comment on a post
    def _comment_post(self, split_comment):
        # returning random comment from a list of comments
        comment = random.choice(split_comment)
        time.sleep(2)
        # first need to click on the Entry ('add comment...')
        S.get(self.driver, "post.comment_input").click()
        # Then enter the comment and click post (found again: the box re-renders after the click)
        S.get(self.driver, "post.comment_input").send_keys(comment + Keys.RETURN)

    def _follow_user(self, to_distribution, group_id):
        settings_data = self.database.get_data_from_settings()
        # only found while you don't follow the author yet
        follow_button = S.find(self.driver, "post.author_follow_button", timeout=7)
        if follow_button is None:
            print("_follow_user: no Follow button (already following, or not found)")
            return
        username = None
        try:
            # Get the username
            try:
                username = S.get(self.driver, "post.author_link").text
            except Exception:
                log.exception("%s: could not read the post author", self.username)
            followers_num, no_use_data, no_use_d = self._get_followers_number(username)
            if followers_num != -1:
                if int(followers_num) >= int(settings_data[2]):
                    follow_button.click()
                    self.database.save_unfollow_users(username, self.username)
                    if to_distribution:
                        self.database.add_username_to_distribution_group(username, group_id)
        except Exception:
            log.exception("%s: could not follow %s", self.username, username)

    def _unfollow_user(self, username, user_id):
        if not self._login():
            return
        self._nav_user(username)
        time.sleep(2)
        unfollowed = False
        try:
            S.click(self.driver, "profile.following_button")
            S.click(self.driver, "profile.unfollow_confirm")
            db.Database().remove_username_from_unfollow_list(username, user_id)
            unfollowed = True
        except Exception:
            # normal for a private account you only requested to follow
            log.debug("%s: no Following button on %s", self.username, username, exc_info=True)
        try:
            S.click(self.driver, "profile.requested_button", timeout=2)
        except Exception:
            if not unfollowed:
                log.warning("%s: could not unfollow %s: no Following or Requested button", self.username, username)
            return
        try:
            self._popup_unfollow()
            db.Database().remove_username_from_unfollow_list(username, user_id)
        except Exception:
            log.exception("%s: could not cancel the follow request to %s", self.username, username)

    def _popup_unfollow(self):
        # when user is private and you unfollow him, it pops up a message if you sure you want to unfollow
        # if it is there, click on the button "unfollow"
        button = S.find(self.driver, "profile.unfollow_confirm", timeout=3)
        if button is not None:
            S.clickable(button).click()

    def _user_not_found_broken_link(self):
        return S.exists(self.driver, "profile.not_found_title", timeout=7)

    def _check_if_blocked(self):
        url = self.check_current_url()
        if any(part in url for part in S.text("restriction_urls")):
            log.warning("%s: Instagram restricted this account: %s", self.username, url)
            return True
        popup = S.find(self.driver, "block.popup", timeout=0)
        if popup is not None:
            log.warning("%s: Instagram blocked an action: %s", self.username, popup.text)
            return True
        return False

    # (followers, has_profile_image, posts) of a user, read in a new tab.
    # Always 3 values: -1 means unknown. has_profile_image is -1 when the user HAS a picture.
    def _get_followers_number(self, username):
        self._nav_user_new_tab(username)
        self.driver.switch_to.window(self.driver.window_handles[1])
        has_profile_image = self._has_profile_image()
        clean_number = -1
        post_amount = -1
        try:
            if has_profile_image == -1:
                post_amount = utils().clean_number(self.get_post_amount())
                clean_number = utils().clean_number(S.count(self.driver, "profile.followers_counter"))
        except Exception:
            log.exception("%s: could not read the followers of %s", self.username, username)
        finally:
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])
        return clean_number, has_profile_image, post_amount

    # this method is double check, when i unfollow user, check if the button display 'follow_back'
    # means the user that i just unfollow is following me.
    def _check_if_follow_back(self):
        button = S.find(self.driver, "profile.follow_back_button", timeout=4)
        if button is None:
            return False
        button.click()
        return True

    # usernames in the open list (followers/following), after scrolling it to the end
    def _get_usersname(self):
        scroll_box = S.get(self.driver, "dialog.scroll_area")
        last_height, height = 0, 1
        # this while scrolls all over the followers
        while last_height != height:
            last_height = height
            time.sleep(2)
            height = S.scroll_to_bottom(self.driver, scroll_box)
        # (username,) like the rows of the dm_users table
        return [(username,) for username, _button in S.dialog_rows(self.driver)]

    def _screen_shot(self, username):
        self.driver.save_screenshot("screen_shots/{}.png".format(username))

    def _send_email(self, username, success_posts, time, section):
        mailgun_domain = os.environ.get('MAILGUN_DOMAIN')
        mailgun_api = os.environ.get('MAILGUN_API')
        alert_email = os.environ.get('ALERT_EMAIL')
        if not (mailgun_domain and mailgun_api and alert_email):
            log.warning("Not sending the alert e-mail: set MAILGUN_DOMAIN, MAILGUN_API and ALERT_EMAIL in .env")
            return
        print('sending email')
        image_name = username + '.png'
        requests.post("https://api.mailgun.net/v3/{}/messages".format(mailgun_domain),
                      auth=("api", "{}".format(mailgun_api)),
                      files=[("attachment", (username,
                                open("screen_shots/{}".format(image_name), "rb").read()))],
                      data={"from": "RocketBot <{}>".format(alert_email),
                            "to": [alert_email],
                            "subject": "RocketBot Error - {}".format(username),
                            "text": """ 
                            Username: {} 
                            Section: {}
                            Success: {} 
                            Time: {}""".format(username, section, success_posts, time)})

    def _blocked_action_popup(self):
        popup = S.find(self.driver, "block.popup", timeout=4)
        if popup is None:
            return False
        self._screen_shot(self.username)
        time.sleep(1)
        ok = S.find(self.driver, "block.popup_ok", timeout=1)
        if ok is not None:
            S.clickable(ok).click()
        return True

    def _has_profile_image(self):
        # if this method returns -1, means the user has profile image.
        # if it returns a number bigger then -1 means the user has no profile image
        # (None when the picture isn't found at all)
        image = S.find(self.driver, "profile.picture", timeout=7)
        if image is None:
            return None
        return (image.get_attribute("src") or "").find(S.text("default_avatar_file"))

    def global_block_message(self, username, seaction):
        log.error("%s has been blocked by Instagram (%s)", username, seaction)

    def global_complate_task(self, username, section, results):
        print(("""Complate tast: {},\nResults: {}\nUsername: {} """.format(section, results, username)))

    # this method checks if the post 'liked'. if it is then it 'unlike' it
    # used for combination
    def is_post_liked(self):
        button = S.find(self.driver, "post.unlike_button", timeout=0)
        if button is not None:
            S.clickable(button).click()
            time.sleep(1.3)

    def skip_posts(self, num_of_skips):
        for post in range(num_of_skips):
            S.click(self.driver, "post.next_button")
            time.sleep(1.0)

    def save_account_action(self, account_action):
        db.Database().save_data_account_action(account_action)

    # get the number of posts, as text ("1,234")
    def get_post_amount(self):
        posts_amount = S.count(self.driver, "profile.posts_counter")
        if posts_amount is None:
            log.warning("%s: could not read the number of posts", self.username)
            return 0
        return posts_amount

    # getting current url
    def check_current_url(self):
        return self.driver.current_url

    def is_login_successful(self):
        # logged in when the Home icon shows up; a wrong password or a security check stops it
        for _ in range(15):
            if S.exists(self.driver, "login.logged_in_marker"):
                return True
            if S.exists(self.driver, "login.error_message"):
                log.error("%s: Instagram says the username or password is wrong", self.username)
                return False
            if any(part in self.check_current_url() for part in S.text("restriction_urls")):
                log.error("%s: Instagram wants a security check: log in to this account by hand once", self.username)
                return False
            time.sleep(1)
        return False
