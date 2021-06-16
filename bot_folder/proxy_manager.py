from database import db

MAX_USERS_IN_ONE_PROXY = 5


class ProxyManager:
    def __init__(self):
        self.__proxies = {}
        for username in db.Database().get_proxies_usernames():
            self.__proxies[username] = []

    def add_user(self, username):
        for username in db.Database().get_proxies_usernames():
            if username not in self.__proxies:
                self.__proxies[username] = []

        for proxy in self.__proxies:
            if len(self.__proxies[proxy]) < MAX_USERS_IN_ONE_PROXY:
                self.__proxies[proxy].append(username)
                return proxy

        raise Exception("not enough proxy")

    def remove_user(self, username):
        for proxy in self.__proxies:
            if username in self.__proxies[proxy]:
                self.__proxies[proxy].remove(username)
                return
