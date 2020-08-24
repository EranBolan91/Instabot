from bot_folder import main_bot
from database.follow_followers.follow_followers import FollowFollowersDB
from models.follow_followers import FollowFollowers
import time
from utils.utils import Utils as utils
import datetime as dt


class FollowFollowersBot(main_bot.InstagramBot):
    def follow_after_followers(self, user_url, account_username, num_of_following, to_distribution, group_name, group_id, is_schedule):
        settings_data_from_db = FollowFollowersDB().get_data_from_settings()
        self._login()
        time.sleep(1.5)
        self.driver.get(user_url)
        time.sleep(1.5)
        # Open the followers page
        self.driver.find_element_by_xpath("//a[contains(@href,'/followers')]").click()
        try:
            time.sleep(2)
            # sometimes when you scroll to fast, it display to you the suggestions
            sugs = self.driver.find_element_by_xpath('//h4[contains(text(), Suggestions)]')
            self.driver.execute_script('arguments[0].scrollIntoView()', sugs)
        except Exception as e:
            print('follow_after_followers: ', e)
        time.sleep(2.5)
        # getting the box element
        scroll_box = self.driver.find_element_by_xpath("/html/body/div[4]/div/div/div[2]")
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
        users_name_list = self.driver.find_elements_by_class_name('_0imsa')
        # After it scrolled all down the scroll box, this line of code, gets all the buttons into a list
        buttons = scroll_box.find_elements_by_tag_name('button')
        # i starts from 0 because the list of users_name, its the index
        i = 0
        # follow_count is for sub from the i in the end of the loop.
        # count how many clicks it did. how many actual users i followed
        follow_count = 0
        # reset the wait time after a specific time
        # This for runs all over the buttons list and click 'follow'
        # for looping
        loops = 0
        try:
            for button in buttons:
                username = users_name_list[i].text
                if loops % utils.TIME_SLEEP == 0:
                    print('Time start: ', dt.datetime.now(), ' Sleep time: ', loops * utils.TIME_SLEEP, 'seconds')
                    time.sleep(loops * utils.TIME_SLEEP)
                if button.text == 'Follow':
                    followers_num = self._get_followers_number(username)
                    if int(followers_num) >= int(settings_data_from_db[2]):
                        button.click()
                        follow_count += 1
                        self.database.save_unfollow_users(username, account_username)
                        if to_distribution:
                            self.database.add_username_to_distribution_group(username, group_id)
                    i += 1
                    loops += 1
                else:
                    i += 1
                    loops += 1
                if int(loops * utils.TIME_SLEEP) == 500:
                    loops = 1
                    print('reset loops')
                if follow_count == num_of_following:
                    break
        except Exception as e:
            print('follow after followers ', e)
        finally:
            self.driver.delete_all_cookies()
            # I did -1 because the for loop ends by giving +1 to i (one more then it needs)
            failed_follow_num = int(num_of_following) - follow_count
            self._prepare_data_for_db(user_url, num_of_following, to_distribution, group_name, failed_follow_num,
                                      is_schedule)
            self.driver.close()

    def follow_after_following(self, user_url, account_username, num_of_following, to_distribution, group_name, group_id, is_schedule):
        settings_data_from_db = FollowFollowersDB().get_data_from_settings()
        self._login()
        time.sleep(2)
        self.driver.get(user_url)
        time.sleep(2)
        # Open the followers page
        self.driver.find_element_by_xpath("//a[contains(@href,'/following')]") \
            .click()
        try:
            time.sleep(2)
            # sometimes when you scroll too fast, it display to you the suggestions
            sugs = self.driver.find_element_by_xpath('//h4[contains(text(), Suggestions)]')
            self.driver.execute_script('arguments[0].scrollIntoView()', sugs)
        except Exception as e:
            print('follow after following: here ', e)
        time.sleep(1.5)
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
        users_name_list = self.driver.find_elements_by_class_name('_0imsa')
        # After it scrolled all down the scroll box, this line of code, gets all the buttons into a list
        buttons = scroll_box.find_elements_by_tag_name('button')
        # i starts from 0 because the list of users_name, its the index
        i = 0
        # follow_count is for sub from the i in the end of the loop.
        # count how many clicks it did. how many actual users i followed
        follow_count = 0
        # for looping
        loops = 0
        try:
            # This for runs all over the buttons list and click 'follow'
            for button in buttons:
                username = users_name_list[i].text
                if loops % utils.TIME_SLEEP == 0:
                    print('Time start: ', dt.datetime.now(), ' Sleep time: ', loops * utils.TIME_SLEEP, 'seconds')
                    time.sleep(i * utils.TIME_SLEEP)
                if button.text == 'Follow':
                    followers_num = self._get_followers_number(username)
                    if int(followers_num) >= int(settings_data_from_db[2]):
                        button.click()
                        follow_count += 1
                        self.database.save_unfollow_users(username, account_username)
                        if to_distribution:
                            self.database.add_username_to_distribution_group(username, group_id)
                    loops += 1
                    i += 1
                else:
                    loops += 1
                    i += 1

                print('index: ', loops)
                if int(loops * utils.TIME_SLEEP) == 500:
                    loops = 1
                    print('reset to loops')

                if follow_count == num_of_following:
                    break
        except Exception as e:
            print('follow after following: ', e)
        finally:
            self.driver.delete_all_cookies()
            # I did -1 because the for loop ends by giving +1 to i (one more then it needs)
            failed_follow_num = int(num_of_following) - follow_count
            self._prepare_data_for_db(user_url, num_of_following, to_distribution, group_name, failed_follow_num,
                                      is_schedule)
            self.driver.close()

    # Saving Hash-tag data to display in the statistics
    def _prepare_data_for_db(self, user_url, num_of_following, to_distribution, group_name, failed_follow_num, is_schedule):
        follow_followers = FollowFollowers(self.username, user_url, num_of_following, failed_follow_num, to_distribution, group_name, is_schedule)
        FollowFollowersDB().save_in_db(follow_followers)