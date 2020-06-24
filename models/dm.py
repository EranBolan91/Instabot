from datetime import datetime


class DM:
    def __init__(self, account, message, group, num_members, num_failed_members, schedule):
        self.account = account
        self.message = message
        self.group = group
        self.num_members = num_members
        self.num_failed_members = num_failed_members
        self.schedule = schedule
        self.date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")