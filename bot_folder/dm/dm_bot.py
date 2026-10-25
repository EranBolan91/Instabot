from bot_folder import main_bot
from selenium.webdriver.common.keys import Keys
from database.dm.dm import DMDB
from models.dm import DM as dm_model
import time
from utils.utils import Utils as utils
from utils.instagram_selectors import S
import datetime as dt
from utils.log import get_logger

log = get_logger(__name__)


class DM(main_bot.InstagramBot):
    def send_message_to_distribution_group(self, message, dm_users, group_name, is_schedule, to_login, account_id, group_id, limit_msg):
        if to_login:
            if not self._login():
                return
        i = 0
        sent = 0
        size_list = len(dm_users)
        dm_users.reverse()
        try:
            for user in dm_users:
                if sent == limit_msg:
                    break
                if i % utils.TIME_SLEEP == 0:
                    print('Account', self.username, 'Time start: ', dt.datetime.now(), ' Sleep time: ', i * utils.TIME_SLEEP, 'seconds')
                    time.sleep(i*utils.TIME_SLEEP)
                self._nav_user(user[0])
                try:
                    S.click(self.driver, "profile.message_button", timeout=4)
                    # Gets to the input message
                    text_input = S.get(self.driver, "dm.message_input", timeout=10)
                    self._type_message(text_input, message)
                    send_button = S.find(self.driver, "dm.send_button", timeout=2)
                    if send_button is not None:
                        S.clickable(send_button).click()
                    else:
                        text_input.send_keys(Keys.RETURN)
                    time.sleep(1.5)
                    # after sending the message, delete the user from the list
                    DMDB().remove_dm_user_from_list(user[0], group_id)
                    sent += 1
                    print('Removed user from distribution list: ', user[0])
                except Exception:
                    log.warning("DM %s: could not send the message to %s", self.username, user[0], exc_info=True)
                # Requested: they never accepted the follow, so cancel it and drop them
                requested = S.find(self.driver, "profile.requested_button", timeout=4)
                if requested is not None:
                    try:
                        S.clickable(requested).click()
                        self._popup_unfollow()
                        DMDB().remove_dm_user_from_list(user[0], group_id)
                        DMDB().remove_username_from_unfollow_list(user[0], account_id)
                        print('Removed user from distribution list and database: ', user[0])
                    except Exception:
                        log.exception("DM %s: could not cancel the follow request to %s", self.username, user[0])
                # A 'Follow' button means I'm not following the user (anymore): drop them
                follow_btn = S.find(self.driver, "profile.follow_button", timeout=4)
                if follow_btn is not None:
                    try:
                        if follow_btn.text.startswith('Follow'):
                            DMDB().remove_dm_user_from_list(user[0], group_id)
                            DMDB().remove_username_from_unfollow_list(user[0], account_id)
                            print('Removed user from distribution list and database: ', user[0])
                    except Exception:
                        log.exception("DM %s: could not remove %s from the list", self.username, user[0])
                try:
                    is_blocked = self._check_if_blocked()
                    if is_blocked:
                        self.global_block_message(self.username, "DM")
                        break
                except Exception:
                    log.exception("DM %s: could not check if the account is blocked", self.username)
                print('DM: sent message to {} {}/{}'.format(user[0], str(size_list), sent), '- Username:', self.username)
                i += 1
                if int(i * utils.TIME_SLEEP) == 500:
                    i = 1
                    print('reset to i')
        except Exception:
            log.exception("DM %s: sending to distribution group %s stopped", self.username, group_name)
        finally:
            self.driver.delete_all_cookies()
            group_len = len(dm_users)
            num_failed_members = group_len - sent
            self._prepare_data_for_db(message, group_name, group_len, num_failed_members, is_schedule)
            self.driver.close()

    def send_message_to_following_list(self, message, is_schedule):
        if not self._login():
            return
        time.sleep(1)
        self._nav_user(self.username)
        S.click(self.driver, "profile.followers_counter", timeout=4)

        users_name = self._get_usersname()
        self.send_message_to_distribution_group(message, users_name, self.username, is_schedule, False)

    # In the chat box Enter sends, so line breaks are typed as Shift+Enter
    def _type_message(self, text_input, message):
        for index, line in enumerate(message.split("\n")):
            if index:
                text_input.send_keys(Keys.SHIFT, Keys.ENTER)
            if line:
                text_input.send_keys(line)

    # Saving Hash-tag data to display in the statistics
    def _prepare_data_for_db(self, message, group, num_members, num_failed_members, is_schedule):
        dm = dm_model(self.username, message, group, num_members, num_failed_members, is_schedule)
        DMDB().save_in_db(dm)


