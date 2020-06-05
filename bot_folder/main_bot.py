from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from database import db
import time, random


class InstagramBot:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.base_url = 'https://www.instagram.com'
        self.driver = webdriver.Chrome('chromedriver.exe')
        self.database = db.Database()
        self._login()

    def get_username(self):
        return self.username

    def get_password(self):
        return self.password

    def _login(self):
        self.driver.get('{}/accounts/login/'.format(self.base_url))
        time.sleep(2)
        self.driver.find_element_by_name('username').send_keys(self.username)
        self.driver.find_element_by_name('password').send_keys(self.password + Keys.RETURN)
        time.sleep(3)
        try:
            self.driver.find_element_by_xpath("//button[contains(text(), 'Not Now')]").click()
        except:
            print("Didn't find 'not now'")

    def _nav_user(self, user):
        self.driver.get('{}/{}/'.format(self.base_url, user))

    def _like_post(self):
        time.sleep(1)
        self.driver.find_element_by_class_name('fr66n').click()  # click the 'like' button

    def _get_like_amount_text(self):
        time.sleep(1.9)
        try:
            text = self.driver.find_element_by_xpath(
                '/html/body/div[4]/div[2]/div/article/div[2]/section[2]/div/div/button/span').text
            if text != '':
                # these 3 lines, delete all ',' from the string
                num = text.split(',')
                new_num = ''.join(num)
                print(new_num)
            else:
                new_num = 0
        except:
            new_num = 0
        return new_num

    # comment on a post
    def _comment_post(self, split_comment):
        # returning random comment from a list of comments
        comment = random.choice(split_comment)
        time.sleep(3)
        # first need to click on the Entry ('add comment...')
        self.driver.find_element_by_class_name('Ypffh').click()
        # Then enter the comment and click post
        self.driver.find_element_by_class_name('Ypffh').send_keys(comment + Keys.RETURN)

    def _follow_user(self, to_distribution, group_id):
        time.sleep(1)
        # TODO: not the correct way of doing it. I need to change it to check if im following the user or not
        follow_button = self.driver.find_element_by_xpath(
            "/html/body/div[4]/div[2]/div/article/header/div[2]/div[1]/div[2]/button")
        if follow_button.text == 'Follow':
            follow_button.click()
            # Get the username
            username = self.driver.find_element_by_xpath(
                '/html/body/div[4]/div[2]/div/article/header/div[2]/div[1]/div[1]/a').text
            self.database.save_unfollow_users(username, self.username)

        if to_distribution:
            username = self.driver.find_element_by_xpath(
                '/html/body/div[4]/div[2]/div/article/header/div[2]/div[1]/div[1]/a').text
            self.database.add_username_to_distribution_group(username, group_id)

    def _popup_unfollow(self):
        # when user is private and you unfollow him, it pops up a message if you sure you want to unfollow
        # this class name is of the popup message and here i check if it exists
        # if it is then click on the button "unfollow"
        popup_unfollow = self.driver.find_element_by_class_name('mt3GC')
        if popup_unfollow:
            self.driver.find_element_by_xpath('/html/body/div[5]/div/div/div[3]/button[1]').click()
            # can also use this self.driver.find_element_by_xpath('//button[text()="Unfollow"]').click()
