from bot_folder import main_bot
from selenium.webdriver.common.keys import Keys
from database.location.location import LocationDB
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from models.location import Location
import time
from utils.utils import Utils as utils
import datetime as dt


class LocationBot(main_bot.InstagramBot):
    # search for location posts by the URL that the user provides
    def search_location_by_url(self, url, amount, like, follow, comment, split_comment, to_distribution, group_name, group_id, time_schedule):
        self._login()
        amount_likes = self.database.get_data_from_settings()
        i = 1
        time.sleep(2)
        try:
            self.driver.get(url)  # open web browser by the URL
            wait = WebDriverWait(self.driver, 7)
            first_post = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, '_9AhH0')))
            first_post.click()
            while i <= int(amount):
                if i % utils.TIME_SLEEP == 0:
                    if int(amount) != int(i):
                        print('Time start: ', dt.datetime.now(), ' Sleep time: ', i * utils.TIME_SLEEP, 'seconds')
                        time.sleep(i * utils.TIME_SLEEP)
                likes_from_insta = self._get_like_amount_text()
                if int(likes_from_insta) > int(amount_likes[1]):
                    if int(like) == 1:
                        self._like_post()
                    if int(comment) == 1:
                        self._comment_post(split_comment)
                    if int(follow) == 1:
                        self._follow_user(to_distribution, group_id)
                    # click on the right arrow
                    self.driver.find_element_by_class_name('coreSpriteRightPaginationArrow ').click()
                    i += 1
                else:
                    self.driver.find_element_by_class_name('coreSpriteRightPaginationArrow ').click()
        except Exception as e:
            print('search location by url: ', e)
        finally:
            # I did -1 because the for loop ends by giving +1 to i (one more then it needs)
            failed_posts_num = int(amount) - (i - 1)
            self._prepare_data_for_db(url, amount, like, comment, follow,
                                      split_comment, to_distribution, group_name, failed_posts_num, time_schedule)

    # search for location posts by the location name that the user provides
    def search_location_by_name(self, location_name, amount, like, follow, comment, split_comment, to_distribution, group_name, group_id):
        i = 1
        self._search_entry(location_name)
        time.sleep(2)
        self.driver.find_element_by_class_name('_9AhH0').click()  # click the post
        while i <= int(amount):
            if int(like) == 1:
                self._like_post()
            if int(comment) == 1:
                self._comment_post(split_comment)
            if int(follow) == 1:
                self._follow_user()
            self.driver.find_element_by_class_name(
                'coreSpriteRightPaginationArrow ').click()  # click on the right arrow
            i += 1

    def _search_entry(self, name):
        time.sleep(1)
        self.driver.find_element_by_xpath('/html/body/div[1]/section/nav/div[2]/div/div/div[2]/input').click()
        self.driver.find_element_by_xpath('/html/body/div[1]/section/nav/div[2]/div/div/div[2]/input') \
            .send_keys(name + Keys.RETURN)

    # Saving Hash-tag data to display in the statistics
    def _prepare_data_for_db(self, hash_tag, amount, like, comment, follow,
                             split_comment, to_distribution, group_name, failed_posts_num, time_schedule):

        join_comment = ','.join(split_comment)
        hashtag = Location(self.username, hash_tag, amount, like, follow, comment,
                          to_distribution, group_name, join_comment, failed_posts_num, time_schedule)
        LocationDB().save_in_db(hashtag)