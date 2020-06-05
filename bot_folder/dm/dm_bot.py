from bot_folder import main_bot
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time


class DM(main_bot.InstagramBot):
    def send_message_to_distribution_group(self, message, dm_users):
        for user in dm_users:
            self._nav_user(user[0])
            wait = WebDriverWait(self.driver, 6)
            message_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[text()="Message"]')))
            message_button.click()
            # Gets to the input message
            text_input = wait.until(EC.element_to_be_clickable((By.XPATH,'//*[@id="react-root"]/section/div/div[2]/div/div/div[2]/div[2]/div/div[2]/div/div/div[2]/textarea')))
            text_input.send_keys(message + Keys.RETURN)

            time.sleep(1)

