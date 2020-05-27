from bot_folder import main_bot
import time


class HashTagBot(main_bot.InstagramBot):
    # search instagram page by the hash tag
    def search_hash_tag(self, hash_tag, amount, like, comment, follow, split_comment):
        amount_likes = self.database.get_data_from_settings()
        i = 1
        time.sleep(2)
        self.driver.get('{}/explore/tags/{}'.format(self.base_url, hash_tag))
        self.driver.find_element_by_class_name('_9AhH0').click()  # click the post
        while i <= int(amount):
            likes_from_insta = self._get_like_amount_text()
            if int(likes_from_insta) > int(amount_likes[1]):
                if int(like) == 1:
                    self._like_post()
                if int(comment) == 1:
                    self._comment_post(split_comment)
                if int(follow) == 1:
                    self._follow_user()
                # click on the right arrow
                self.driver.find_element_by_class_name('coreSpriteRightPaginationArrow ').click()
                i += 1
            else:
                self.driver.find_element_by_class_name('coreSpriteRightPaginationArrow ').click()
