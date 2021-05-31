from datetime import datetime


class Combination:
    def __init__(self, account, url, hashtag, num_likes, num_failed_likes, num_followers,
                num_failed_followers, schedule, distribution, group_name, skip_users):
        self.account = account
        self.url = url
        self.hashtag = hashtag
        self.num_likes = num_likes
        self.num_failed_likes = num_failed_likes
        self.num_followers = num_followers
        self.num_failed_followers = num_failed_followers
        self.distribution = distribution
        self.group_name = group_name
        self.schedule = schedule
        self.skip_users = skip_users
        self.date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")