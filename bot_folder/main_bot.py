from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from utils.utils import Utils as utils
from database import db
import time, random


class InstagramBot:
    def __init__(self, username, password, is_mobile):
        self.database = db.Database()
        self.username = username
        self.password = password
        self.base_url = 'https://www.instagram.com'
        # the options from this website -> https://www.selenium.dev/documentation/en/webdriver/page_loading_strategy/
        options = Options()
        options.page_load_strategy = 'eager'
        chrome_options = webdriver.ChromeOptions()
        # # This is how to set PRXY
        # PROXY = "92.119.62.163"
        # chrome_options.add_argument('--proxy-server=%s' % PROXY)
        if is_mobile:
            mobile_emulation = {"deviceName": "Nexus 5"}
            chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)
            self.driver = webdriver.Chrome('chromedriver.exe', options=options, chrome_options=chrome_options)
        else:
            self.driver = webdriver.Chrome('chromedriver.exe', options=options)

    def get_username(self):
        return self.username

    def get_password(self):
        return self.password

    def _login(self):
        self.driver.get('{}/accounts/login/'.format(self.base_url))
        time.sleep(1.5)
        self.driver.find_element_by_name('username').send_keys(self.username)
        self.driver.find_element_by_name('password').send_keys(self.password + Keys.RETURN)
        time.sleep(1.5)
        try:
            wait = WebDriverWait(self.driver, 7)
            popup_not_now = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Not Now')]")))
            popup_not_now.click()
        except Exception as e:
            print("Didn't find 'not now' :", e)

    def _nav_user(self, user):
        self.driver.get('{}/{}/'.format(self.base_url, user))

    def _nav_user_new_tab(self, username):
        self.driver.execute_script("window.open('{}');".format(self.base_url + '/' + username))

    def _like_post(self):
        time.sleep(1)
        self.driver.find_element_by_class_name('fr66n').click()  # click the 'like' button

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
                print(new_num)
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
        self.driver.find_element_by_class_name('Ypffh').send_keys(comment + Keys.RETURN)

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
                followers_num = self._get_followers_number(username)
                if int(followers_num) >= int(settings_data[2]):
                    follow_button.click()
                    self.database.save_unfollow_users(username, self.username)
                    if to_distribution:
                        # Get the username
                        username = self.driver.find_element_by_xpath(
                            '/html/body/div[4]/div[2]/div/article/header/div[2]/div[1]/div[1]/span/a').text
                        self.database.add_username_to_distribution_group(username, group_id)
            except Exception as e:
                print('follow user: ', e)

    def _popup_unfollow(self):
        # when user is private and you unfollow him, it pops up a message if you sure you want to unfollow
        # this class name is of the popup message and here i check if it exists
        # if it is then click on the button "unfollow"
        popup_unfollow = self.driver.find_element_by_class_name('mt3GC')
        if popup_unfollow:
            self.driver.find_element_by_xpath('//button[text()="Unfollow"]').click()

    def _check_if_blocked(self):
        error_text = self.driver.find_element_by_xpath('/html/body/div/div[1]/div/div/h2').text
        para_text = self.driver.find_element_by_xpath('/html/body/div/div[1]/div/div/p').text
        if error_text == "Sorry, this page isn't available.":
            return False
        if error_text and para_text:
            print(error_text)
            print(para_text)
            return True

    def _get_followers_number(self, username):
        followers_number = 0
        self._nav_user_new_tab(username)
        self.driver.switch_to.window(self.driver.window_handles[1])
        self.driver.implicitly_wait(3)
        try:
            button_list = self.driver.find_elements_by_class_name('g47SY')
            followers_number = button_list[1].text
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])
            clean_number = utils().clean_number(followers_number)
            print(clean_number)
        except Exception as e:
            print('get followers number: ', e)
        return int(clean_number)


