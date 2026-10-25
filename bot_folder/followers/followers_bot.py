from bot_folder import main_bot
from database.followers.followers import FollowersDB
from database import db
from models.followers import Followers
from utils.utils import Utils as utils
from utils.instagram_selectors import S
import datetime as dt
import time


class FollowersBot(main_bot.InstagramBot):
    def get_unfollowers(self):
        if not self._login():
            return
        time.sleep(2)
        self._nav_user(self.username)
        time.sleep(2)
        S.click(self.driver, "profile.following_counter")
        following = self._get_names()
        S.click(self.driver, "profile.followers_counter")
        followers = self._get_names()
        followers_amount, no_use_data, no_use_posts = self._get_followers_number(self.username)
        if int(followers_amount) <= int((len(followers)+10)):
            not_following_back = [user for user in following if user not in followers]
            print(not_following_back)
            print('Not following back: ', len(not_following_back))
            return not_following_back
        else:
            print('Something fucked up with the followers,'
                  'it counted {} followers and the current user has {} followers'.format(len(followers), followers_amount))
            return False

    # usernames in the open list, after scrolling it to the end; closes the list
    def _get_names(self):
        time.sleep(2)
        scroll_box = S.get(self.driver, "dialog.scroll_area")
        last_height, height = 0, 1
        while last_height != height:
            last_height = height
            time.sleep(2)
            height = S.scroll_to_bottom(self.driver, scroll_box)
        names = [username for username, _button in S.dialog_rows(self.driver)]
        # close button
        S.click(self.driver, "dialog.close_button")
        time.sleep(1)
        return names

    # This unfollow, goes to the current account, click on the 'Following'
    # and go over all the users and then unfollow them one by one
    def unfollow_all_users(self, limit_unfollowers):
        if not self._login():
            return
        time.sleep(2)
        self._nav_user(self.username)
        time.sleep(2)
        is_action_blocked = False
        unfollow_click = 0
        i = 0
        try:
            # Open the following list
            S.click(self.driver, "profile.following_counter")
            time.sleep(2)
            scroll_box = S.get(self.driver, "dialog.scroll_area")
            done = set()
            empty_scrolls = 0
            # this while scrolls all over the list
            while unfollow_click < limit_unfollowers and not is_action_blocked:
                time.sleep(2)
                S.scroll_to_bottom(self.driver, scroll_box)
                time.sleep(1)
                new_rows = [(username, button) for username, button in S.dialog_rows(self.driver)
                            if username not in done]
                if not new_rows:
                    empty_scrolls += 1
                    if empty_scrolls == 3:
                        print("Unfollow everyone: reached the end of the list")
                        break
                    continue
                empty_scrolls = 0
                for username, button in new_rows:
                    done.add(username)
                    if unfollow_click >= limit_unfollowers:
                        break
                    if button is None or not button.text.startswith('Following'):
                        continue
                    if int(i * utils.TIME_SLEEP) == 500:
                        i = 1
                        print('reset to i')
                    if i % utils.TIME_SLEEP == 0:
                        print('Account', self.username, 'Time start: ', dt.datetime.now().strftime('%H:%M:%S'), ' Sleep time: ', i * utils.TIME_SLEEP, 'seconds')
                        time.sleep(i * utils.TIME_SLEEP)
                    try:
                        button.click()
                        i += 1
                        unfollow_click += 1
                    except Exception as e:
                        print('unfollow all users: ', e)
                        continue
                    # Instagram asks "Unfollow @user?": confirm it
                    self._popup_unfollow()
                    is_action_blocked = self._blocked_action_popup()
                    if is_action_blocked:
                        self._send_email(self.username, unfollow_click, dt.datetime.now().strftime('%H:%M:%S'), 'Unfollow all')
                        self.global_block_message(self.username, "Unfollow everyone")
                        break
                print("Unfollow everyone: removed {}/{} account: {}".format(limit_unfollowers, unfollow_click, self.username))
        except Exception as e:
            print("Error in the end: ", e)
        self.driver.close()

    # unfollow users - gets list of users
    # Go to each user and unfollow him
    def unfollow_users(self, user_list, to_remove_from_db, account_id, to_login, to_reverse, limit_unfollow_list, remove_not_found_users):
        i = 1
        remove_clicks = 0
        follow_back = 0
        if to_login:
            if not self._login():
                return
        time.sleep(1.5)
        if to_reverse:
            user_list.reverse()
        for user in user_list:
            self._nav_user(user)
            if i % utils.ROUNDS == 0:
                print('Account', self.username, 'Time start: ', dt.datetime.now().strftime('%H:%M:%S'), ' Sleep time: ', i * utils.TIME_SLEEP, 'seconds')
                time.sleep(i*utils.TIME_SLEEP)
            unfollowed = False
            try:
                if S.exists(self.driver, "profile.following_button", timeout=4):
                    # "Following" opens a menu; "Unfollow" in it unfollows
                    S.click(self.driver, "profile.following_button")
                    S.click(self.driver, "profile.unfollow_confirm")
                    unfollowed = True
                elif S.exists(self.driver, "profile.requested_button"):
                    # a private account we asked to follow: cancel the request
                    S.click(self.driver, "profile.requested_button")
                    self._popup_unfollow()
                    unfollowed = True
            except Exception as e:
                print('unfollow users: ', e)
            if unfollowed:
                i += 1
                remove_clicks += 1
                if not to_remove_from_db:
                    self._check_if_follow_back()

            if self._blocked_action_popup():
                self._send_email(self.username, remove_clicks, dt.datetime.now().strftime('%H:%M:%S'), 'Followers')
                self.driver.close()
                self.global_block_message(self.username, "Followers")
                break
            # count how many users follow back
            if S.exists(self.driver, "profile.follow_back_button", timeout=4):
                follow_back += 1

            # Remove username from unfollow list
            # Only when the button really turned into Follow / Follow Back: if the bot clicked
            # 'unfollow' and it didn't work, the username stays in the database
            if to_remove_from_db and S.exists(self.driver, "profile.follow_button", timeout=4):
                print(user, 'Removed from db of', self.username)
                db.Database().remove_username_from_unfollow_list(user, account_id)
            # if username is not found, then delete it from list of unfollow (this is optionally)
            if remove_not_found_users:
                if self._user_not_found_broken_link():
                    db.Database().remove_username_from_unfollow_list(user, account_id)
                    remove_clicks += 1
            print('{} Removed from {} account'.format(remove_clicks, self.username))
            if int(i * utils.TIME_SLEEP) == 500:
                i = 1
                print('reset to i')
            if remove_clicks == limit_unfollow_list:
                break
        # save the amount of followers back
        followers_obj = Followers(account_id, self.username, follow_back)
        FollowersDB().save_in_db(followers_obj)
        self.driver.close()

    # unfollow one user
    def unfollow_user(self, username, account_id):
        try:
            self._unfollow_user(username, account_id)
        except Exception as e:
            print('unfollow user: ', e)
        finally:
            self.driver.close()

    # Getting list of the account followers and compare it with the list of the followers of the account
    # unfollow every user that the account following him and the user not following back
    def unfollow_users_who_not_return_follow(self, unfollowers_list, account_id, to_reverse):
        if not self._login():
            return
        time.sleep(2)
        self._nav_user(self.username)
        time.sleep(2)
        S.click(self.driver, "profile.followers_counter")
        followers = self._get_names()
        not_following_back = [user for user in unfollowers_list if user not in followers]
        time.sleep(1.3)
        self.driver.close()
        return not_following_back

    # Saving Hash-tag data to display in the statistics
    # def _prepare_data_for_db(self, hash_tag, amount, like, comment, follow,
    #                          split_comment, to_distribution, group_name, failed_posts_num, time_schedule):
    #
    #     join_comment = ','.join(split_comment)
    #     hashtag = Hashtag(self.username, hash_tag, amount, like, follow, comment,
    #                       to_distribution, group_name, join_comment, failed_posts_num, time_schedule)
    #     HashtagDB().save_in_db(hashtag)
    #     account_id = CombinationDM().get_user_id(self.username)
    #     account_action = AccountActions(account_id, self.username, "HashTag", amount,
    #                                     amount - failed_posts_num)
    #     FollowersDB().save_data_account_action(account_action)