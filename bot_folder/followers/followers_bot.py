from bot_folder import main_bot
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from database import db
from utils.utils import Utils as utils
import datetime as dt
import time


class FollowersBot(main_bot.InstagramBot):
    def __init__(self, username, password, is_mobile):
        super().__init__(username, password, is_mobile)
        self.wait = WebDriverWait(self.driver, 4)

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
        followers_amount, no_use_data = self._get_followers_number(self.username)
        if int(followers_amount) <= int((len(followers)+10)):
            not_following_back = [user for user in following if user not in followers]
            print(not_following_back)
            print('Not following back: ', len(not_following_back))
            return not_following_back
        else:
            print('Something fucked up with the followers,'
                  'it counted {} followers and the current user has {} followers'.format(len(followers), len(followers_amount)))
            return False

    def _get_names(self):
        time.sleep(2)
        try:
            sugs = self.driver.find_element_by_xpath('//h4[contains(text(), Suggestions)]')
            self.driver.execute_script('arguments[0].scrollIntoView()', sugs)
        except Exception as e:
            pass

        scroll_box = self.wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[5]/div/div/div[2]')))
        button_close = self.wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[5]/div/div/div[1]/div/div[2]/button')))
        last_height, height = 0, 1
        while last_height != height:
            last_height = height
            time.sleep(2)
            height = self.driver.execute_script("""
                arguments[0].scrollTo(0, arguments[0].scrollHeight); 
                return arguments[0].scrollHeight;
                """, scroll_box)
        links = scroll_box.find_elements_by_class_name('Jv7Aj')
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
        self.driver.find_element_by_xpath("//a[contains(@href,'/following')]").click()
        time.sleep(3)
        # getting the box element
        scroll_box = self.driver.find_element_by_xpath("/html/body/div[4]/div/div/div[2]")
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
            if int(i * utils.TIME_SLEEP) == 500:
                i = 1
                print('reset to i')
            i += 1
            if i % utils.TIME_SLEEP == 0:
                print('Account', self.username, 'Time start: ', dt.datetime.now().strftime('%H:%M:%S'), ' Sleep time: ', i * utils.TIME_SLEEP, 'seconds')
                time.sleep(i * utils.TIME_SLEEP)
            button.click()
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
    def unfollow_users(self, user_list, to_remove_from_db, account_id, to_login):
        i = 1
        remove_clicks = 0
        if to_login:
            self._login()
        time.sleep(2.5)
        for user in user_list:
            self._nav_user(user)
            if i % utils.ROUNDS == 0:
                print('Account', self.username, 'Time start: ', dt.datetime.now().strftime('%H:%M:%S'), ' Sleep time: ', i * utils.TIME_SLEEP, 'seconds')
                time.sleep(i*utils.TIME_SLEEP)
            # This try is for accounts that when they access to another user page, it display them Icon following
            try:
                following_btn = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="react-root"]/section/main/div/header/section/div[1]/div[1]/div/div[2]/button ')))
                following_btn.click()
                i += 1
                remove_clicks += 1
                try:
                    self._popup_unfollow()
                    if not to_remove_from_db:
                        self._check_if_follow_back()
                except Exception as e:
                    print('unfollow users pop up exception: ', e)
            except Exception as e:
                pass
                # print('did not find the follow icon')
            try:
                following_btn = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="react-root"]/section/main/div/header/section/div[1]/div[1]/div/div[2]/div/span/span[1]/button')))
                following_btn.click()
                i += 1
                remove_clicks += 1
                try:
                    self._popup_unfollow()
                    if not to_remove_from_db:
                        self._check_if_follow_back()
                except Exception as e:
                    print('unfollow users pop up exception: ', e)
            except Exception as e:
                pass
                # print('did not find the follow icon')
            try:
                following_btn = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="react-root"]/section/main/div/header/section/div[1]/div[2]/div/div[2]/div/span/span[1]/button')))
                following_btn.click()
                i += 1
                remove_clicks += 1
                try:
                    self._popup_unfollow()
                    if not to_remove_from_db:
                        self._check_if_follow_back()
                except Exception as e:
                    print('unfollow users pop up exception: ', e)
            except Exception as e:
                pass
                # print('did not find the follow icon')
            # This try is for accounts that when they access to another user page, it display them "following"
            try:
                following_btn = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, '//button[text()="Following"]')))
                following_btn.click()
                i += 1
                remove_clicks += 1
                try:
                    self._popup_unfollow()
                    if not to_remove_from_db:
                        self._check_if_follow_back()
                except Exception as e:
                    print('unfollow users pop up exception: ', e)
            except Exception as e:
                pass
                # print('did not find the Following button')
            # If it finds Requested button
            try:
                requested_btn = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, '//button[text()="Requested"]')))
                requested_btn.click()
                i += 1
                remove_clicks += 1
                try:
                    self._popup_unfollow()
                    if not to_remove_from_db:
                        self._check_if_follow_back()
                except Exception as e:
                    pass
            except Exception as e:
                pass
            try:
                is_blocked = self._check_if_blocked()
                if is_blocked:
                    self._screen_shot(self.username)
                    self._send_email(self.username, remove_clicks, dt.datetime.now().strftime('%H:%M:%S'), 'Followers')
                    self.driver.close()
                    print('Blocked!')
                    break
            except Exception as e:
                pass

            try:
                is_action_blocked = self._blocked_action_popup()
                if is_action_blocked:
                    self._screen_shot(self.username)
                    self._send_email(self.username, remove_clicks, dt.datetime.now().strftime('%H:%M:%S'), 'Followers')
                    self.driver.close()
                    print('Action Blocked!')
                    break
            except Exception as e:
                pass

            # Remove username from unfollow list
            # This two try and catch are double check, if the bot clicks on 'unfollow' and it does not turn
            # into unfollow. In this situation, i prefer not to remove the username from database
            if to_remove_from_db:
                try:
                    follow_btn = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, '//button[text()="Follow"]')))
                    if follow_btn:
                        print(user, 'Removed from db of', self.username)
                        db.Database().remove_username_from_unfollow_list(user, account_id)
                except Exception as e:
                    pass
                try:
                    follow_btn = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, '//button[text()="Follow Back"]')))
                    if follow_btn:
                        print(user, 'Removed from db', self.username)
                        db.Database().remove_username_from_unfollow_list(user, account_id)
                except Exception as e:
                    pass
            print('{} Removed from {} account'.format(remove_clicks, self.username))
            if int(i * utils.TIME_SLEEP) == 500:
                i = 1
                print('reset to i')

    # unfollow one user
    def unfollow_user(self, username, account_id):
        try:
            self._unfollow_user(username, account_id)
        except Exception as e:
            print('unfollow user: ', e)
        finally:
            self.driver.close()

    def _nav_user(self, user):
        self.driver.get('{}/{}/'.format(self.base_url, user))

    # Getting list of the account followers and compare it with the list of the followers of the account
    # unfollow every user that the account following him and the user not following back
    def unfollow_users_who_not_return_follow(self, unfollowers_list, account_id):
        self._login()
        time.sleep(2)
        self._nav_user(self.username)
        time.sleep(2)
        self.wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href,'/followers')]"))).click()
        followers = self._get_names()
        not_following_back = [user for user in unfollowers_list if user not in followers]
        time.sleep(1.3)
        self.driver.get(self.base_url)
        time.sleep(1)
        self.unfollow_users(not_following_back, 1, account_id, 0)