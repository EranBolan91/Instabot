from datetime import datetime


class FollowFollowers:
    def __init__(self, account, url, num_follow, num_failed_follow, distribution, group_name, schedule):
        self.account = account
        self.url = url
        self.num_follow = num_follow
        self.num_failed_follow = num_failed_follow
        self.distribution = distribution
        self.group_name = group_name
        self.schedule = schedule
        self.date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")