from bot_folder import main_bot
from selenium.webdriver.common.keys import Keys
import time


class LocationBot(main_bot.InstagramBot):
    # search for location posts by the URL that the user provides
    def search_location_by_url(self, url, amount, like, follow, comment, split_comment, to_distribution, group_name, group_id):
        self._login()
        i = 1
        time.sleep(2)
        self.driver.get(url)  # open web browser by the URL
        self.driver.find_element_by_class_name('_9AhH0').click()  # click the post
        while i <= int(amount):
            if int(like) == 1:
                self._like_post()
            if int(comment) == 1:
                self._comment_post(split_comment)
            if int(follow) == 1:
                self._follow_user(to_distribution, group_id)
            self.driver.find_element_by_class_name(
                'coreSpriteRightPaginationArrow ').click()  # click on the right arrow
            i += 1

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