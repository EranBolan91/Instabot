from datetime import datetime


class Website:
    def __init__(self, website_link):
        self.website = website_link
        self.modify = datetime.now().strftime("%d/%m/%Y %H:%M")