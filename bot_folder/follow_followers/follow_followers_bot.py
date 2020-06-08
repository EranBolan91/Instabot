from bot_folder import main_bot
import time


class FollowFollowersBot(main_bot.InstagramBot):
    def follow_after_followers(self, user_url, account_username, num_of_following):
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
        scroll_box = self.driver.find_element_by_xpath("/html/body/div[4]/div/div[2]")
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
        print(len(users_name))
        # After it scrolled all down the scroll box, this line of code, gets all the buttons into a list
        buttons = scroll_box.find_elements_by_tag_name('button')
        i = 0
        # This for runs all over the buttons list and click 'follow'
        for button in buttons:
            time.sleep(1)
            if button.text == 'Follow':
                button.click()
                self.database.save_unfollow_users(users_name[i].text, account_username)
                i += 1
                try:
                    # TODO: popup_unfollow should be a method in "main_bot"
                    # when user is private and you unfollow him, it pops up a message if you sure you want to unfollow
                    # this class name is of the popup message and here i check if it exists
                    # if it is then click on the button "unfollow"
                    self._popup_unfollow()
                    #popup_unfollow = self.driver.find_element_by_class_name('mt3GC')
                    #if popup_unfollow:
                         #self.driver.find_element_by_xpath('/html/body/div[5]/div/div/div[3]/button[1]').click()
                         # can also use this self.driver.find_element_by_xpath('//button[text()="Unfollow"]').click()
                except Exception as e:
                    print('follow after followers: ', e)
            if i == num_of_following:
                break

    def follow_after_following(self, user_url, account_username, num_of_following):
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
            print('follow after following: ', e)
        time.sleep(3)
        # getting the box element
        scroll_box = self.driver.find_element_by_xpath("/html/body/div[4]/div/div[2]")
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
                i += 1

                # TODO: popup_unfollow should be a method in "main_bot"
                # when user is private and you unfollow him, it pops up a message if you sure you want to unfollow
                # this class name is of the popup message and here i check if it exists
                # if it is then click on the button "unfollow"
                try:
                    self._popup_unfollow()
                    # popup_unfollow = self.driver.find_element_by_class_name('mt3GC')
                    # if popup_unfollow:
                    #     self.driver.find_element_by_xpath('/html/body/div[5]/div/div/div[3]/button[1]').click()
                        # can also use this self.driver.find_element_by_xpath('//button[text()="Unfollow"]').click()
                except Exception as e:
                    print('follow after following: ', e)

            if i == num_of_following:
                break
