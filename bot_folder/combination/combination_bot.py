from bot_folder import main_bot
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from database.combination.combination import CombinationDM
from database.followers.followers import FollowersDB
from utils.utils import Utils as utils
from models.combination import Combination
from models.account_actions import AccountActions
import time
import datetime as dt
from random import randint
from database import db
import sys
from models.followers import Followers
from bs4 import BeautifulSoup as bs


PROCESS_TIME = 60 * 60 * 12
MAX_FOLLOWERS_EACH_PROCESS = 100
WAIT_FOR_EACH_FOLLOW = PROCESS_TIME / MAX_FOLLOWERS_EACH_PROCESS


class CombinationBot(main_bot.InstagramBot):
    def combination(self, hashtag, url, likes, followers, to_distribution, schedule, group_name, group_id, skip_posts, skip_users, clients, proxy_manager):
        try:
            self.automation(followers, hashtag, url, skip_posts, likes)
            clients[self.username] = 'finished'
        except Exception as e:
            print(e)
            clients[self.username] = 'crashed'
            self._save_data()

        proxy_manager.remove_user(self.username)

    def automation(self, max_followers, hashtag, url, skip_posts, likes):
        wait = WebDriverWait(self.driver, 5)
        settings_data_from_db = CombinationDM().get_data_from_settings()
        follow_buttons = []
        curr_height = 0

        self._login()
        print("{} -- combination log in".format(
            self.username))

        self._get_wanted_post(
            hashtag, url, skip_posts, wait)

        self._open_likes(wait)
        scroll_box = self._get_scroll_box(wait)

        while max_followers > 0:
            follow_counter = 0
            self.__reset_data()

            unfollow_users = self.database.get_unfollow_users(self.username)
            self._unfollow_users(
                unfollow_users, self.database.get_user_id(self.username), wait)

            while follow_counter < MAX_FOLLOWERS_EACH_PROCESS and max_followers > 0:
                curr_follow_add = randint(1, 4)
                i = 0

                while i < curr_follow_add:
                    print("{} -- combination follow: {} people left to follow".format(
                        self.username, max_followers))

                    if max_followers <= 0:
                        break

                    # checking for buttons if not, reload them
                    if not follow_buttons:
                        try:
                            follow_buttons, curr_height, scroll_box = self._get_buttons(
                                scroll_box, curr_height, wait)
                        except Exception as e:
                            print(e)

                    try:
                        if follow_buttons[0][1].text == 'Follow':
                            if self._follow(follow_buttons[0][1], follow_buttons[0][0].text, settings_data_from_db, follow_counter, wait, likes):
                                follow_counter += 1
                                max_followers -= 1
                                i += 1
                                self.follow += 1
                    except Exception as e:
                        print(e)

                    if follow_buttons:
                        # remove the first button
                        follow_buttons.pop(0)

                print("{} -- waiting {} seconds".format(
                    self.username, WAIT_FOR_EACH_FOLLOW * curr_follow_add))
                time.sleep(WAIT_FOR_EACH_FOLLOW * curr_follow_add)

            self._save_data()

        self.driver.delete_all_cookies()
        self.driver.close()

    def __reset_data(self):
        self.follow = 0
        self.unfollow = 0
        self.follow_back = 0
        self.likes = 0

    def _save_data(self):
        user_id = db.Database().get_user_id(self.username)
        db.Database().save_gains(user_id, self.likes,
                                 self.follow, self.unfollow, self.follow_back)

    def _scroll_down(self, scroll_box):
        height = self.driver.execute_script("""
                                        arguments[0].scrollTo(
                                            0, arguments[0].scrollHeight);
                                        return arguments[0].scrollHeight;
                                        """, scroll_box)

        time.sleep(2)
        return height

    def _get_buttons(self, scroll_box, last_height, wait):
        height = self._scroll_down(scroll_box)

        # checking if we made it to the end of the post
        if height == last_height:
            self._go_to_next_post(wait)

            self._open_likes(wait)
            scroll_box = self._get_scroll_box(wait)
            height = self._scroll_down(scroll_box)

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
        time.sleep(2)
        like = wait.until(
            EC.element_to_be_clickable((By.CLASS_NAME, 'fr66n')))
        soup = bs(like.get_attribute('innerHTML'), 'html.parser')
        if(soup.find('svg')['aria-label'] == 'Like'):
            like.click()
            self.likes += 1

    def _open_likes(self, wait):
        try:
            wait.until(EC.element_to_be_clickable(
                (By.XPATH, "/html/body/div[5]/div[2]/div/article/div[3]/section[2]/div/div/a"))).click()
        except Exception as e:
            try:
                wait.until(
                    EC.element_to_be_clickable((By.XPATH, '/html/body/div[5]/div/div/article/div[2]/div[2]/div/section[1]/div/div/a'))).click()
            except Exception as e:
                self._go_to_next_post(wait)
                self._open_likes(wait)

    def _get_scroll_box(self, wait):
        try:
            return wait.until(EC.element_to_be_clickable(
                (By.XPATH, '/html/body/div[6]/div/div/div[2]/div')))
        except Exception as e:
            return wait.until(
                EC.element_to_be_clickable((By.XPATH, '/html/body/div[6]/div/div/div[3]/div')))

    def _follow(self, button, username, settings_data_from_db, follow_count, wait, likes):
        followed = False

        followers_num, has_image_profile = self._get_followers_number(username)
        if has_image_profile == -1:
            if int(followers_num) >= int(settings_data_from_db[2]):
                button.click()

                try:
                    if likes > 0:
                        self._like_posts(wait, username, likes)
                except Exception as e:
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])

                followed = True
                print("{} -- followed {}".format(self.username, username))

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

    def _like_posts(self, wait, username, likes):
        self._nav_user_new_tab(username)
        self.driver.switch_to.window(self.driver.window_handles[1])

        print("{} -- combination likes: likes left {}".format(
            self.username, likes))

        first_post = wait.until(
            EC.element_to_be_clickable((By.CLASS_NAME, '_9AhH0')))
        first_post.click()

        self._like_post(wait)
        likes -= 1

        for i in range(likes):
            self._go_to_next_post(wait)
            self._like_post(wait)
            print("{} -- combination likes: likes left {}/{}".format(
                self.username, i, likes))

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
            wait.until(EC.element_to_be_clickable(
                (By.XPATH, '/html/body/div[6]/div/div/div[1]/div/div[2]/button'))).click()
            wait.until(EC.element_to_be_clickable(
                (By.CLASS_NAME, 'coreSpriteRightPaginationArrow'))).click()
        except Exception as e:
            wait.until(EC.element_to_be_clickable(
                (By.CLASS_NAME, 'coreSpriteRightPaginationArrow'))).click()

        time.sleep(1)

    def _unfollow_users(self, user_list, account_id, wait):
        curr_user = 0
        self._nav_user_new_tab("")
        self.driver.switch_to.window(self.driver.window_handles[1])

        while curr_user < len(user_list):
            follow_sub = randint(1, 4)

            for i in range(follow_sub):
                if curr_user >= len(user_list):
                    break

                print("{} -- combination unfollow: {} people left to unfollow".format(
                    self.username, len(user_list) - curr_user))

                try:
                    if self._unfollow(user_list[curr_user][2], account_id, wait) == -1:
                        self._send_email(self.username, curr_user, dt.datetime.now().strftime(
                            '%H:%M:%S'), 'Followers')
                        self.driver.close()
                        self.global_block_message(self.username, "Followers")
                except Exception:
                    pass

                curr_user += 1
                self.unfollow += 1

            print("{} -- waiting {} secodns".format(
                self.username, WAIT_FOR_EACH_FOLLOW * follow_sub))
            time.sleep(WAIT_FOR_EACH_FOLLOW * follow_sub)

        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])

    def _unfollow(self, user, account_id, wait):
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

        try:
            _find_and_click_unfollow()
        except Exception:
            pass

        try:
            is_action_blocked = self._blocked_action_popup()
            if is_action_blocked:
                return -1
        except Exception as e:
            pass
        # count how many users follow back
        try:
            wait.until(EC.element_to_be_clickable(
                (By.XPATH, '//button[text()="Follow Back"]')))
            self.follow_back += 1
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
