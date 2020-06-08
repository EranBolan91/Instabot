from bot_folder import main_bot
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import time


class FollowersBot(main_bot.InstagramBot):
    def get_unfollowers(self):
        self._login()
        time.sleep(3)
        self._nav_user(self.username)
        time.sleep(2)
        self.driver.find_element_by_xpath("//a[contains(@href,'/following')]") \
            .click()
        following = self._get_names()
        self.driver.find_element_by_xpath("//a[contains(@href,'/followers')]") \
            .click()
        followers = self._get_names()
        not_following_back = [user for user in following if user not in followers]
        print(not_following_back)
        return not_following_back

    def _get_names(self):
        time.sleep(2)
        try:
            sugs = self.driver.find_element_by_xpath('//h4[contains(text(), Suggestions)]')
            self.driver.execute_script('arguments[0].scrollIntoView()', sugs)
        except:
            print("Didn't find Suggestions")

        time.sleep(3)
        scroll_box = self.driver.find_element_by_xpath("/html/body/div[4]/div/div[2]")
        last_height, height = 0, 1
        while last_height != height:
            last_height = height
            time.sleep(3)
            height = self.driver.execute_script("""
                arguments[0].scrollTo(0, arguments[0].scrollHeight); 
                return arguments[0].scrollHeight;
                """, scroll_box)
        links = scroll_box.find_elements_by_tag_name('a')
        names = [name.text for name in links if name.text != '']
        # close button
        self.driver.find_element_by_xpath("/html/body/div[4]/div/div[1]/div/div[2]/button") \
            .click()
        return names

    def unfollow_all_users(self):
        time.sleep(2)
        self.driver.get(self.base_url + "/" + self.username)
        time.sleep(3)
        # Open the following page
        self.driver.find_element_by_xpath("//a[contains(@href,'/following')]") \
            .click()
        try:
            time.sleep(2)
            # sometimes when you scroll to fast, it display to you the suggestions
            sugs = self.driver.find_element_by_xpath('//h4[contains(text(), Suggestions)]')
            self.driver.execute_script('arguments[0].scrollIntoView()', sugs)
        except Exception as e:
            print('unfollow all users: ', e)
        time.sleep(3)
        # getting the box element
        scroll_box = self.driver.find_element_by_xpath("/html/body/div[4]/div/div[2]")
        last_height, height = 0, 1
        # this while scrolls all over the followers
        while last_height != height:
            last_height = height
            time.sleep(3)
            height = self.driver.execute_script("""
                             arguments[0].scrollTo(0, arguments[0].scrollHeight); 
                             return arguments[0].scrollHeight;
                             """, scroll_box)
        # After it scrolled all down the scroll box, this line of code, gets all the buttons into a list
        buttons = scroll_box.find_elements_by_tag_name('button')
        print(buttons)
        i = 0
        # This for runs all over the buttons list and click 'follow'
        for button in buttons:
            i += 1
            time.sleep(1)
            button.click()
            time.sleep(1)
            # TODO: popup_unfollow should be a method in "main_bot"
            # when user is private and you unfollow him, it pops up a message if you sure you want to unfollow
            # this class name is of the popup message and here i check if it exists
            # if it is then click on the button "unfollow"
            try:
                self._popup_unfollow()
            except Exception as e:
                print('unfollow all users: ', e)
            #popup_unfollow = self.driver.find_element_by_class_name('mt3GC')
            #if popup_unfollow:
             #   self.driver.find_element_by_xpath('/html/body/div[5]/div/div/div[3]/button[1]').click()
                # can also use this self.driver.find_element_by_xpath('//button[text()="Unfollow"]').click()

    # unfollow users - gets list of users
    # Go to each user and unfollow him
    def unfollow_users(self, user_list):
        for user in user_list:
            self.driver.get('{}/{}'.format(self.base_url, user))
            time.sleep(2)
            try:
                self.driver.find_element_by_xpath('//button[text()="Following"]').click()
                time.sleep(2)
            except Exception as e:
                print('unfollow users: ', e)
            self.driver.find_element_by_xpath('/html/body/div[4]/div/div/div[3]/button[1]').click()

    def _nav_user(self, user):
        self.driver.get('{}/{}/'.format(self.base_url, user))