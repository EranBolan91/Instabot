from datetime import datetime


class Hashtag:
    def __init__(self, account, hashtag, num_posts, action_like, action_follow, action_comment,
                                                        distribution, group_name, comment, num_failed_posts, schedule):
        self.account = account
        self.hashtag = hashtag
        self.num_posts = num_posts
        self.num_failed_posts = num_failed_posts
        self.action_like = action_like
        self.action_follow = action_follow
        self.action_comment = action_comment
        self.distribution = distribution
        self.group_name = group_name
        self.comment = comment
        self.schedule = schedule
        self.date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")