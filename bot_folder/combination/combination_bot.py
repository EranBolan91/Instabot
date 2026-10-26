from bot_folder import main_bot
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from database.combination.combination import CombinationDM
from database.followers.followers import FollowersDB
from utils.utils import Utils as utils
from utils.instagram_selectors import S
from models.combination import Combination
from models.account_actions import AccountActions
import time
from time import strftime
from time import gmtime
import datetime as dt
from random import randint
from database import db
from models.followers import Followers
from utils.log import get_logger

log = get_logger(__name__)

PROCESS_TIME = 60 * 60 * 12
MAX_FOLLOWERS_EACH_PROCESS = 100
WAIT_FOR_EACH_FOLLOW = PROCESS_TIME / MAX_FOLLOWERS_EACH_PROCESS
#WAIT_FOR_EACH_FOLLOW = 5
# give up after this many likes lists in a row with nobody new in them
MAX_EMPTY_LISTS = 5


class CombinationBot(main_bot.InstagramBot):
    def combination(self, hashtag, url, likes, followers, to_distribution, schedule, group_name, group_id, skip_posts, skip_users):
        if not self.automation(followers, hashtag, url, skip_posts, likes,
                               group_id=group_id if to_distribution else None, skip_users=skip_users):
            return
        failed_follows = max(int(followers) - self._followed, 0)
        self._prepare_data_for_db(url, hashtag, self._likes_target, self._likes_target - self._likes_done,
                                  followers, failed_follows, schedule, to_distribution, group_name, skip_users)

    # returns False when the login failed (nothing ran, nothing to save)
    # group_id: save each followed user to this distribution list (None = don't)
    # skip_users: pass over this many users at the start of the likes list without following them
    def automation(self, max_followers, hashtag, url, skip_posts, likes, group_id=None, skip_users=0):
        wait = None  # kept in the helper signatures; the selectors do their own waiting
        settings_data_from_db = CombinationDM().get_data_from_settings()
        follow_buttons = []
        curr_height = 0
        is_follow = False
        is_blocked = False
        out_of_users = False
        empty_lists = 0
        # usernames already looked at in the likes lists
        self._seen = set()
        # counted while the run goes; combination() saves them for the Statistics page
        self._followed = 0
        self._likes_target = 0
        self._likes_done = 0
        self._group_id = group_id
        users_to_skip = max(int(skip_users or 0), 0)

        if not self._login():
            return False

        try:
            self._get_wanted_post(
                hashtag, url, skip_posts, wait)

            # open likes button - it press on "likes" of the post
            self._open_likes(wait)
            scroll_box = self._get_scroll_box(wait)

            while max_followers > 0 and not out_of_users:
                follow_counter = 0

                while follow_counter < MAX_FOLLOWERS_EACH_PROCESS and max_followers > 0 and not out_of_users:
                    # follow between 1 - 4 users
                    curr_follow_add = randint(1, 4)
                    i = 0

                    while i < curr_follow_add:
                        print("{} : {} -- combination follow: {} people left to follow".
                                        format(dt.datetime.now().strftime('%H:%M:%S'), self.username, max_followers))

                        if max_followers <= 0:
                            break

                        # checking for rows, if not, load more of them
                        if not follow_buttons:
                            follow_buttons, curr_height, scroll_box = self._get_buttons(
                                scroll_box, curr_height, wait)
                            if not follow_buttons:
                                empty_lists += 1
                                if empty_lists >= MAX_EMPTY_LISTS:
                                    print("Combination: no more users to follow")
                                    out_of_users = True
                                    break
                                continue
                            empty_lists = 0

                        username, button = follow_buttons.pop(0)
                        if users_to_skip > 0:
                            users_to_skip -= 1
                            continue
                        try:
                            if button is not None and button.text == 'Follow':
                                is_follow, is_blocked = self._follow(button, username, settings_data_from_db, follow_counter, wait, likes)
                                if is_follow:
                                    self._followed += 1
                                    follow_counter += 1
                                    max_followers -= 1
                                    i += 1
                        except Exception:
                            log.exception("Combination %s: could not follow %s", self.username, username)
                        # break the inner while loop
                        if is_blocked:
                            break
                    # break the middle while loop
                    if is_blocked or out_of_users:
                        break
                    print("{} : {} -- sleep for {} minutes".format(dt.datetime.now().strftime('%H:%M:%S'),
                        self.username, strftime("%M:%S", gmtime(WAIT_FOR_EACH_FOLLOW * curr_follow_add))))
                    time.sleep(WAIT_FOR_EACH_FOLLOW * curr_follow_add)

                unfollow_users = self.database.get_unfollow_users(self.username)
                # a block while unfollowing stops the run too
                if self._unfollow_users(unfollow_users, self.database.get_user_id(self.username), wait):
                    is_blocked = True

                # break the first while loop
                if is_blocked:
                    self._screen_shot(self.username)
                    break
        except Exception:
            log.exception("Combination %s: run stopped", self.username)
        finally:
            self._close_browser()
        return True

    def _scroll_down(self, scroll_box):
        height = S.scroll_to_bottom(self.driver, scroll_box)
        time.sleep(2)
        return height

    # rows of the likes list not looked at yet, as (username, button or None)
    def _new_rows(self):
        rows = [(username, button) for username, button in S.dialog_rows(self.driver) if username not in self._seen]
        self._seen.update(username for username, _ in rows)
        return rows

    def _get_buttons(self, scroll_box, last_height, wait):
        height = self._scroll_down(scroll_box)
        rows = self._new_rows()

        # checking if we made it to the end of the post's likes
        if not rows and height == last_height:
            self._close_list()
            self._go_to_next_post(wait)

            self._open_likes(wait)
            scroll_box = self._get_scroll_box(wait)
            height = self._scroll_down(scroll_box)
            rows = self._new_rows()

        return rows, height, scroll_box

    # Saving Combination data to display in the statistics
    def _prepare_data_for_db(self, url, hashtag, num_likes, num_failed_likes, num_followers,
                             num_failed_followers, schedule, distribution, group_name, skip_users):
        combination = Combination(self.username, url, hashtag, num_likes, num_failed_likes,
                                  num_followers, num_failed_followers, schedule, distribution, group_name, skip_users)
        CombinationDM().save_in_db(combination)
        account_id = CombinationDM().get_user_id(self.username)
        account_action = AccountActions(
            account_id, self.username, "Combination", num_followers, num_followers - num_failed_followers)
        FollowersDB().save_data_account_action(account_action)

    def _get_wanted_post(self, hashtag, url, skip_posts, wait):
        try:
            if hashtag:
                time.sleep(3)
                self.driver.get(S.url("hashtag", tag=hashtag))
            elif url:
                self.driver.get(url)
            # a post's own address is already the post; anything else is a grid: open its first post
            if hashtag or not ("/p/" in url or "/reel/" in url):
                S.click(self.driver, "grid.first_post")
            time.sleep(2)
            self.skip_posts(skip_posts)
        except Exception:
            log.exception("Combination %s: could not open the post to start from", self.username)

    def _like_post(self, wait):
        time.sleep(2)
        # only found while the post isn't liked yet
        like = S.find(self.driver, "post.like_button", timeout=5)
        if like is not None:
            S.clickable(like).click()
            self._likes_done += 1

    def _open_likes(self, wait):
        try:
            S.click(self.driver, "post.likes_link")
            time.sleep(3)
        except Exception:
            log.warning("Combination %s: could not open the likes list, skipping the post", self.username, exc_info=True)
            self._go_to_next_post(wait)

    def _get_scroll_box(self, wait):
        return S.get(self.driver, "dialog.scroll_area")

    # closes the likes list (Escape closes the top dialog; a Close click could hit the post's)
    def _close_list(self):
        self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        time.sleep(1)

    def _follow(self, button, username, settings_data_from_db, follow_count, wait, likes):
        followed = False
        is_action_blocked = False
        # check if Instagram sent us to a restriction / security check page
        if any(part in self.check_current_url() for part in S.text("restriction_urls")):
            is_action_blocked = True
        else:
            followers_num, has_image_profile, post_amount = self._get_followers_number(username)
            if has_image_profile == -1:
                if int(followers_num) >= int(settings_data_from_db[2]) and int(post_amount) >= int(settings_data_from_db[7]):
                    button.click()
                    self.database.save_unfollow_users(username, self.username)
                    followed = True
                    # print("{} -- followed {}".format(self.username, username))
                    is_action_blocked = self._blocked_action_popup()
                    if is_action_blocked:
                        self._send_email(self.username, follow_count, dt.datetime.now().strftime('%H:%M:%S'),'Combination')
                        self.global_block_message(self.username, "Combination")
                        followed = False
                    elif getattr(self, "_group_id", None) is not None:
                        self.database.add_username_to_distribution_group(username, self._group_id)

                    try:
                        if followed and likes > 0:
                            self._likes_target += likes
                            self._like_posts(wait, username, likes)
                    except Exception:
                        log.exception("Combination %s: could not like the posts of %s", self.username, username)
                        # close the user's tab, if it opened, never the likes list
                        self._close_extra_tabs()

        return followed, is_action_blocked

    def _like_posts(self, wait, username, likes):
        self._nav_user_new_tab(username)
        self.driver.switch_to.window(self.driver.window_handles[1])

        S.click(self.driver, "profile.first_post")
        time.sleep(2)

        self._like_post(wait)
        likes -= 1

        for i in range(likes):
            self._go_to_next_post(wait)
            self._like_post(wait)

        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])

    def _print_username_and_time(self, loops):
        if loops % utils.TIME_SLEEP == 0:
            print('Username:', self.username, 'Time start:',
                  dt.datetime.now().strftime('%H:%M:%S'),
                  ' Sleep time:',
                  loops * utils.TIME_SLEEP, 'seconds')
            time.sleep(loops * utils.TIME_SLEEP)

    def _go_to_next_post(self, wait):
        try:
            S.click(self.driver, "post.next_button")
        except Exception:
            log.exception("Combination %s: could not go to the next post", self.username)

        time.sleep(1)

    # unfollows the users in the list, in a second tab. Returns True when Instagram blocked the account.
    def _unfollow_users(self, user_list, account_id, wait):
        curr_user = 0
        is_blocked = False
        self._nav_user_new_tab("")
        self.driver.switch_to.window(self.driver.window_handles[1])
        follow_back_counter = 0

        while curr_user < len(user_list):
            follow_sub = randint(1, 4)

            for i in range(follow_sub):
                if curr_user >= len(user_list):
                    break

                print("{} -- combination unfollow: {} people left to unfollow".format(
                    self.username, len(user_list) - curr_user))
                # if _unfollow says blocked, stop the whole process
                is_follow_back, is_blocked = self._unfollow(user_list[curr_user][2], account_id, wait)
                if is_blocked:
                    self._screen_shot(self.username)
                    self._send_email(self.username, curr_user, dt.datetime.now().strftime(
                        '%H:%M:%S'), 'Followers')
                    self.global_block_message(self.username, "Followers")
                    break

                curr_user += 1
                if is_follow_back:
                    follow_back_counter += 1
            # break the while loop
            if is_blocked:
                break
            print("{} : {} -- sleep for {} minutes".format(dt.datetime.now().strftime('%H:%M:%S'),
                                                           self.username, strftime("%M:%S", gmtime(WAIT_FOR_EACH_FOLLOW * follow_sub))))
            time.sleep(WAIT_FOR_EACH_FOLLOW * follow_sub)

        # save the amount of followers back
        followers_obj = Followers(account_id, self.username, follow_back_counter)
        FollowersDB().save_in_db(followers_obj)

        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])
        return is_blocked

    def _unfollow(self, user, account_id, wait):
        follow_back = False
        self._nav_user(user)

        try:
            if S.exists(self.driver, "profile.following_button", timeout=6):
                # "Following" opens a menu; "Unfollow" in it unfollows
                S.click(self.driver, "profile.following_button")
                self._popup_unfollow()
            elif S.exists(self.driver, "profile.requested_button"):
                S.click(self.driver, "profile.requested_button")
                self._popup_unfollow()
        except Exception:
            log.exception("Combination %s: could not unfollow %s", self.username, user)

        if self._blocked_action_popup():
            return False, True  # return False for follow_back and True for blocked
        # count how many users follow back
        if S.exists(self.driver, "profile.follow_back_button", timeout=4):
            follow_back = True

        # Remove username from unfollow list
        # Only when the button really turned into Follow / Follow Back: if the bot clicked
        # 'unfollow' and it didn't work, the username stays in the database
        if S.exists(self.driver, "profile.follow_button", timeout=4):
            print(user, 'Removed from db of', self.username)
            db.Database().remove_username_from_unfollow_list(user, account_id)

        return follow_back, False
