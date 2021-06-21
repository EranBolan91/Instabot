from bot_folder import main_bot
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from database.dm.dm import DMDB
from database import db
from bot_folder.dm.dm_bot import DM
from models.dm import DM as dm_model
import time
from utils.utils import Utils as utils
import datetime as dt
from selenium.webdriver.common.keys import Keys


class DMTtoFollowers(main_bot.InstagramBot):
    def send_message_to_followers(self, message, limit_msg):
        self.wait = WebDriverWait(self.driver, 4)

        self._login()

        time.sleep(2)
        self._nav_user(self.username)

        self._open_followers()
        scroll_box = self._get_scroll_box()
        followers = self._get_followers(scroll_box, limit_msg)

        for follower in followers:
            self._nav_user(follower)
            self._follow_back()
            try:
                self._send_msg(message)
            except Exception:
                pass

    def _follow_back(self):
        try:
            follow_button = self.driver.find_element_by_xpath(
                '//button[text()="Follow Back"]')
            follow_button.click()
        except:
            return

    def _open_followers(self):
        time.sleep(2)
        self.wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//a[contains(@href,'/followers')]"))).click()

    def _get_current_followers(self):
        users_name_list = self.driver.find_elements_by_class_name('_0imsa')
        followers = []

        try:
            for user in users_name_list:
                followers.append(user.text)
        except:
            pass

        return followers

    def _get_followers(self, scroll_box, limit):
        followers = []
        time.sleep(2)

        while len(followers) < limit:
            self._scroll_down(scroll_box)
            followers = self._get_current_followers()

        return followers[:limit]

    def _get_scroll_box(self):
        return self.wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[5]/div/div/div[2]")))

    def _scroll_down(self, scroll_box):
        self.driver.execute_script("""
            arguments[0].scrollTo(0, arguments[0].scrollHeight); 
            return arguments[0].scrollHeight;
            """, scroll_box)

    def _open_message(self):
        self.wait.until(EC.element_to_be_clickable(
            (By.XPATH, "/html/body/div[1]/section/main/div/header/section/div[1]/div[1]/div/div[1]/button"))).click()

    def _pop_up_box(self):
        time.sleep(3)
        first_post = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, '/html/body/div[5]/div/div/div/div[3]/button[2]')))
        first_post.click()

    def _get_text_area(self):
        return self.driver.find_element_by_xpath(
            '/html/body/div[1]/section/div/div[2]/div/div/div[2]/div[2]/div/div[2]/div/div/div[2]/textarea')

    def _send_msg(self, msg):
        self._open_message()
        self._pop_up_box()

        # click on message area
        send = self._get_text_area()

        # types message
        send.send_keys(msg)
        time.sleep(1)
