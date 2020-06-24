from bot_folder import main_bot
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from database.dm.dm import DMDB
from models.dm import DM as dm_model
import time


class DM(main_bot.InstagramBot):
    def send_message_to_distribution_group(self, message, dm_users, group_name,is_schedule):
        self._login()
        time.sleep(2)
        i = 0
        for user in dm_users:
            self._nav_user(user[0])
            wait = WebDriverWait(self.driver, 6)
            try:
                message_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[text()="Message"]')))
                message_button.click()
                # Gets to the input message
                text_input = wait.until(EC.element_to_be_clickable((By.XPATH,'//*[@id="react-root"]/section/div/div[2]/div/div/div[2]/div[2]/div/div[2]/div/div/div[2]/textarea')))
                text_input.send_keys(message + Keys.RETURN)
                time.sleep(1)
                i += 1
            except Exception as e:
                print('send message to distribution group: ', e)
        group_len = len(dm_users)
        num_failed_members = group_len - i
        self._prepare_data_for_db(message, group_name, group_len, num_failed_members, is_schedule)

    # Saving Hash-tag data to display in the statistics
    def _prepare_data_for_db(self, message, group, num_members, num_failed_members, is_schedule):
        dm = dm_model(self.username, message, group, num_members, num_failed_members, is_schedule)
        DMDB().save_in_db(dm)


