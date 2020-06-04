from bot_folder import main_bot
import time


class DM(main_bot.InstagramBot):
    def send_message_to_distribution_group(self, message, dm_users):
        for user in dm_users:
            time.sleep(10)
            self._nav_user(user[0])
            self.driver.find_element_by_xpath('//button[text()="Message"]').click()
            self._nav_user(self.base_url, user)

