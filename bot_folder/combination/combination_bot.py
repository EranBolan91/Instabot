from bot_folder import main_bot
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from database.combination.combination import CombinationDM
from database.followers.followers import FollowersDB
from selenium.webdriver.common.action_chains import ActionChains
from utils.utils import Utils as utils
from models.combination import Combination
from models.account_actions import AccountActions
import time
import datetime as dt
from random import randint
from database import db
from models.followers import Followers


PROCESS_TIME = 60 * 60 / 8
MAX_FOLLOWERS_EACH_PROCESS = 100
WAIT_FOR_EACH_FOLLOW = PROCESS_TIME / MAX_FOLLOWERS_EACH_PROCESS

POST = 0
HEIGHT = 1
BUTTON = 2


class CombinationBot(main_bot.InstagramBot):
    def combination(self, hashtag, url, likes, followers, to_distribution, schedule, group_name, group_id, skip_posts):
        self.automation(followers, hashtag, url, skip_posts, likes)

    def automation(self, max_followers, hashtag, url, skip_posts, likes):
        wait = WebDriverWait(self.driver, 5)
        settings_data_from_db = CombinationDM().get_data_from_settings()
        follow_buttons = []
        curr_height = 0
        curr_like = 0
        last_place = [0, 0, 0]

        self._login()

        while max_followers > 0:
            follow_counter = 0

            self._get_wanted_post(
                hashtag, url, skip_posts + last_place[POST], wait)

            if curr_like < likes:
                self.is_post_liked()
                self._like_post(wait)
                curr_like += 1

            self._open_likes(wait, last_place)
            scroll_box = self._get_scroll_box(wait)

            follow_buttons, curr_height, scroll_box = self._go_to_last_place(
                last_place, scroll_box, wait)

            while follow_counter < MAX_FOLLOWERS_EACH_PROCESS:
                curr_follow_add = randint(1, 4)

                for i in range(curr_follow_add):
                    print("combination follow: {} people left to follow".format(
                        max_followers))

                    if max_followers <= 0:
                        break

                    # checking for buttons if not, reload them
                    if not follow_buttons:
                        follow_buttons, curr_height, scroll_box = self._get_buttons(
                            scroll_box, curr_height, last_place, wait)

                    try:
                        if follow_buttons[0][1].text == 'Follow':
                            if self._follow(follow_buttons[0][1], follow_buttons[0][0].text, settings_data_from_db, follow_counter):
                                follow_counter += 1
                                max_followers -= 1
                    except Exception as e:
                        print(e)

                    # remove the first button
                    follow_buttons.pop(0)
                    last_place[BUTTON] += 1

                print("waiting {} secodns".format(
                    WAIT_FOR_EACH_FOLLOW * curr_follow_add))
                time.sleep(WAIT_FOR_EACH_FOLLOW * curr_follow_add)

            unfollow_users = self.database.get_unfollow_users(self.username)
            self._unfollow_users(
                unfollow_users, self.database.get_user_id(self.username), wait)

        self.driver.delete_all_cookies()
        self.driver.close()

    def _go_to_last_place(self, last_place, scroll_box, wait):
        height = 0

        for i in range(last_place[HEIGHT]):
            height = self._scroll_down(scroll_box, last_place)

        buttons, height, scroll_box = self._get_buttons(scroll_box, height, last_place, wait)[
            last_place[BUTTON]:]
        return buttons, height, scroll_box

    def _scroll_down(self, scroll_box, last_place):
        height = self.driver.execute_script("""
                                        arguments[0].scrollTo(
                                            0, arguments[0].scrollHeight);
                                        return arguments[0].scrollHeight;
                                        """, scroll_box)

        time.sleep(2)
        return height

    def _get_buttons(self, scroll_box, last_height, last_place, wait):
        last_place[BUTTON] = 0
        last_place[HEIGHT] += 1
        height = self._scroll_down(scroll_box, last_place)

        # checking if we made it to the end of the post
        if height == last_height:
            self._go_to_next_post(wait, last_place)
            self._open_likes(wait, last_place)
            scroll_box = self._get_scroll_box(wait)
            height = self._scroll_down(scroll_box, last_place)
            last_place[HEIGHT] = 1

        users_name_list = self.driver.find_elements_by_class_name(
            'MBL3Z')
        buttons = scroll_box.find_elements_by_tag_name('button')[:11]

        # convert the 2 lists to 1 list of tuples
        return list(zip(users_name_list, buttons)), height, scroll_box

    # Saving Hash-tag data to display in the statistics

    def _prepare_data_for_db(self, url, hashtag, num_likes, num_failed_likes, num_followers,
                             num_failed_followers, schedule, distribution, group_name):
        follow_followers = Combination(self.username, url, hashtag, num_likes, num_failed_likes,
                                       num_followers, num_failed_followers, schedule, distribution, group_name)
        CombinationDM().save_in_db(follow_followers)
        account_id = CombinationDM().get_user_id(self.username)
        account_action = AccountActions(
            account_id, self.username, "Combination", num_followers, num_followers - num_failed_followers)
        FollowersDB().save_data_account_action(account_action)

    def _get_wanted_post(self, hashtag, url, skip_posts, wait):
        time.sleep(3)
        try:
            if hashtag:
                self.driver.get(
                    '{}/explore/tags/{}'.format(self.base_url, hashtag))
            elif url:
                self.driver.get(url)
            time.sleep(3)
            # click on the first post
            first_post = wait.until(
                EC.element_to_be_clickable((By.CLASS_NAME, '_9AhH0')))
            first_post.click()
            self.skip_posts(skip_posts)
            time.sleep(2)
        except Exception as e:
            print('Combination: ', e)

    def _like_post(self, wait):
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '/html/body/div[5]/div[2]/div/article/div[3]/section[1]/span[1]/button/div/span/svg'))).click()

    def _open_likes(self, wait, last_place):
        try:
            wait.until(EC.element_to_be_clickable(
                (By.XPATH, "/html/body/div[5]/div[2]/div/article/div[3]/section[2]/div/div/a"))).click()
        except Exception as e:
            try:
                wait.until(
                    EC.element_to_be_clickable((By.XPATH, '/html/body/div[5]/div/div/article/div[2]/div[2]/div/section[1]/div/div/a'))).click()
            except Exception as e:
                self._go_to_next_post(wait, last_place)
                self._open_likes(wait, last_place)

    def _get_scroll_box(self, wait):
        try:
            return wait.until(EC.element_to_be_clickable(
                (By.XPATH, '/html/body/div[6]/div/div/div[2]/div')))
        except Exception as e:
            return wait.until(
                EC.element_to_be_clickable((By.XPATH, '/html/body/div[6]/div/div/div[3]/div')))

    def _follow(self, button, username, settings_data_from_db, follow_count):
        followed = False

        followers_num, has_image_profile = self._get_followers_number(username)
        if has_image_profile == -1:
            if int(followers_num) >= int(settings_data_from_db[2]):
                button.click()
                followed = True
                print("followed {}".format(username))

        self.database.save_unfollow_users(
            username, self.username)

        try:
            is_action_blocked = self._blocked_action_popup()
            if is_action_blocked:
                self._send_email(self.username, follow_count,
                                 dt.datetime.now().strftime('%H:%M:%S'),
                                 'Combination')
                self.global_block_message(
                    self.username, "Combination")

        except Exception as e:
            pass

        return followed

    def _print_username_and_time(self, loops):
        if loops % utils.TIME_SLEEP == 0:
            print('Username:', self.username, 'Time start:',
                  dt.datetime.now().strftime('%H:%M:%S'),
                  ' Sleep time:',
                  loops * utils.TIME_SLEEP, 'seconds')
            time.sleep(loops * utils.TIME_SLEEP)

    def _go_to_next_post(self, wait, last_place):
        try:
            wait.until(EC.element_to_be_clickable(
                (By.XPATH, '/html/body/div[6]/div/div/div[1]/div/div[2]/button'))).click()
            wait.until(EC.element_to_be_clickable(
                (By.CLASS_NAME, 'coreSpriteRightPaginationArrow'))).click()
        except Exception as e:
            wait.until(EC.element_to_be_clickable(
                (By.CLASS_NAME, 'coreSpriteRightPaginationArrow'))).click()

        last_place[POST] += 1
        time.sleep(1)

    def _unfollow_users(self, user_list, account_id, wait):
        curr_user = 0

        while curr_user < len(user_list):
            follow_sub = randint(1, 4)

            for i in range(follow_sub):
                if curr_user >= len(user_list):
                    break

                print("combination unfollow: {} people left to unfollow".format(
                    len(user_list) - curr_user))

                if self._unfollow(user_list[curr_user][2], account_id, wait) == -1:
                    self._send_email(self.username, curr_user, dt.datetime.now().strftime(
                        '%H:%M:%S'), 'Followers')
                    self.driver.close()
                    self.global_block_message(self.username, "Followers")

                curr_user += 1

            print("waiting {} secodns".format(
                WAIT_FOR_EACH_FOLLOW * follow_sub))
            time.sleep(WAIT_FOR_EACH_FOLLOW * follow_sub)

    def _unfollow(self, user, account_id, wait):
        follow_back = False

        self._nav_user(user)

        def _find_and_click_unfollow():
            try:
                following_btn = wait.until(
                    EC.element_to_be_clickable((By.XPATH, '//button[text()="Following"]')))
                following_btn.click()

                try:
                    self._popup_unfollow()
                except Exception as e:
                    print('unfollow users pop up exception: ', e)

                return

            except Exception as e:
                pass

            try:
                requested_btn = wait.until(
                    EC.element_to_be_clickable((By.XPATH, '//button[text()="Requested"]')))
                requested_btn.click()

                try:
                    self._popup_unfollow()
                except Exception as e:
                    pass

                return

            except Exception as e:
                pass

            # This try is for accounts that when they access to another user page, it display them Icon following
            try:
                following_btn = wait.until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="react-root"]/section/main/div/header/section/div[1]/div[1]/div/div[2]/button ')))
                following_btn.click()

                try:
                    self._popup_unfollow()
                except Exception as e:
                    print('unfollow users pop up exception: ', e)

                return

            except Exception as e:
                pass

            try:
                following_btn = wait.until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="react-root"]/section/main/div/header/section/div[1]/div[1]/div/div[2]/div/span/span[1]/button')))
                following_btn.click()

                try:
                    self._popup_unfollow()
                except Exception as e:
                    print('unfollow users pop up exception: ', e)

                return

            except Exception as e:
                pass

            try:
                following_btn = wait.until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="react-root"]/section/main/div/header/section/div[1]/div[2]/div/div[2]/div/span/span[1]/button')))
                following_btn.click()

                try:
                    self._popup_unfollow()
                except Exception as e:
                    print('unfollow users pop up exception: ', e)

                return

            except Exception as e:
                pass

        _find_and_click_unfollow()
        try:
            is_action_blocked = self._blocked_action_popup()
            if is_action_blocked:
                return -1
        except Exception as e:
            pass
        # count how many users follow back
        try:
            self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, '//button[text()="Follow Back"]')))
            follow_back = True
        except Exception as e:
            pass

        # Remove username from unfollow list
        # This two try and catch are double check, if the bot clicks on 'unfollow' and it does not turn
        # into unfollow. In this situation, i prefer not to remove the username from database

        try:
            follow_btn = wait.until(
                EC.element_to_be_clickable((By.XPATH, '//button[text()="Follow"]')))
            if follow_btn:
                print(user, 'Removed from db of', self.username)
                db.Database().remove_username_from_unfollow_list(user, account_id)

        except Exception as e:
            pass
        try:
            follow_btn = wait.until(
                EC.element_to_be_clickable((By.XPATH, '//button[text()="Follow Back"]')))
            if follow_btn:
                print(user, 'Removed from db', self.username)
                db.Database().remove_username_from_unfollow_list(user, account_id)

        except Exception as e:
            pass

        # save the amount of followers back
        followers_obj = Followers(account_id, self.username, follow_back)
        FollowersDB().save_in_db(followers_obj)
