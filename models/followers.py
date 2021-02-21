from datetime import datetime


class Followers:
    def __init__(self, user_id, account, follow_back):
        self.account = account
        self.user_id = user_id
        self.follow_back = follow_back
        self.date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")