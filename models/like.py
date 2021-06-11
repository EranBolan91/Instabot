from datetime import datetime


class Like:
    def __init__(self, account, url, hashtag, num_likes):
        self.account = account
        self.url = url
        self.hashtag = hashtag
        self.num_likes = num_likes
        self.date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
