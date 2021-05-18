from bot_folder import main_bot
from database.follow_followers.follow_followers import FollowFollowersDB
from models.follow_followers import FollowFollowers
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import time
from utils.utils import Utils as utils
import datetime as dt


class FollowFollowersBot(main_bot.InstagramBot):
    def follow_after_followers(self, user_url, account_username, num_of_following, to_distribution, group_name, group_id, is_schedule, num_skip):
        settings_data_from_db = FollowFollowersDB().get_data_from_settings()
        self._login()
        time.sleep(1.5)
        self.driver.get(user_url)
        time.sleep(1.5)
        # Open the followers page
        wait = WebDriverWait(self.driver, 7)
        wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href,'/followers')]"))).click()
        # getting the box element
        scroll_box = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[5]/div/div/div[2]")))
        # follow_count is for sub from the i in the end of the loop.
        # count how many clicks it did. how many actual users i followed
        follow_count = 0
        # this while scrolls all over the followers
        i = 1
        try:
            while follow_count <= num_of_following:
                time.sleep(1)
                self.driver.execute_script("""
                           arguments[0].scrollTo(0, arguments[0].scrollHeight); 
                           return arguments[0].scrollHeight;
                           """, scroll_box)
                # Gets all the users name by the class name
                users_name_list = self.driver.find_elements_by_class_name('_0imsa')
                # After it scrolled all down the scroll box, this line of code, gets all the buttons into a list
                buttons = scroll_box.find_elements_by_tag_name('button')
                # i starts from 0 because the list of users_name, its the index
                #i = 0
                # reset the wait time after a specific time
                # This for runs all over the buttons list and click 'follow'
                # for looping
                buttons_length = len(buttons)
                loops = 0
                try:
                    for btn_index in range(i, buttons_length):
                        username = users_name_list[i].text
                        # This 'if' statement is avoid current username on the following list
                        # I increase the i because the 'buttons' return 1 short button.
                        # For example there are 100 people,
                        # it will return 99 because the current user has no button (follow button)
                        # So i increase the i to skip the current username and move to the next user
                        if username == self.username:
                            i += 1
                            username = users_name_list[i].text
                        if buttons[btn_index].text == 'Follow':
                            if loops % utils.TIME_SLEEP == 0:
                                print('Username:', account_username, 'Time start:',
                                      dt.datetime.now().strftime('%H:%M:%S'), ' Sleep time:',
                                      loops * utils.TIME_SLEEP, 'seconds')
                                time.sleep(loops * utils.TIME_SLEEP)
                            followers_num, has_image_profile = self._get_followers_number(username)
                            if has_image_profile == -1:
                                if int(followers_num) >= int(settings_data_from_db[2]):
                                    buttons[btn_index].click()
                                    follow_count += 1
                                    try:
                                        is_action_blocked = self._blocked_action_popup()
                                        if is_action_blocked:
                                            self._send_email(self.username, follow_count,
                                                             dt.datetime.now().strftime('%H:%M:%S'),
                                                             'Follow Followers')
                                            # self.driver.close()
                                            self.global_block_message(self.username, "Follow followers")
                                            break
                                    except Exception as e:
                                        pass
                                    print('Follow count {}/{}'.format(num_of_following, follow_count), 'Username: ',
                                          account_username)
                                    self.database.save_unfollow_users(username, account_username)
                                    if to_distribution:
                                        self.database.add_username_to_distribution_group(username, group_id)
                            i += 1
                            loops += 1
                        else:
                            i += 1
                        if int(loops * utils.TIME_SLEEP) == 500:
                            loops = 1
                            print('reset loops')
                        if follow_count == num_of_following:
                            break
                except Exception as e:
                    print('follow after followers ', e)
                    self._screen_shot(self.username)
                    self._send_email(self.username, follow_count, dt.datetime.now().strftime('%H:%M:%S'),
                                     'Follow followers')
                users_name_list = []
                buttons = []
        except Exception as e:
            pass
        finally:
            self.driver.delete_all_cookies()
            # I did -1 because the for loop ends by giving +1 to i (one more then it needs)
            failed_follow_num = int(num_of_following) - follow_count
            self._prepare_data_for_db(user_url, num_of_following, to_distribution, group_name, failed_follow_num,
                                      is_schedule, num_skip)
            self.driver.close()

    def follow_after_following(self, user_url, account_username, num_of_following, to_distribution, group_name, group_id, is_schedule, num_skip):
        settings_data_from_db = FollowFollowersDB().get_data_from_settings()
        self._login()
        time.sleep(2)
        self.driver.get(user_url)
        time.sleep(2)
        # Open the followers page
        wait = WebDriverWait(self.driver, 7)
        wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href,'/following')]"))).click()
        time.sleep(1.5)
        # getting the box element
        scroll_box = self.driver.find_element_by_xpath("/html/body/div[5]/div/div/div[2]")
        last_height, height = 0, 1
        # this while scrolls all over the followers
        while last_height != height:
            last_height = height
            time.sleep(0.7)
            height = self.driver.execute_script("""
                          arguments[0].scrollTo(0, arguments[0].scrollHeight); 
                          return arguments[0].scrollHeight;
                          """, scroll_box)
        # Gets all the users name by the class name
        users_name_list = self.driver.find_elements_by_class_name('_0imsa')
        # After it scrolled all down the scroll box, this line of code, gets all the buttons into a list
        buttons = scroll_box.find_elements_by_tag_name('button')
        # i starts from 0 because the list of users_name, its the index
        i = num_skip
        # follow_count is for sub from the i in the end of the loop.
        # count how many clicks it did. how many actual users i followed
        follow_count = 0
        # for looping
        loops = 0
        try:
            # This for runs all over the buttons list and click 'follow'
            for btn_index in range(i, len(buttons)):
            #for button in buttons:
                username = users_name_list[i].text
                if buttons[btn_index].text == 'Follow':
                    if loops % utils.TIME_SLEEP == 0:
                        print('Username:', account_username, 'Time start: ', dt.datetime.now().strftime('%H:%M:%S'), ' Sleep time: ',
                              loops * utils.TIME_SLEEP, 'seconds')
                        time.sleep(loops * utils.TIME_SLEEP)
                    followers_num, has_image_profile = self._get_followers_number(username)
                    if has_image_profile == -1:
                        if int(followers_num) >= int(settings_data_from_db[2]):
                            buttons[btn_index].click()
                            follow_count += 1
                            print('Follow count {}/{}'.format(num_of_following, follow_count), 'Username: ',
                                  account_username)
                            self.database.save_unfollow_users(username, account_username)
                            if to_distribution:
                                self.database.add_username_to_distribution_group(username, group_id)
                    loops += 1
                    i += 1
                else:
                    i += 1
                try:
                    is_action_blocked = self._blocked_action_popup()
                    if is_action_blocked:
                        self._send_email(self.username, follow_count, dt.datetime.now().strftime('%H:%M:%S'),
                                         'Follow Followers')
                        # self.driver.close()
                        self.global_block_message(self.username, "Follow followers")
                        break
                except Exception as e:
                    pass
                if int(loops * utils.TIME_SLEEP) == 500:
                    loops = 1
                    print('reset to loops')

                if follow_count == num_of_following:
                    break
        except Exception as e:
            print('follow after following: ', e)
        finally:
            self.driver.delete_all_cookies()
            # I did -1 because the for loop ends by giving +1 to i (one more then it needs)
            failed_follow_num = int(num_of_following) - follow_count
            self._prepare_data_for_db(user_url, num_of_following, to_distribution, group_name, failed_follow_num,
                                      is_schedule, num_skip)
            self.driver.close()

    # Saving Hash-tag data to display in the statistics
    def _prepare_data_for_db(self, user_url, num_of_following, to_distribution, group_name, failed_follow_num, is_schedule, num_skip):
        follow_followers = FollowFollowers(self.username, user_url, num_of_following, failed_follow_num, to_distribution, group_name, is_schedule, num_skip)
        FollowFollowersDB().save_in_db(follow_followers)
