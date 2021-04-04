from datetime import datetime


class AccountActions:
    def __init__(self, user_id, username, action, amount, amount_success):
        self.user_id = user_id
        self.username = username
        self.action = action
        self.amount = amount
        self.amount_success = amount_success
        self.date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
