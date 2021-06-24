from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.firefox.options import Options
from utils.utils import Utils as utils
from database import db
from seleniumwire import webdriver
from bot_folder.proxy import get_proxy_plugin
import time
import random
import requests
from requests import get
import os
from base64 import b64encode


class InstagramBot:
    def __init__(self, username, password, is_mobile, proxy_dict):
        self.database = db.Database()
        self.username = username
        self.password = password
        self.proxy_dict = proxy_dict
        self.base_url = 'https://www.instagram.com'

        # the options from this website -> https://www.selenium.dev/documentation/en/webdriver/page_loading_strategy/
        options = Options()

        options.page_load_strategy = 'eager'
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument("--disable-notifications")

        #options.add_argument("--headless")
        options.add_argument('--disable-extensions')
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36")

        proxy_options = {
            'proxy': {
                'http': 'http://{}:{}@{}:{}'.format(proxy_dict['user'], proxy_dict['password'], proxy_dict['host'], proxy_dict['port']),
                'https': 'https://{}:{}@{}:{}'.format(proxy_dict['user'], proxy_dict['password'], proxy_dict['host'], proxy_dict['port']),
                'no_proxy': 'localhost,127.0.0.1,dev_server:8080'
            }
        }

        if is_mobile:
            chrome_options = webdriver.ChromeOptions()
            mobile_emulation = {"deviceName": "Nexus 5"}
            chrome_options.add_experimental_option(
                "mobileEmulation", mobile_emulation)
            self.driver = webdriver.Chrome(
                'chromedriver.exe', options=options, chrome_options=chrome_options)
        else:
            self.driver = webdriver.Firefox(
                options=options, seleniumwire_options=proxy_options)

    def get_username(self):
        return self.username

    def get_password(self):
        return self.password

    def _login(self):
        self.driver.get('{}/accounts/login/'.format(self.base_url))
        WebDriverWait(self.driver, 7).until(
            EC.element_to_be_clickable((By.NAME, 'username'))).send_keys(self.username)
        # self.driver.find_element_by_name('username').send_keys(self.username)
        self.driver.find_element_by_name(
            'password').send_keys(self.password + Keys.RETURN)
        time.sleep(3.2)

    def _nav_user(self, user):
        self.driver.get('{}/{}/'.format(self.base_url, user))

    def _nav_user_new_tab(self, username):
        self.driver.execute_script(
            "window.open('{}');".format(self.base_url + '/' + username))

    def _like_post(self):
        try:
            wait = WebDriverWait(self.driver, 7)
            # click the 'like' button
            wait.until(EC.element_to_be_clickable(
                (By.CLASS_NAME, "fr66n"))).click()
        except Exception as e:
            self._screen_shot(self.username)
            print("_like_post on main: ", e)

    def _get_like_amount_text(self):
        text = ""
        time.sleep(1)
        try:
            text = self.driver.find_element_by_xpath(
                '/html/body/div[4]/div[2]/div/article/div[3]/section[2]/div/div/button/span').text
        except Exception as e:
            pass
        try:
            text = self.driver.find_element_by_xpath(
                '/html/body/div[4]/div[2]/div/article/div[3]/section[2]/div/div[2]/button/span').text
        except Exception as e:
            pass
        finally:
            if text != '':
                # these 3 lines, delete all ',' from the string
                num = text.split(',')
                new_num = ''.join(num)
            else:
                new_num = 0
        return new_num

    # comment on a post
    def _comment_post(self, split_comment):
        # returning random comment from a list of comments
        comment = random.choice(split_comment)
        time.sleep(2)
        # first need to click on the Entry ('add comment...')
        self.driver.find_element_by_class_name('Ypffh').click()
        # Then enter the comment and click post
        self.driver.find_element_by_class_name(
            'Ypffh').send_keys(comment + Keys.RETURN)

    def _follow_user(self, to_distribution, group_id):
        settings_data = self.database.get_data_from_settings()
        time.sleep(1)
        follow_button = self.driver.find_element_by_xpath(
            "/html/body/div[4]/div[2]/div/article/header/div[2]/div[1]/div[2]/button")
        if follow_button.text == 'Follow':
            try:
                # Get the username
                username = self.driver.find_element_by_xpath(
                    '/html/body/div[4]/div[2]/div/article/header/div[2]/div[1]/div[1]/span/a').text
                followers_num, no_use_data = self._get_followers_number(
                    username)
                if followers_num != -1:
                    if int(followers_num) >= int(settings_data[2]):
                        follow_button.click()
                        self.database.save_unfollow_users(
                            username, self.username)
                        if to_distribution:
                            # Get the username
                            username = self.driver.find_element_by_xpath(
                                '/html/body/div[4]/div[2]/div/article/header/div[2]/div[1]/div[1]/span/a').text
                            self.database.add_username_to_distribution_group(
                                username, group_id)
            except Exception as e:
                print('follow user: ', e)

    def _unfollow_user(self, username, user_id):
        self._login()
        self._nav_user(username)
        time.sleep(2)
        try:
            self.driver.find_element_by_xpath(
                '//button[text()="Following"]').click()
            try:
                self._popup_unfollow()
                db.Database().remove_username_from_unfollow_list(username, user_id)
            except Exception as e:
                print('Following unfollow user: ', e)
        except Exception as e:
            pass
        try:
            self.driver.find_element_by_xpath(
                '//button[text()="Requested"]').click()
            try:
                self._popup_unfollow()
                db.Database().remove_username_from_unfollow_list(username, user_id)
            except Exception as e:
                print('Requested unfollow user: ', e)
        except Exception as e:
            pass

    def _popup_unfollow(self):
        # when user is private and you unfollow him, it pops up a message if you sure you want to unfollow
        # this class name is of the popup message and here i check if it exists
        # if it is then click on the button "unfollow"
        popup_unfollow = self.driver.find_element_by_class_name('mt3GC')
        if popup_unfollow:
            self.driver.find_element_by_xpath(
                '//button[text()="Unfollow"]').click()

    def _check_if_blocked(self):
        try:
            error_text = self.driver.find_element_by_xpath(
                '/html/body/div/div[1]/div/div/h2').text
            para_text = self.driver.find_element_by_xpath(
                '/html/body/div/div[1]/div/div/p').text
            if error_text == "Sorry, this page isn't available.":
                return False
            if error_text and para_text:
                print(error_text)
                print(para_text)
                return True
        except Exception as e:
            return False

    def _get_followers_number(self, username):
        self._nav_user_new_tab(username)
        self.driver.switch_to.window(self.driver.window_handles[1])
        self.driver.implicitly_wait(3)
        has_profile_image = self._has_profile_image()
        clean_number = -1
        if has_profile_image == -1:
            try:
                button_list = self.driver.find_elements_by_class_name('g47SY')
                followers_number = button_list[1].text
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
                clean_number = utils().clean_number(followers_number)
            except Exception as e:
                print('get followers number: ', e)
            return clean_number, has_profile_image
        else:
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])
        return clean_number, has_profile_image

    # this method is double check, when i unfollow user, check if the button display 'follow_back'
    # means the user that i just unfollow is following me.
    def _check_if_follow_back(self):
        try:
            wait = WebDriverWait(self.driver, 4)
            follow_back_btn = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Follow Back')]")))
            follow_back_btn.click()
            return True
        except Exception as e:
            return False

    def _get_usersname(self):
        scroll_box = self.driver.find_element_by_xpath(
            "/html/body/div[5]/div/div/div[2]")
        last_height, height = 0, 1
        # this while scrolls all over the followers
        while last_height != height:
            last_height = height
            time.sleep(2)
            height = self.driver.execute_script("""
                                       arguments[0].scrollTo(0, arguments[0].scrollHeight); 
                                       return arguments[0].scrollHeight;
                                       """, scroll_box)

        # Gets all the users name by the class name
        users_name_list = self.driver.find_elements_by_class_name('_0imsa')
        return users_name_list

    def _screen_shot(self, username):
        self.driver.save_screenshot("screen_shots/{}.png".format(username))

    def _send_email(self, username, success_posts, time, section):
        print('sending email')
        mailgun_domain = os.environ.get('MAILGUN_DOMAIN')
        mailgun_api = os.environ.get('MAILGUN_API')
        image_name = username + '.png'
        requests.post("https://api.mailgun.net/v3/{}/messages".format(mailgun_domain),
                      auth=("api", "{}".format(mailgun_api)),
                      files=[("attachment", (username,
                                             open("screen_shots/{}".format(image_name), "rb").read()))],
                      data={"from": "RocketBot <eranbolan91@gmail.com>",
                            "to": ["eranbolan91@gmail.com"],
                            "subject": "RocketBot Error - {}".format(username),
                            "text": """ 
                            Username: {} 
                            Section: {}
                            Success: {} 
                            Time: {}""".format(username, section, success_posts, time)})

    def _blocked_action_popup(self):
        wait = WebDriverWait(self.driver, 4)
        popup_blocked = wait.until(
            EC.element_to_be_clickable((By.CLASS_NAME, "bIiDR")))
        if popup_blocked:
            self._screen_shot(self.username)
            popup_blocked.click()
            return True
        else:
            return False

    def _has_profile_image(self):
        # if this method returns -1, means the user has profile image.
        # if it returns a number bigger then -1 means the user has no profile image
        wait = WebDriverWait(self.driver, 7)
        try:
            # this is for private accounts
            image = wait.until(
                EC.element_to_be_clickable((By.CLASS_NAME, "be6sR")))
            src_text = image.get_attribute("src")
            has_text = src_text.find(
                '44884218_345707102882519_2446069589734326272_n.jpg')
            return has_text
        except:
            pass
        try:
            # this is for none private accounts
            image = wait.until(
                EC.element_to_be_clickable((By.CLASS_NAME, "_6q-tv")))
            src_text = image.get_attribute("src")
            has_text = src_text.find(
                '44884218_345707102882519_2446069589734326272_n.jpg')
            return has_text
        except:
            pass

    def global_block_message(self, username, seaction):
        print("""User: {} has been blocked.\nSection: {}""".format(
            username, seaction))

    def global_complate_task(self, username, section, results):
        print(("""Complate tast: {},\nResults: {}\nUsername: {} """.format(
            section, results, username)))

    # this method checks if the post 'liked'. if it is then it 'unlike' it
    # used for combination
    def is_post_liked(self):
        try:
            self.driver.find_element_by_xpath(
                '//div[@class="_8-yf5"]/*[name()="svg"][@aria-label="Unlike"]').click()
            time.sleep(1.3)
        except Exception as e:
            pass

    def skip_posts(self, num_of_skips):
        wait = WebDriverWait(self.driver, 7)
        for post in range(num_of_skips):
            wait.until(EC.element_to_be_clickable(
                (By.CLASS_NAME, 'coreSpriteRightPaginationArrow'))).click()
            time.sleep(1.5)

    def save_account_action(self, account_action):
        db.Database().save_data_account_action(account_action)
