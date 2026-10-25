from bot_folder import main_bot
from database.follow_followers.follow_followers import FollowFollowersDB
from models.follow_followers import FollowFollowers
import time
from utils.utils import Utils as utils
from utils.instagram_selectors import S
import datetime as dt


class FollowFollowersBot(main_bot.InstagramBot):
    def follow_after_followers(self, user_url, account_username, num_of_following, to_distribution, group_name, group_id, is_schedule, num_skip):
        settings_data_from_db = FollowFollowersDB().get_data_from_settings()
        if not self._login():
            return
        time.sleep(1.5)
        self.driver.get(user_url)
        time.sleep(1.5)
        # count how many actual users i followed
        follow_count = 0
        try:
            # Open the followers list and get its scrolling part
            S.click(self.driver, "profile.followers_counter")
            time.sleep(2)
            scroll_box = S.get(self.driver, "dialog.scroll_area")
            # usernames already looked at: the list keeps its earlier rows while it scrolls
            done = set()
            loops = 0
            empty_scrolls = 0
            blocked = False
            # this while scrolls all over the followers
            while follow_count < num_of_following and not blocked:
                time.sleep(1)
                S.scroll_to_bottom(self.driver, scroll_box)
                time.sleep(1)
                new_rows = [(username, button) for username, button in S.dialog_rows(self.driver)
                            if username not in done]
                if not new_rows:
                    empty_scrolls += 1
                    if empty_scrolls == 3:
                        print('Follow followers: reached the end of the list')
                        break
                    continue
                empty_scrolls = 0
                for username, button in new_rows:
                    done.add(username)
                    # skip the account itself, and rows without a Follow button (already following)
                    if username == self.username or button is None or button.text != 'Follow':
                        continue
                    if loops % utils.TIME_SLEEP == 0:
                        print('Username:', account_username, 'Time start:',
                              dt.datetime.now().strftime('%H:%M:%S'), ' Sleep time:',
                              loops * utils.TIME_SLEEP, 'seconds')
                        time.sleep(loops * utils.TIME_SLEEP)
                    followers_num, has_image_profile, _posts = self._get_followers_number(username)
                    if has_image_profile == -1 and int(followers_num) >= int(settings_data_from_db[2]):
                        button.click()
                        follow_count += 1
                        if self._blocked_action_popup():
                            self._send_email(self.username, follow_count, dt.datetime.now().strftime('%H:%M:%S'),
                                             'Follow Followers')
                            self.global_block_message(self.username, "Follow followers")
                            blocked = True
                            break
                        print('Follow count {}/{}'.format(num_of_following, follow_count), 'Username: ',
                              account_username)
                        self.database.save_unfollow_users(username, account_username)
                        if to_distribution:
                            self.database.add_username_to_distribution_group(username, group_id)
                    loops += 1
                    if int(loops * utils.TIME_SLEEP) == 500:
                        loops = 1
                        print('reset loops')
                    if follow_count == num_of_following:
                        break
        except Exception as e:
            print('follow after followers ', e)
            self._screen_shot(self.username)
            self._send_email(self.username, follow_count, dt.datetime.now().strftime('%H:%M:%S'),
                             'Follow followers')
        finally:
            self.driver.delete_all_cookies()
            failed_follow_num = int(num_of_following) - follow_count
            self._prepare_data_for_db(user_url, num_of_following, to_distribution, group_name, failed_follow_num,
                                      is_schedule, num_skip)
            self.driver.close()

    def follow_after_following(self, user_url, account_username, num_of_following, to_distribution, group_name, group_id, is_schedule, num_skip):
        settings_data_from_db = FollowFollowersDB().get_data_from_settings()
        if not self._login():
            return
        time.sleep(2)
        self.driver.get(user_url)
        time.sleep(2)
        # count how many actual users i followed
        follow_count = 0
        # for looping
        loops = 0
        try:
            # Open the following list
            S.click(self.driver, "profile.following_counter")
            time.sleep(1.5)
            scroll_box = S.get(self.driver, "dialog.scroll_area")
            last_height, height = 0, 1
            # this while scrolls all over the list first
            while last_height != height:
                last_height = height
                time.sleep(0.7)
                height = S.scroll_to_bottom(self.driver, scroll_box)
            # then goes over its rows, after skipping num_skip of them
            for username, button in S.dialog_rows(self.driver)[num_skip:]:
                if username == self.username or button is None or button.text != 'Follow':
                    continue
                if loops % utils.TIME_SLEEP == 0:
                    print('Username:', account_username, 'Time start: ', dt.datetime.now().strftime('%H:%M:%S'), ' Sleep time: ',
                          loops * utils.TIME_SLEEP, 'seconds')
                    time.sleep(loops * utils.TIME_SLEEP)
                followers_num, has_image_profile, _posts = self._get_followers_number(username)
                if has_image_profile == -1 and int(followers_num) >= int(settings_data_from_db[2]):
                    button.click()
                    follow_count += 1
                    if self._blocked_action_popup():
                        self._send_email(self.username, follow_count, dt.datetime.now().strftime('%H:%M:%S'),
                                         'Follow Followers')
                        self.global_block_message(self.username, "Follow followers")
                        break
                    print('Follow count {}/{}'.format(num_of_following, follow_count), 'Username: ',
                          account_username)
                    self.database.save_unfollow_users(username, account_username)
                    if to_distribution:
                        self.database.add_username_to_distribution_group(username, group_id)
                loops += 1
                if int(loops * utils.TIME_SLEEP) == 500:
                    loops = 1
                    print('reset to loops')
                if follow_count == num_of_following:
                    break
        except Exception as e:
            print('follow after following: ', e)
        finally:
            self.driver.delete_all_cookies()
            failed_follow_num = int(num_of_following) - follow_count
            self._prepare_data_for_db(user_url, num_of_following, to_distribution, group_name, failed_follow_num,
                                      is_schedule, num_skip)
            self.driver.close()

    # Saving Hash-tag data to display in the statistics
    def _prepare_data_for_db(self, user_url, num_of_following, to_distribution, group_name, failed_follow_num, is_schedule, num_skip):
        follow_followers = FollowFollowers(self.username, user_url, num_of_following, failed_follow_num, to_distribution, group_name, is_schedule, num_skip)
        FollowFollowersDB().save_in_db(follow_followers)
