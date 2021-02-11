from bot_folder import main_bot
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from database.hashtag.hashtag import HashtagDB
from models.hashtag import Hashtag
import time
from utils.utils import Utils as utils
import datetime as dt


class HashTagBot(main_bot.InstagramBot):
    def __init__(self, username, password, is_mobile, proxy_dict):
        super().__init__(username, password, is_mobile, proxy_dict)
        self.wait = WebDriverWait(self.driver, 7)

    # search instagram page by the hash tag
    def search_hash_tag(self, hash_tag, amount, like, comment, follow, split_comment, to_distribution, group_name,
                        group_id, time_schedule):
        self._login()
        # amount_likes = self.database.get_data_from_settings()
        i = 0
        loops = 0
        click_count = 0
        time.sleep(1.5)
        try:
            self.driver.get('{}/explore/tags/{}'.format(self.base_url, hash_tag))
            wait = WebDriverWait(self.driver, 7)
            first_post = self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, '_9AhH0')))
            first_post.click()
            while i <= int(amount):
                if loops % utils.TIME_SLEEP == 0:
                    if int(amount) != int(i):
                        print('Username:', self.username, 'Time start: ', dt.datetime.now().strftime('%H:%M:%S'),
                              ' Sleep time: ', loops*utils.TIME_SLEEP, 'seconds')
                        time.sleep(loops*utils.TIME_SLEEP)
                # TODO: need to remove line 36 and uncomment line 34 and 35
                # likes_from_insta = self._get_like_amount_text()
                #if int(likes_from_insta) > int(amount_likes[1]):
                if int(20) > int(0):
                    click_count += 1
                    if int(like) == 1:
                        self._like_post()
                    if int(comment) == 1:
                        self._comment_post(split_comment)
                    if int(follow) == 1:
                        self._follow_user(to_distribution, group_id)
                    # click on the right arrow
                    self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'coreSpriteRightPaginationArrow'))).click()
                    i += 1
                    loops += 1
                else:
                    self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'coreSpriteRightPaginationArrow'))).click()
                    i += 1
                    loops += 1
                if int(i * utils.TIME_SLEEP) == 500:
                    loops = 1
                    print('reset to loops')
                try:
                    is_blocked = self._check_if_blocked()
                    if is_blocked:
                        self._screen_shot(self.username)
                        self._send_email(self.username, click_count, dt.datetime.now().strftime('%H:%M:%S'), 'Hashtag')
                        self.driver.close()
                        print('Blocked!')
                        break
                except Exception as e:
                    pass
                print('Hashtag: {}/{}'.format(amount, i), 'Username: ', self.username)
        except Exception as e:
            print('search hash tag: ', e)
        finally:
            # I did -1 because the for loop ends by giving +1 to i (one more then it needs)
            failed_posts_num = int(amount) - (int(click_count))
            self._prepare_data_for_db(hash_tag, amount, like, comment, follow,
                                      split_comment, to_distribution, group_name, failed_posts_num, time_schedule)
            self.driver.delete_all_cookies()
            self.driver.close()

    # Saving Hash-tag data to display in the statistics
    def _prepare_data_for_db(self, hash_tag, amount, like, comment, follow,
                             split_comment, to_distribution, group_name, failed_posts_num, time_schedule):

        join_comment = ','.join(split_comment)
        hashtag = Hashtag(self.username, hash_tag, amount, like, follow, comment,
                          to_distribution, group_name, join_comment, failed_posts_num, time_schedule)
        HashtagDB().save_in_db(hashtag)
