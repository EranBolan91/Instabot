from bot_folder import main_bot
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from database.dm.dm import DMDB
from models.dm import DM as dm_model
import time
from utils.utils import Utils as utils
import datetime as dt


class DMTtoFollowers(main_bot.InstagramBot):
    def send_message_to_followers(self, message, limit_msg):
        self.wait = WebDriverWait(self.driver, 4)

        self._login()
        time.sleep(2)
        self._nav_user(self.username)

        followers = self._get_followers()
        """
        for follower in followers:
            self._nav_user_new_tab(self.username)
            self._send_msg(follower)

        self.driver.delete_all_cookies()
        self.driver.close()
        """
    def _get_followers(self):
        time.sleep(2)
        self.wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href,'/followers')]"))).click()

        users_name_list = self.driver.find_elements_by_xpath('/html/body/div[5]/div/div/div[2]/ul/div')
        print(users_name_list)

    def _open_messages(self):
        message_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//button[text()="Message"]')))
        message_button.click()

    def _send_msg(self, msg):
        text_input = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="react-root"]/section/div[2]/div/div/div[2]/div/div/div/textarea')))
        text_input.send_keys(msg)

