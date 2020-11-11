from bot_folder import main_bot
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from database.combination.combination import CombinationDM
from utils.utils import Utils as utils
from models.combination import Combination
import time
import datetime as dt


class CombinationBot(main_bot.InstagramBot):
    def combination(self, hashtag, url, likes, followers, to_distribution, schedule, group_name, group_id):
        users_name_list = []
        buttons = []
        # i starts from 0 because the list of users_name, its the index
        i = 0
        loops = 0
        follow_count = 0
        like_count = 0
        wait = WebDriverWait(self.driver, 5)

        self._login()
        time.sleep(2)
        try:
            if hashtag:
                self.driver.get('{}/explore/tags/{}'.format(self.base_url, hashtag))
            elif url:
                self.driver.get(url)
            # click on the first post
            first_post = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, '_9AhH0')))
            first_post.click()

        except Exception as e:
            print('Combination: ', e)

        try:
            while like_count < likes:
                # like the post
                self._like_post()
                like_count += 1
                # some users cant see the amount of likes. Its display them only others - so click on others
                print(like_count)
                print("This is i: ", i)
                try:
                    wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'others')]"))).click()
                    users_name_list, buttons = self._get_usersname_and_buttons()
                except Exception as e:
                    pass
                    # print('did not find others')
                try:
                    wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[5]/div[2]/div/article/div[3]/section[2]/div/div/button"))).click()
                    users_name_list, buttons = self._get_usersname_and_buttons()
                except Exception as e:
                    pass
                    # print('did not find likes')

                for button in buttons:
                    username = users_name_list[i].text
                    if username == self.username:
                        i += 1
                        username = users_name_list[i].text
                    if button.text == 'Follow':
                        if loops % utils.TIME_SLEEP == 0:
                            print('Username:', self.username, 'Time start:', dt.datetime.now().strftime('%H:%M:%S'), ' Sleep time:',
                                  loops * utils.TIME_SLEEP, 'seconds')
                            time.sleep(loops * utils.TIME_SLEEP)
                        followers_num, has_image_profile = self._get_followers_number(username)
                        if has_image_profile == -1:
                            button.click()
                            follow_count += 1
                            print('Follow count {}/{}'.format(followers, follow_count), 'Username: ', self.username)
                            self.database.save_unfollow_users(username, self.username)
                            if to_distribution:
                                self.database.add_username_to_distribution_group(username, group_id)
                        i += 1
                        loops += 1
                    else:
                        i += 1

                    try:
                        is_action_blocked = self._blocked_action_popup()
                        if is_action_blocked:
                            self._screen_shot(self.username)
                            self._send_email(self.username, follow_count, dt.datetime.now().strftime('%H:%M:%S'),
                                             'Combination')
                            self.driver.close()
                            print('Action Blocked!')
                            break
                    except Exception as e:
                        pass
                    if int(loops * utils.TIME_SLEEP) == 500:
                        loops = 1
                        print('reset loops')
                    if follow_count == followers:
                        break
                # Close the scrolling box and move to the next post
                wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[6]/div/div/div[1]/div/div[2]/button'))).click()
                wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'coreSpriteRightPaginationArrow'))).click()
                # reset i
                i = 0
        except Exception as e:
            print('Combination follow: ', e)
            self._screen_shot(self.username)
            self._send_email(self.username, follow_count, dt.datetime.now().strftime('%H:%M:%S'), 'Combination')
        finally:
            num_likes_failed = int(likes) - int(like_count)
            num_followers_failed = int(followers) - int(follow_count)
            self._prepare_data_for_db(url, hashtag, likes, num_likes_failed, followers, num_followers_failed, schedule, to_distribution, group_name)
            self.driver.delete_all_cookies()
            self.driver.close()

    def _get_usersname_and_buttons(self):
        wait = WebDriverWait(self.driver, 3)
        # getting the box element
        try:
            scroll_box = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[6]/div/div/div[3]')))
            # scroll_box = self.driver.find_element_by_xpath("/html/body/div[6]/div/div/div[3]")
            print('did not reach to scroll first')
        except Exception as e:
            scroll_box = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[6]/div/div/div[2]/div')))
            # scroll_box = self.driver.find_element_by_xpath("/html/body/div[6]/div/div/div[2]/div")
            print('did not reach to scroll')
        time.sleep(1.3)
        last_height, height = 0, 1
        # this while scrolls all over the followers
        while last_height != height:
            last_height = height
            time.sleep(1.2)
            height = self.driver.execute_script("""
                              arguments[0].scrollTo(0, arguments[0].scrollHeight); 
                              return arguments[0].scrollHeight;
                              """, scroll_box)
        # Gets all the users name by the class name
        users_name_list = self.driver.find_elements_by_class_name('MBL3Z')
        # After it scrolled all down the scroll box, this line of code, gets all the buttons into a list
        buttons = scroll_box.find_elements_by_tag_name('button')
        print('The len of buttons: ', len(buttons))
        # button_close.click()
        return users_name_list, buttons

    # Saving Hash-tag data to display in the statistics
    def _prepare_data_for_db(self, url, hashtag, num_likes, num_failed_likes, num_followers,
                num_failed_followers, schedule, distribution, group_name):
        follow_followers = Combination(self.username, url, hashtag, num_likes, num_failed_likes, num_followers, num_failed_followers, schedule, distribution, group_name)
        CombinationDM().save_in_db(follow_followers)