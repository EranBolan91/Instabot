from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time


class InstagramBot:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.base_url = 'https://www.instagram.com'
        self.driver = webdriver.Chrome('chromedriver.exe')
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