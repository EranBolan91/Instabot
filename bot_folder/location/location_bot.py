from bot_folder import main_bot
from selenium.webdriver.common.keys import Keys
from database.location.location import LocationDB
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from models.location import Location
import time
from utils.utils import Utils as utils
from utils.instagram_selectors import S
import datetime as dt
from utils.log import get_logger

log = get_logger(__name__)


class LocationBot(main_bot.InstagramBot):
    # search for location posts by the URL that the user provides
    def search_location_by_url(self, url, amount, like, follow, comment, split_comment, to_distribution, group_name, group_id, time_schedule):
        if not self._login():
            return
        amount_likes = self.database.get_data_from_settings()
        i = 1
        loops = 1
        click_count = 0
        time.sleep(2)
        try:
            self.driver.get(url)  # open web browser by the URL
            S.click(self.driver, "grid.first_post")
            while i <= int(amount):
                if loops % utils.TIME_SLEEP == 0:
                    if int(amount) != int(i):
                        print('Username:', self.username, 'Time start: ', dt.datetime.now().strftime('%H:%M:%S'),
                                                                  ' Sleep time: ', loops * utils.TIME_SLEEP, 'seconds')
                        time.sleep(loops * utils.TIME_SLEEP)
                # likes_from_insta = self._get_like_amount_text()
                # if int(likes_from_insta) > int(amount_likes[1]):
                click_count += 1
                if int(like) == 1:
                    self._like_post()
                if int(comment) == 1:
                    self._comment_post(split_comment)
                if int(follow) == 1:
                    self._follow_user(to_distribution, group_id)
                    # click on the right arrow
                S.click(self.driver, "post.next_button")
                i += 1
                loops += 1
                # else:
                    # I still want to increase the 'i'
                    # because if the next post will have less likes then again it will sleep
                    # i += 1
                    # loops += 1
                    # self.driver.find_element(By.CLASS_NAME, 'coreSpriteRightPaginationArrow').click()
                print('Loops: {}/{}'.format(amount, click_count), 'Username: ', self.username)
                # stop when Instagram blocks the account, like Hashtag does
                try:
                    is_blocked = self._check_if_blocked()
                except Exception:
                    log.exception("Location %s: could not check if the account is blocked", self.username)
                    is_blocked = False
                if is_blocked:
                    self._screen_shot(self.username)
                    self._send_email(self.username, click_count, dt.datetime.now().strftime('%H:%M:%S'), 'Location')
                    self.global_block_message(self.username, "Location")
                    break
                if int(loops * utils.TIME_SLEEP) == 500:
                    loops = 1
                    print('reset to loops')
        except Exception:
            log.exception("Location %s: run on %s stopped", self.username, url)
        finally:
            # I did -1 because the for loop ends by giving +1 to i (one more then it needs)
            failed_posts_num = int(amount) - (int(click_count))
            self._prepare_data_for_db(url, amount, like, comment, follow,
                                      split_comment, to_distribution, group_name, failed_posts_num, time_schedule)
            self._close_browser()

    # search for location posts by the location name that the user provides
    def search_location_by_name(self, location_name, amount, like, follow, comment, split_comment, to_distribution, group_name, group_id):
        i = 1
        self._search_entry(location_name)
        time.sleep(2)
        S.click(self.driver, "grid.first_post")  # click the post
        while i <= int(amount):
            if int(like) == 1:
                self._like_post()
            if int(comment) == 1:
                self._comment_post(split_comment)
            if int(follow) == 1:
                self._follow_user()
            S.click(self.driver, "post.next_button")  # click on the right arrow
            i += 1

    def _search_entry(self, name):
        time.sleep(1)
        S.click(self.driver, "search.input")
        S.get(self.driver, "search.input").send_keys(name + Keys.RETURN)

    # Saving Hash-tag data to display in the statistics
    def _prepare_data_for_db(self, hash_tag, amount, like, comment, follow,
                             split_comment, to_distribution, group_name, failed_posts_num, time_schedule):

        join_comment = ','.join(split_comment)
        hashtag = Location(self.username, hash_tag, amount, like, follow, comment,
                          to_distribution, group_name, join_comment, failed_posts_num, time_schedule)
        LocationDB().save_in_db(hashtag)