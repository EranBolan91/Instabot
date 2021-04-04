from bot_folder import main_bot
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from database.combination.combination import CombinationDM
from database.followers.followers import FollowersDB
from selenium.webdriver.common.action_chains import ActionChains
from utils.utils import Utils as utils
from models.combination import Combination
from models.account_actions import AccountActions
import time
import datetime as dt


class CombinationBot(main_bot.InstagramBot):
    def combination(self, hashtag, url, likes, followers, to_distribution, schedule, group_name, group_id, skip_posts):
        users_name_list = []
        buttons = []
        # i starts from 0 because the list of users_name, its the index
        i = 0
        loops = 0
        follow_count = 0
        like_count = 0
        is_blocked = 0
        wait = WebDriverWait(self.driver, 5)
        settings_data_from_db = CombinationDM().get_data_from_settings()

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
            self.skip_posts(skip_posts)
        except Exception as e:
            print('Combination: ', e)

        try:
            while like_count < likes:
                # like the post
                # self._like_post()
                like_count += 1
                print("Post count: {}/{} account: {} ".format(likes, like_count, self.username))
                self.is_post_liked()
                try:
                    wait.until(EC.element_to_be_clickable(
                        (By.XPATH, "/html/body/div[5]/div[2]/div/article/div[3]/section[2]/div/div/a"))).click()
                except Exception as e:
                    try:
                        wait.until(
                            EC.element_to_be_clickable((By.CLASS_NAME, 'coreSpriteRightPaginationArrow'))).click()
                        continue
                    except Exception as e:
                        pass
                try:
                    scroll_box = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[6]/div/div/div[2]/div')))
                    # print('did not reach to scroll first')
                except Exception as e:
                    scroll_box = wait.until(
                        EC.element_to_be_clickable((By.XPATH, '/html/body/div[6]/div/div/div[3]/div')))
                    # print('did not reach to scroll')
                try:
                    scroll_box = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[6]/div/div/div[3]/div')))
                    # print('did not reach to scroll first')
                except Exception as e:
                    pass
                time.sleep(1.1)
                last_height, height = 0, 1
                # this while scrolls all over the followers
                while last_height != height:
                    last_height = height
                    time.sleep(1.0)
                    height = self.driver.execute_script("""
                                                arguments[0].scrollTo(0, arguments[0].scrollHeight); 
                                                return arguments[0].scrollHeight;
                                                """, scroll_box)
                    time.sleep(1)
                    users_name_list = self.driver.find_elements_by_class_name('MBL3Z')
                    # After it scrolled all down the scroll box, this line of code, gets all the buttons into a list
                    buttons = scroll_box.find_elements_by_tag_name('button')

                    for button in buttons[:11]:
                        try:
                            username = users_name_list[i].text
                            if username == self.username:
                                i += 1
                                username = users_name_list[i].text
                            if button.text == 'Follow':
                                if loops % utils.TIME_SLEEP == 0:
                                    print('Username:', self.username, 'Time start:',
                                          dt.datetime.now().strftime('%H:%M:%S'),
                                          ' Sleep time:',
                                          loops * utils.TIME_SLEEP, 'seconds')
                                    time.sleep(loops * utils.TIME_SLEEP)
                                followers_num, has_image_profile = self._get_followers_number(username)
                                if has_image_profile == -1:
                                    if int(followers_num) >= int(settings_data_from_db[2]):
                                        # ActionsChains(self.driver).move_to_element(button).click(button).perform()
                                        button.click()
                                        follow_count += 1
                                        print('Combination count {}/{}'.format(followers, follow_count), 'Username: ',
                                              self.username)
                                        self.database.save_unfollow_users(username, self.username)
                                        if to_distribution:
                                            self.database.add_username_to_distribution_group(username, group_id)
                                        try:
                                            is_action_blocked = self._blocked_action_popup()
                                            if is_action_blocked:
                                                self._send_email(self.username, follow_count,
                                                                 dt.datetime.now().strftime('%H:%M:%S'),
                                                                 'Combination')
                                                self.global_block_message(self.username, "Combination")
                                                is_blocked = 1
                                                break
                                        except Exception as e:
                                            pass
                                i += 1
                                loops += 1
                            else:
                                i += 1
                        except Exception as e:
                            i += 1
                            print("Combination inside while: ", e)

                        if int(loops * utils.TIME_SLEEP) == 500:
                            loops = 1
                            print('reset loops')
                        if follow_count >= followers:
                            break
                        # TODO: i need to find a way to break the while loop when i get block. now its only breaking the for loop
                        if is_blocked:
                            break
                    # reset the lists after every one scroll down
                    buttons = []
                    users_name_list = []
                    i = 0
                    if follow_count >= followers:
                        break
                    # TODO: i need to find a way to break the while loop when i get block. now its only breaking the for loop
                    if is_blocked:
                        break
                # Close the scrolling box and move to the next post
                # I added try and catch for posts that are videos and have no likes or others, so when it try to close
                # the scroll box it wont find it and skip to the next post
                try:
                    wait.until(EC.element_to_be_clickable(
                        (By.XPATH, '/html/body/div[6]/div/div/div[1]/div/div[2]/button'))).click()
                    wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'coreSpriteRightPaginationArrow'))).click()
                    # reset i
                    i = 0
                except Exception as e:
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
            self._prepare_data_for_db(url, hashtag, likes, num_likes_failed, followers, num_followers_failed, schedule,
                                      to_distribution, group_name)
            self.driver.delete_all_cookies()
            self.driver.close()

    # Saving Hash-tag data to display in the statistics
    def _prepare_data_for_db(self, url, hashtag, num_likes, num_failed_likes, num_followers,
                num_failed_followers, schedule, distribution, group_name):
        follow_followers = Combination(self.username, url, hashtag, num_likes, num_failed_likes, num_followers, num_failed_followers, schedule, distribution, group_name)
        CombinationDM().save_in_db(follow_followers)
        account_id = CombinationDM().get_user_id(self.username)
        account_action = AccountActions(account_id, self.username, "Combination", num_followers, num_followers - num_failed_followers)
        FollowersDB().save_data_account_action(account_action)