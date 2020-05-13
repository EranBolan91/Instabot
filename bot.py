from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time, random
from database import db


class InstagramBot:

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.base_url = 'https://www.instagram.com'
        self.driver = webdriver.Chrome('chromedriver.exe')
        self.database = db.Database()

    def login(self):
        self.driver.get('{}/accounts/login/'.format(self.base_url))
        time.sleep(2)
        self.driver.find_element_by_name('username').send_keys(self.username)
        self.driver.find_element_by_name('password').send_keys(self.password + Keys.RETURN)
        time.sleep(3)
        try:
            self.driver.find_element_by_xpath("//button[contains(text(), 'Not Now')]").click()
        except:
            print("Didn't find 'not now'")

    def nav_user(self, user):
        self.driver.get('{}/{}/'.format(self.base_url, user))

    # search instagram page by the hash tag
    def search_hash_tag(self, hash_tag, amount, like, comment, follow, split_comment):
        amount_likes = self.database.get_data_from_settings()
        i = 1
        time.sleep(2)
        self.driver.get('{}/explore/tags/{}'.format(self.base_url, hash_tag))
        self.driver.find_element_by_class_name('_9AhH0').click()  # click the post
        while i <= int(amount):
            likes_from_insta = self._get_text()
            if int(likes_from_insta) > int(amount_likes[1]):
                if int(like) == 1:
                    self.like_post()
                if int(comment) == 1:
                    self.comment_post(split_comment)
                if int(follow) == 1:
                    self.follow_user()
                # click on the right arrow
                self.driver.find_element_by_class_name('coreSpriteRightPaginationArrow ').click()
                i += 1
            else:
                self.driver.find_element_by_class_name('coreSpriteRightPaginationArrow ').click()

    def follow_user(self):
        time.sleep(1)
        # TODO: not the correct way of doing it. I need to change it to check if im following the user or not
        self.driver.find_element_by_xpath(
            "/html/body/div[4]/div[2]/div/article/header/div[2]/div[1]/div[2]/button").click()
        is_schedule = self.database.get_data_from_settings()
        if is_schedule[3] == 1:
            # Get the username
            username = self.driver.find_element_by_xpath(
                '/html/body/div[4]/div[2]/div/article/header/div[2]/div[1]/div[1]/a').text
            # I must put it in a list because in db.py it gets only lists
            # Also it checks the size of the list. if it has more then 1 it will do other function
            users_list = [username]
            self.database.save_unfollow_users(users_list)

    def like_post(self):
        time.sleep(1)
        self.driver.find_element_by_class_name('fr66n').click()  # click the 'like' button

    def like_photos(self, amount):
        self.driver.find_element_by_class_name('_9AhH0').click()  # click the post
        i = 1
        while i <= int(amount):
            time.sleep(1)
            self.driver.find_element_by_class_name('fr66n').click()  # click the 'like' button
            self.driver.find_element_by_class_name(
                'coreSpriteRightPaginationArrow ').click()  # click on the right arrow
            i += 1

    # comment on a post
    def comment_post(self, split_comment):
        # returning random comment from a list of comments
        comment = random.choice(split_comment)
        time.sleep(3)
        # first need to click on the Entry ('add comment...')
        self.driver.find_element_by_class_name('Ypffh').click()
        # Then enter the comment and click post
        self.driver.find_element_by_class_name('Ypffh').send_keys(comment + Keys.RETURN)

    def get_unfollowers(self):
        time.sleep(2)
        self.driver.find_element_by_xpath("//a[contains(@href,'/{}/')]".format(self.username)) \
            .click()
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

    # search for location posts by the URL that the user provides
    def search_location_by_url(self, url, amount, like, follow, comment, split_comment):
        i = 1
        time.sleep(2)
        self.driver.get(url)  # open web browser by the URL
        self.driver.find_element_by_class_name('_9AhH0').click()  # click the post
        while i <= int(amount):
            if int(like) == 1:
                self.like_post()
            if int(comment) == 1:
                self.comment_post(split_comment)
            if int(follow) == 1:
                self.follow_user()
            self.driver.find_element_by_class_name(
                'coreSpriteRightPaginationArrow ').click()  # click on the right arrow
            i += 1

    # search for location posts by the location name that the user provides
    def search_location_by_name(self, location_name, amount, like, follow, comment, split_comment):
        i = 1
        self._search_entry(location_name)
        time.sleep(2)
        self.driver.find_element_by_class_name('_9AhH0').click()  # click the post
        while i <= int(amount):
            if int(like) == 1:
                self.like_post()
            if int(comment) == 1:
                self.comment_post(split_comment)
            if int(follow) == 1:
                self.follow_user()
            self.driver.find_element_by_class_name(
                'coreSpriteRightPaginationArrow ').click()  # click on the right arrow
            i += 1

    def _search_entry(self, name):
        time.sleep(1)
        self.driver.find_element_by_xpath('/html/body/div[1]/section/nav/div[2]/div/div/div[2]/input').click()
        self.driver.find_element_by_xpath('/html/body/div[1]/section/nav/div[2]/div/div/div[2]/input') \
            .send_keys(name + Keys.RETURN)

    def follow_after_followers(self, user_url):
        time.sleep(2)
        self.driver.get(user_url)
        time.sleep(2)
        # Open the followers page
        self.driver.find_element_by_xpath("//a[contains(@href,'/followers')]") \
            .click()
        try:
            time.sleep(2)
            # sometimes when you scroll to fast, it display to you the suggestions
            sugs = self.driver.find_element_by_xpath('//h4[contains(text(), Suggestions)]')
            self.driver.execute_script('arguments[0].scrollIntoView()', sugs)
        except:
            print('error')
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
            if i == 5:
                break

    def follow_after_following(self, user_url):
        time.sleep(2)
        self.driver.get(user_url)
        time.sleep(3)
        # Open the followers page
        self.driver.find_element_by_xpath("//a[contains(@href,'/following')]") \
            .click()
        try:
            time.sleep(2)
            # sometimes when you scroll to fast, it display to you the suggestions
            sugs = self.driver.find_element_by_xpath('//h4[contains(text(), Suggestions)]')
            self.driver.execute_script('arguments[0].scrollIntoView()', sugs)
        except:
            print('error')
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
            if i == 3:
                break

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
        except:
            print('error')
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
            # when user is private and you unfollow him, it pops up a message if you sure you want to unfollow
            # this class name is of the popup message and here i check if it exists
            # if it is then click on the button "unfollow"
            popup_unfollow = self.driver.find_element_by_class_name('mt3GC')
            if popup_unfollow:
                self.driver.find_element_by_xpath('/html/body/div[5]/div/div/div[3]/button[1]').click()
                # can also use this self.driver.find_element_by_xpath('//button[text()="Unfollow"]').click()

    def _get_text(self):
        time.sleep(1.9)
        try:
            text = self.driver.find_element_by_xpath(
                '/html/body/div[4]/div[2]/div/article/div[2]/section[2]/div/div/button/span').text
            if text != '':
                # these 3 lines, delete all ',' from the string
                num = text.split(',')
                new_num = ''.join(num)
            else:
                new_num = 0
        except:
            new_num = 0
        return new_num

    # unfollow users - gets list of users
    # Go to each user and unfollow him
    def unfollow_users(self, user_list):
        for user in user_list:
            self.driver.get('{}/{}'.format(self.base_url, user))
            time.sleep(2)
            self.driver.find_element_by_xpath('//button[text()="Following"]').click()
            time.sleep(2)
            self.driver.find_element_by_xpath('/html/body/div[4]/div/div/div[3]/button[1]').click()


if __name__ == '__main__':
    pass
