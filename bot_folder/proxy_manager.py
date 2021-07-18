from database import db
import time

MAX_USERS_IN_ONE_PROXY = 3


class ProxyManager:
    def __init__(self):
        self.__proxies = {}
        for username in db.Database().get_proxies_usernames():
            self.__proxies[username] = [], Mutex()

    def add_user(self, username):
        for proxy_username in db.Database().get_proxies_usernames():
            if proxy_username not in self.__proxies:
                self.__proxies[proxy_username] = [], Mutex()

        for proxy in self.__proxies:
            if len(self.__proxies[proxy][0]) < MAX_USERS_IN_ONE_PROXY:
                self.__proxies[proxy][0].append(username)
                return proxy

        raise Exception("not enough proxy")

    def remove_user(self, username):
        for proxy in self.__proxies:
            if username in self.__proxies[proxy][0]:
                self.__proxies[proxy][0].remove(username)
                return

    def get_mutex(self, instegram_username):
        for proxy in self.__proxies:
            if instegram_username in self.__proxies[proxy][0]:
                return self.__proxies[proxy][1]


class Mutex(object):
    def __init__(self):
        self.__locker = False

    def lock(self):
        while True:
            time.sleep(30)
            if not self.__locker:
                break

        self.__locker = True

    def unlock(self):
        self.__locker = False
