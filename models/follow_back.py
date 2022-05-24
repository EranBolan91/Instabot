from datetime import datetime


class FollowBack:
    def __init__(self, used_id, account, follow_back, date):
        self.user_id = used_id
        self.account = account
        self.follow_back = follow_back
        self.date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")