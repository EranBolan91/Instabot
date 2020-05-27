from tkinter import *
from tkinter import ttk, messagebox
import tkinter.font as tkfont
from bot_folder.follow_followers.follow_followers_bot import FollowFollowersBot
from database import db


class TabFollowFollowers(ttk.Frame):
    def __init__(self, window):
        super().__init__(window)
        self.user_url_followers = StringVar()
        self.user_url_following = StringVar()
        self.menu_followers = StringVar()
        self.menu_following = StringVar()
        self.username_following = StringVar()
        self.password_following = StringVar()
        self.username_followers = StringVar()
        self.password_followers = StringVar()

        self.accounts = db.Database().get_accounts()
        user_name_list = []
        for account in self.accounts:
            user_name_list.append(account[3])

        self.headerFont = tkfont.Font(family="Helvetica", size=12, weight='bold')
        self.titleFont = tkfont.Font(family="Helvetica", size=9)
        self.bold = tkfont.Font(weight='bold', size=10)

        # Left side Form
        ttk.Label(self, text='Follow after users that user following them', font=self.headerFont)\
                                                    .grid(column=0, row=0, padx=10, pady=10)
        ttk.Label(self, text='Enter the user URL', font=self.titleFont).grid(column=0, row=1, padx=10, pady=10)
        ttk.Entry(self, textvariable=self.user_url_following, width=50).grid(column=0, row=2)
        ttk.Label(self, text='Choose user', font=self.titleFont).grid(column=0, row=3, padx=10, pady=10)
        if len(user_name_list) > 0:
            ttk.OptionMenu(self, self.menu_following, user_name_list[0], *user_name_list, command=self._set_username_password_following)\
                                                                                                .grid(column=0, row=4)
        else:
            ttk.Label(self, text='No Users, go to Accounts', font=self.titleFont).grid(column=0, row=4, padx=10,
                                                                                       pady=10)
        # username and password form
        ttk.Label(self, text='Please enter username and password', font=self.titleFont) \
            .grid(column=0, row=5, padx=10, pady=10)
        ttk.Label(self, text='username:', font=self.bold).grid(column=0, row=6, padx=10, pady=10, sticky='w')
        ttk.Entry(self, textvariable=self.username_following, show='*', width=25).grid(column=0, row=6)
        ttk.Label(self, text='password:', font=self.bold).grid(column=0, row=7, padx=10, pady=10, sticky='w')
        ttk.Entry(self, textvariable=self.password_following, show='*', width=25).grid(column=0, row=7)

        ttk.Button(self, text="START FOLLOW", command=self._search_following).grid(column=0, row=8, pady=15)

        # Right side Form
        ttk.Label(self, text='Follow after users that following user', font=self.headerFont)\
                                                    .grid(column=1, row=0, padx=100, pady=10)
        ttk.Label(self, text='Enter the user URL', font=self.titleFont).grid(column=1, row=1, padx=10, pady=10)
        ttk.Entry(self, textvariable=self.user_url_followers, width=50).grid(column=1, row=2)
        ttk.Label(self, text='Choose user', font=self.titleFont).grid(column=1, row=3, padx=10, pady=10)
        if len(user_name_list) > 0:
            ttk.OptionMenu(self, self.menu_followers, user_name_list[0], *user_name_list, command=self._set_username_password_followers)\
                                                                                                .grid(column=1, row=4)
        else:
            ttk.Label(self, text='No Users, go to Accounts', font=self.titleFont).grid(column=1, row=4, padx=10,
                                                                                       pady=10)
        # username and password form
        ttk.Label(self, text='Please enter username and password', font=self.titleFont) \
            .grid(column=1, row=5, padx=10, pady=10)
        ttk.Label(self, text='username:', font=self.bold).grid(column=1, row=6, padx=10, pady=10, sticky='w')
        ttk.Entry(self, textvariable=self.username_followers, show='*', width=25).grid(column=1, row=6)
        ttk.Label(self, text='password:', font=self.bold).grid(column=1, row=7, padx=10, pady=10, sticky='w')
        ttk.Entry(self, textvariable=self.password_followers, show='*', width=25).grid(column=1, row=7)

        ttk.Button(self, text="START FOLLOW", command=self._search_followers).grid(column=1, row=8, pady=15)

    # Getting the username from the menu option, look for it on the list and sets username and password
    def _set_username_password_following(self, value):
        for account in self.accounts:
            if value == account[3]:
                self.username_following.set(account[3])
                self.password_following.set(account[4])

    # Getting the username from the menu option, look for it on the list and sets username and password
    def _set_username_password_followers(self, value):
        for account in self.accounts:
            if value == account[3]:
                self.username_followers.set(account[3])
                self.password_followers.set(account[4])

    def _search_followers(self):
        user_url = self.user_url_followers.get()
        username = self.username_followers.get()
        password = self.password_followers.get()
        if user_url:
            bot = FollowFollowersBot(username, password)
            bot.follow_after_followers(user_url)
        else:
            messagebox.showerror('Missing data', 'Please enter URL')

    def _search_following(self):
        user_url = self.user_url_following.get()
        username = self.username_following.get()
        password = self.password_following.get()
        if user_url:
            bot = FollowFollowersBot(username, password)
            bot.follow_after_following(user_url)
        else:
            messagebox.showerror('Missing data', 'Please enter URL')