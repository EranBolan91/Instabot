from bot_folder import main_bot
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import time
from database import db
from utils.utils import Utils as utils
import datetime as dt


class FollowersBot(main_bot.InstagramBot):
    def get_unfollowers(self):
        self._login()
        time.sleep(2)
        self._nav_user(self.username)
        time.sleep(2)
        self.driver.find_element_by_xpath("//a[contains(@href,'/following')]") \
            .click()
        following = self._get_names()
        self.driver.find_element_by_xpath("//a[contains(@href,'/followers')]") \
            .click()
        followers = self._get_names()
        not_following_back = [user for user in following if user not in followers]
        return not_following_back

    def _get_names(self):
        time.sleep(2)
        try:
            sugs = self.driver.find_element_by_xpath('//h4[contains(text(), Suggestions)]')
            self.driver.execute_script('arguments[0].scrollIntoView()', sugs)
        except Exception as e:
            print(" get names: ", e)

        wait = WebDriverWait(self.driver, 4)
        scroll_box = wait.until(EC.element_to_be_clickable((By.XPATH, '/ html / body / div[4] / div / div / div[2]')))
        button_close = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[4]/div/div/div[1]/div/div[2]/button')))
        last_height, height = 0, 1
        while last_height != height:
            last_height = height
            time.sleep(2)
            height = self.driver.execute_script("""
                arguments[0].scrollTo(0, arguments[0].scrollHeight); 
                return arguments[0].scrollHeight;
                """, scroll_box)
        links = scroll_box.find_elements_by_tag_name('a')
        names = [name.text for name in links if name.text != '']
        # close button
        button_close.click()
        return names

    # This unfollow, goes to the current account, click on the 'Following'
    # and go over all the users and then unfollow them one by one
    def unfollow_all_users(self):
        self._login()
        time.sleep(2)
        self.driver.get(self.base_url + "/" + self.username)
        time.sleep(3)
        # Open the following page
        self.driver.find_element_by_xpath("//a[contains(@href,'/following')]") \
            .click()
        try:
            time.sleep(2)
            # sometimes when you scroll to fast, it display to you the suggestions
            sugs = self.driver.find_element_by_xpath('//h4[contains(text(), Suggestions)]')
            self.driver.execute_script('arguments[0].scrollIntoView()', sugs)
        except Exception as e:
            print('unfollow all users: ', e)
        time.sleep(3)
        # getting the box element
        scroll_box = self.driver.find_element_by_xpath("/ html / body / div[4] / div / div / div[2]")
        last_height, height = 0, 1
        # this while scrolls all over the followers
        while last_height != height:
            last_height = height
            time.sleep(2)
            height = self.driver.execute_script("""
                             arguments[0].scrollTo(0, arguments[0].scrollHeight); 
                             return arguments[0].scrollHeight;
                             """, scroll_box)
        # After it scrolled all down the scroll box, this line of code, gets all the buttons into a list
        buttons = scroll_box.find_elements_by_tag_name('button')
        i = 0
        # This for runs all over the buttons list and click 'follow'
        for button in buttons:
            i += 1
            if i % utils.TIME_SLEEP == 0:
                print('Time start: ', dt.datetime.now(), ' Sleep time: ', i * utils.TIME_SLEEP, 'seconds')
                time.sleep(i * utils.TIME_SLEEP)
            button.click()
            # TODO: Need to get the names of the users so i can remove them from DB
            # when user is private and you unfollow him, it pops up a message if you sure you want to unfollow
            # this class name is of the popup message and here i check if it exists
            # if it is then click on the button "unfollow"
            try:
                self._popup_unfollow()
            except Exception as e:
                print('unfollow all users: ', e)

        self.driver.close()

    # unfollow users - gets list of users
    # Go to each user and unfollow him
    def unfollow_users(self, user_list):
        i = 1
        self._login()
        for user in user_list:
            self._nav_user(user)
            if i % utils.TIME_SLEEP == 0:
                print('Time start: ', dt.datetime.now(), ' Sleep time: ', i * utils.TIME_SLEEP, 'seconds')
                time.sleep(i*utils.TIME_SLEEP)
            # This try is for accounts that when they access to another user page, it display them Icon following
            try:
                wait = WebDriverWait(self.driver, 4)
                following_btn = wait.until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="react-root"]/section/main/div/header/section/div[1]/div[2]/span/span[1]/button/div/span')))
                following_btn.click()
                i += 1
                try:
                    self._popup_unfollow()
                except Exception as e:
                    print('unfollow users pop up exception: ', e)
            except Exception as e:
                print('didnt not find the follow icon')
            # This try is for accounts that when they access to another user page, it display them "following"
            try:
                wait = WebDriverWait(self.driver, 4)
                following_btn = wait.until(
                    EC.element_to_be_clickable((By.XPATH, '//button[text()="Following"]')))
                following_btn.click()
                i += 1
                try:
                    self._popup_unfollow()
                except Exception as e:
                    print('unfollow users pop up exception: ', e)
            except Exception as e:
                # wait = WebDriverWait(self.driver, 4)
                # requested_btn = wait.until(
                #     EC.element_to_be_clickable((By.XPATH, '//button[text()="Requested"]')))
                # requested_btn.click()
                # self._popup_unfollow()
                print('unfollow users requested button: ', e)

    # unfollow one user
    def unfollow_user(self, username):
        self._login()
        self._nav_user(username)
        time.sleep(2)
        self.driver.find_element_by_xpath('//button[text()="Following"]').click()
        try:
            self._popup_unfollow()
            db.Database().remove_username_from_unfollow_list(username)
        except Exception as e:
            print('unfollow user: ', e)
        finally:
            self.driver.close()

    def _nav_user(self, user):
        self.driver.get('{}/{}/'.format(self.base_url, user))