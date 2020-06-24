from bot_folder import main_bot
from database.follow_followers.follow_followers import FollowFollowersDB
from models.follow_followers import FollowFollowers
import time


class FollowFollowersBot(main_bot.InstagramBot):
    def follow_after_followers(self, user_url, account_username, num_of_following, to_distribution, group_name, group_id, is_schedule):
        self._login()
        time.sleep(2)
        self.driver.get(user_url)
        time.sleep(2)
        # Open the followers page
        self.driver.find_element_by_xpath("//a[contains(@href,'/followers')]").click()
        try:
            time.sleep(2)
            # sometimes when you scroll to fast, it display to you the suggestions
            sugs = self.driver.find_element_by_xpath('//h4[contains(text(), Suggestions)]')
            self.driver.execute_script('arguments[0].scrollIntoView()', sugs)
        except Exception as e:
            print('follow_after_followers: ', e)
        time.sleep(3)
        # getting the box element
        scroll_box = self.driver.find_element_by_xpath("/ html / body / div[4] / div / div / div[2]")
        #/ html / body / div[4] / div / div
        #/ html / body / div[4] / div / div / div[2]
        last_height, height = 0, 1
        # this while scrolls all over the followers
        while last_height != height:
            last_height = height
            time.sleep(2)
            height = self.driver.execute_script("""
                       arguments[0].scrollTo(0, arguments[0].scrollHeight); 
                       return arguments[0].scrollHeight;
                       """, scroll_box)
        # Gets all the users name by the class name
        users_name = self.driver.find_elements_by_class_name('_0imsa')
        # After it scrolled all down the scroll box, this line of code, gets all the buttons into a list
        buttons = scroll_box.find_elements_by_tag_name('button')
        i = 0
        # This for runs all over the buttons list and click 'follow'
        for button in buttons:
            time.sleep(1)
            if button.text == 'Follow':
                button.click()
                self.database.save_unfollow_users(users_name[i].text, account_username)
                if to_distribution:
                    self.database.add_username_to_distribution_group(users_name[i].text, group_id)
                i += 1
                try:
                    # when user is private and you unfollow him, it pops up a message if you sure you want to unfollow
                    # this class name is of the popup message and here i check if it exists
                    # if it is then click on the button "unfollow"
                    self._popup_unfollow()
                except Exception as e:
                    print('follow after followers: ', e)
            if i == num_of_following:
                break
        # I did -1 because the for loop ends by giving +1 to i (one more then it needs)
        failed_follow_num = int(num_of_following) - (i - 1)
        # TODO: why group_name gives null in the database
        self._prepare_data_for_db(user_url, num_of_following, to_distribution, group_name, failed_follow_num, is_schedule)

    def follow_after_following(self, user_url, account_username, num_of_following, to_distribution, group_name, group_id, is_schedule):
        self._login()
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
        except Exception as e:
            print('follow after following: here ', e)
        time.sleep(3)
        # getting the box element
        scroll_box = self.driver.find_element_by_xpath("/ html / body / div[4] / div / div / div[2]")
        last_height, height = 0, 1
        # this while scrolls all over the followers
        while last_height != height:
            last_height = height
            time.sleep(2)
            height = self.driver.execute_script("""
                          arguments[0].scrollTo(0, arguments[0].scrollHeight); 
                          return arguments[0].scrollHeight;
                          """, scroll_box)
        # Gets all the users name by the class name
        users_name = self.driver.find_elements_by_class_name('_0imsa')
        # After it scrolled all down the scroll box, this line of code, gets all the buttons into a list
        buttons = scroll_box.find_elements_by_tag_name('button')
        i = 0
        # This for runs all over the buttons list and click 'follow'
        for button in buttons:
            time.sleep(1)
            if button.text == 'Follow':
                button.click()
                self.database.save_unfollow_users(users_name[i].text, account_username)
                if to_distribution:
                    self.database.add_username_to_distribution_group(users_name[i].text, group_id)
                i += 1
                # when user is private and you unfollow him, it pops up a message if you sure you want to unfollow
                # this class name is of the popup message and here i check if it exists
                # if it is then click on the button "unfollow"
                try:
                    self._popup_unfollow()
                except Exception as e:
                    print('follow after following: ', e)

            if i == num_of_following:
                break
        # I did -1 because the for loop ends by giving +1 to i (one more then it needs)
        failed_follow_num = int(num_of_following) - (i - 1)
        self._prepare_data_for_db(user_url, num_of_following, to_distribution, group_name, failed_follow_num, is_schedule)

    # Saving Hash-tag data to display in the statistics
    def _prepare_data_for_db(self, user_url, num_of_following, to_distribution, group_name, failed_follow_num, is_schedule):
        follow_followers = FollowFollowers(self.username, user_url, num_of_following, failed_follow_num, to_distribution, group_name, is_schedule)
        FollowFollowersDB().save_in_db(follow_followers)