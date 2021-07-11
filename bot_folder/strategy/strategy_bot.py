from bot_folder import main_bot
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import datetime as dt
from random import randint
from database import db
from datetime import datetime
from bs4 import BeautifulSoup as bs

START_TIME = 23
END_TIME = 6
PROCESS_TIME = 60 * 60
REST = -1

class StrategyBot(main_bot.InstagramBot):
    def __init__(self, username, password, is_mobile, proxy_dict):
        time.sleep(START_TIME - datetime.now().hour)

        super(StrategyBot, self).__init__(username, password, is_mobile, proxy_dict)
        self.__wait = WebDriverWait(self.driver, 5)
        self.__follow_buttons = []
        self.__curr_height = 0
        self.__skip_posts = 0
        self.__scroll_box = None

    def strategy(self, hashtag, url, likes, clients, proxy_manager):
        try:
            self.__reset_data()
            self.automation(hashtag, url, likes)
            clients[self.username] = 'finished'
        except Exception as e:
            print(e)
            clients[self.username] = 'crashed'
            self._save_data()

        proxy_manager.remove_user(self.username)

    def automation(self, hashtag, url, likes):
        strategy = self.__build_strategy()

        self._login()
        print("{} -- combination log in".format(
            self.username))

        self._get_wanted_post(
            hashtag, url, 0)

        self._open_likes()
        self.__scroll_box = self._get_scroll_box()

        for day in strategy:
            self.__execute_strategy(day, hashtag, url, likes)

        while True:
            after_strategy = []
            for i in range(4):
                after_strategy.append(randint(22, 27))
                after_strategy.append(REST)

            self.__execute_strategy(after_strategy, hashtag, url, likes)

    def __execute_strategy(self, day, hashtag, url, likes):
        self.__reset_data()
        for part in day:

            if part == REST:
                self.__rest()
            else:
                for i in range(part):
                    self.__follow(hashtag, url, likes)
                    time.sleep(PROCESS_TIME / part)
        unfollow_users = self.database.get_unfollow_users(self.username)
        self._unfollow_users(
            unfollow_users, self.database.get_user_id(self.username))

        self._save_data()
        time.sleep(17 * 60 * 60)

    def __rest(self):
        # sleep one hour
        time.sleep(60 * 60)

    def __follow(self, hashtag, url, likes):
        followed = False

        while not followed:
            # checking for buttons if not, reload them
            if not self.__follow_buttons:
                try:
                    self.__follow_buttons, self.__curr_height, self.__scroll_box = self._get_buttons(
                        self.__scroll_box, self.__curr_height, self.__wait)
                except Exception as e:
                    self.__skip_posts += 1
                    self._get_wanted_post(
                        hashtag, url, self.__skip_posts)

                    self._open_likes()
                    self.__scroll_box = self._get_scroll_box()

            try:
                if self.__follow_buttons[0][1].text == 'Follow':
                    if self._follow(self.__follow_buttons[0][1], self.__follow_buttons[0][0].text, likes):
                        self.follow += 1
                        followed = True
            except Exception as e:
                print(e)

            if self.__follow_buttons:
                # remove the first button
                self.__follow_buttons.pop(0)

    def __modify_day(self, day, modification):
        curr = []
        for part in day:
            if part == REST:
                curr.append(REST)
            else:
                curr.append(part + modification)
        return curr

    def __build_strategy(self):
        day_one = [5, REST, 3, REST, 13, REST, 7]
        day_three = [10, REST, 5, REST, 27, REST, 13]
        strategy = []

        #day 1
        strategy.append(day_one)

        #day 2
        day_two = self.__modify_day(day_one, -1)
        strategy.append(day_two)

        #day 3
        strategy.append(day_three)

        #day 4
        strategy.append(day_one)

        #day 5
        day_five = self.__modify_day(day_three, 5)
        strategy.append(day_five)

        #day 6
        day_six = self.__modify_day(day_five, 5)
        strategy.append(day_six)

        return strategy

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
            self._go_to_next_post()

            self._open_likes()
            scroll_box = self._get_scroll_box()
            height = self._scroll_down(scroll_box)

        users_name_list = self.driver.find_elements_by_class_name(
            'MBL3Z')
        buttons = scroll_box.find_elements_by_tag_name('button')[:11]

        # convert the 2 lists to 1 list of tuples
        return list(zip(users_name_list, buttons)), height, scroll_box

    def _get_wanted_post(self, hashtag, url, skip_posts):
        time.sleep(3)
        try:
            if hashtag:
                self.driver.get(
                    '{}/explore/tags/{}'.format(self.base_url, hashtag))
            elif url:
                self.driver.get(url)
            time.sleep(3)
            # click on the first post
            first_post = self.__wait.until(
                EC.element_to_be_clickable((By.CLASS_NAME, '_9AhH0')))
            first_post.click()
            self.skip_posts(skip_posts)
            time.sleep(2)
        except Exception as e:
            print('Combination: ', e)

    def _like_post(self):
        time.sleep(2)
        like = self.__wait.until(
            EC.element_to_be_clickable((By.CLASS_NAME, 'fr66n')))
        soup = bs(like.get_attribute('innerHTML'), 'html.parser')
        if(soup.find('svg')['aria-label'] == 'Like'):
            like.click()
            self.likes += 1

    def _open_likes(self):
        try:
            self.__wait.until(EC.element_to_be_clickable(
                (By.XPATH, "/html/body/div[5]/div[2]/div/article/div[3]/section[2]/div/div/a"))).click()
        except Exception as e:
            try:
                self.__wait.until(
                    EC.element_to_be_clickable((By.XPATH, '/html/body/div[5]/div/div/article/div[2]/div[2]/div/section[1]/div/div/a'))).click()
            except Exception as e:
                self._go_to_next_post()
                self._open_likes()

    def _get_scroll_box(self):
        try:
            return self.__wait.until(EC.element_to_be_clickable(
                (By.XPATH, '/html/body/div[6]/div/div/div[2]/div')))
        except Exception as e:
            return self.__wait.until(
                EC.element_to_be_clickable((By.XPATH, '/html/body/div[6]/div/div/div[3]/div')))

    def _follow(self, button, username, likes):
        followed = False

        followers_num, has_image_profile = self._get_followers_number(username)
        if has_image_profile == -1:
            button.click()

            try:
                if likes > 0:
                    self._like_posts(username, likes)
            except Exception as e:
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])

            followed = True
            print("{} -- followed {}".format(self.username, username))

        self.database.save_unfollow_users(
            username, self.username)

        return followed

    def _like_posts(self, username, likes):
        self._nav_user_new_tab(username)
        self.driver.switch_to.window(self.driver.window_handles[1])

        print("{} -- combination likes: likes left {}".format(
            self.username, likes))

        first_post = self.__wait.until(
            EC.element_to_be_clickable((By.CLASS_NAME, '_9AhH0')))
        first_post.click()

        self._like_post()
        likes -= 1

        for i in range(likes):
            self._go_to_next_post()
            self._like_post()
            print("{} -- combination likes: likes left {}/{}".format(
                self.username, i, likes))

        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])

    def _go_to_next_post(self):
        try:
            self.__wait.until(EC.element_to_be_clickable(
                (By.XPATH, '/html/body/div[6]/div/div/div[1]/div/div[2]/button'))).click()
            self.__wait.until(EC.element_to_be_clickable(
                (By.CLASS_NAME, 'coreSpriteRightPaginationArrow'))).click()
        except Exception as e:
            self.__wait.until(EC.element_to_be_clickable(
                (By.CLASS_NAME, 'coreSpriteRightPaginationArrow'))).click()

        time.sleep(1)

    def _unfollow_users(self, user_list, account_id):
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
                    if self._unfollow(user_list[curr_user][2], account_id) == -1:
                        self._send_email(self.username, curr_user, dt.datetime.now().strftime(
                            '%H:%M:%S'), 'Followers')
                        self.driver.close()
                        self.global_block_message(self.username, "Followers")
                except Exception:
                    pass

                curr_user += 1
                self.unfollow += 1

        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])

    def _unfollow(self, user, account_id):
        self._nav_user(user)

        def _find_and_click_unfollow():
            try:
                following_btn = self.__wait.until(
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
                requested_btn = self.__wait.until(
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
                following_btn = self.__wait.until(
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
                following_btn = self.__wait.until(
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
                following_btn = self.__wait.until(
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
            self.__wait.until(EC.element_to_be_clickable(
                (By.XPATH, '//button[text()="Follow Back"]')))
            self.follow_back += 1
        except Exception as e:
            pass

        # Remove username from unfollow list
        # This two try and catch are double check, if the bot clicks on 'unfollow' and it does not turn
        # into unfollow. In this situation, i prefer not to remove the username from database

        try:
            follow_btn = self.__wait.until(
                EC.element_to_be_clickable((By.XPATH, '//button[text()="Follow"]')))
            if follow_btn:
                print(user, 'Removed from db of', self.username)
                db.Database().remove_username_from_unfollow_list(user, account_id)

        except Exception as e:
            pass
        try:
            follow_btn = self.__wait.until(
                EC.element_to_be_clickable((By.XPATH, '//button[text()="Follow Back"]')))
            if follow_btn:
                print(user, 'Removed from db', self.username)
                db.Database().remove_username_from_unfollow_list(user, account_id)

        except Exception as e:
            pass
