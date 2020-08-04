from bot_folder import main_bot
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from database.dm.dm import DMDB
from models.dm import DM as dm_model
import time
from utils.utils import Utils as utils
import datetime as dt


class DM(main_bot.InstagramBot):
    def send_message_to_distribution_group(self, message, dm_users, group_name, is_schedule):
        self._login()
        i = 0
        try:
            for user in dm_users:
                # Sleep after sending to 5 accounts message
                if i % utils.TIME_SLEEP == 0:
                    print('Time start: ', dt.datetime.now(), ' Sleep time: ', i * utils.TIME_SLEEP, 'seconds')
                    time.sleep(i*utils.TIME_SLEEP)
                self._nav_user(user[0])
                wait = WebDriverWait(self.driver, 4)
                try:
                    message_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[text()="Message"]')))
                    message_button.click()
                    # Gets to the input message
                    text_input = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="react-root"]/section/div[2]/div/div/div[2]/div/div/div/textarea')))
                    text_input.send_keys(message)
                    self.driver.find_element_by_xpath('//*[@id="react-root"]/section/div[2]/div/div/div[2]/div/div/div[2]/button').click()
                    # after sending the message, delete the user from the list
                    DMDB().remove_dm_user_from_list(user[0])
                except Exception as e:
                    pass
                try:
                    # Requested
                    requested_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[text()="Requested"]')))
                    requested_btn.click()
                    try:
                        self._popup_unfollow()
                        DMDB().remove_dm_user_from_list(user[0])
                        DMDB().remove_username_from_unfollow_list(user[0])
                    except Exception as e:
                        pass
                except Exception as e:
                    pass
                try:
                    is_blocked = self._check_if_blocked()
                    if is_blocked:
                        print('Block')
                        break
                    else:
                        # will remove the username if i'm not following the user and its not requested and its not blocked or
                        # maybe the webpage is not available
                        # in this situation i'm not following the user, so i should remove him from the list
                        DMDB().remove_dm_user_from_list(user[0])
                        DMDB().remove_username_from_unfollow_list(user[0])
                except Exception as e:
                    pass
                print('index: ', i)
                i += 1
        except Exception as e:
            print('send message to distribution group: ', e)
        finally:
            self.driver.delete_all_cookies()
            group_len = len(dm_users)
            num_failed_members = group_len - i
            self._prepare_data_for_db(message, group_name, group_len, num_failed_members, is_schedule)
            self.driver.close()

    # Saving Hash-tag data to display in the statistics
    def _prepare_data_for_db(self, message, group, num_members, num_failed_members, is_schedule):
        dm = dm_model(self.username, message, group, num_members, num_failed_members, is_schedule)
        DMDB().save_in_db(dm)


