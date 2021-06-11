from bot_folder import main_bot
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from bs4 import BeautifulSoup as bs


class LikeBot(main_bot.InstagramBot):
    def __init__(self, username, password, is_mobile, proxy_dict):
        super().__init__(username, password, is_mobile, proxy_dict)
        self.wait = WebDriverWait(self.driver, 5)

    def like(self, hashtag, url, likes, skip_posts):
        self._login()
        print("{} -- like: log in".format(
                        self.username))

        self._get_wanted_post(
            hashtag, url, skip_posts)
        print("{} -- like: open post".format(
                        self.username))

        for i in range(likes):
            print("{} -- like: likes left {}/{}".format(
                        self.username, i, likes))
            self._press_like_button()
            self._go_to_next_post()

        self.driver.delete_all_cookies()
        self.driver.close()

    def _get_wanted_post(self, hashtag, url, skip_posts):
        time.sleep(3)
        try:
            if hashtag:
                self.driver.get(
                    '{}/explore/tags/{}'.format(self.base_url, hashtag))
            elif url:
                self.driver.get(url)
            time.sleep(3)
            # click on the first post
            first_post = self.wait.until(
                EC.element_to_be_clickable((By.CLASS_NAME, '_9AhH0')))
            first_post.click()
            self.skip_posts(skip_posts)
            time.sleep(2)
        except Exception as e:
            print('Combination: ', e)

    def _go_to_next_post(self):
        try:
            self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, '/html/body/div[6]/div/div/div[1]/div/div[2]/button'))).click()
            self.wait.until(EC.element_to_be_clickable(
                (By.CLASS_NAME, 'coreSpriteRightPaginationArrow'))).click()
        except Exception as e:
            self.wait.until(EC.element_to_be_clickable(
                (By.CLASS_NAME, 'coreSpriteRightPaginationArrow'))).click()

        time.sleep(1)

    def _open_wanted_post(self, hashtag, url, skip_posts, wait):
        time.sleep(3)
        try:
            if hashtag:
                self.driver.get(
                    '{}/explore/tags/{}'.format(self.base_url, hashtag))
            elif url:
                self.driver.get(url)
            time.sleep(3)
            # click on the first post
            first_post = wait.until(
                EC.element_to_be_clickable((By.CLASS_NAME, '_9AhH0')))
            first_post.click()
            self.skip_posts(skip_posts)
            time.sleep(2)
        except Exception as e:
            print('Combination: ', e)

    def _press_like_button(self):
        time.sleep(2)
        button = self.wait.until(
            EC.element_to_be_clickable((By.CLASS_NAME, 'fr66n')))
        soup = bs(button.get_attribute('innerHTML'), 'html.parser')
        if(soup.find('svg')['aria-label'] == 'Like'):
            button.click()

