from tkinter import *
from tkinter import ttk, messagebox
import tkinter.font as tkfont
from bot_folder.follow_followers.follow_followers_bot import FollowFollowersBot
from database import db
import threading


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
        self.num_following = IntVar()
        self.check_box_distribution_list = IntVar()
        self.distribution_menu_var = StringVar()
        self.groups_list = []

        self.check_box_distribution_list.set(0)
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
        ttk.Button(self, text="START FOLLOW", command=self._search_following).grid(column=0, row=10, pady=15)

        # middle area - number of users to follow and distribution list
        ttk.Label(self, text='Enter the number of people to follow', font=self.titleFont).grid(column=0, columnspan=2, row=8, pady=10)
        self.following_input = ttk.Entry(self, textvariable=self.num_following, width=20)
        self.following_input.grid(column=0, columnspan=2, row=9, pady=10)
        self.distribution_check_box = ttk.Checkbutton(self, variable=self.check_box_distribution_list,
                                                      text='Save users in distribution list?')
        self.distribution_check_box.grid(column=0, columnspan=2, row=10, pady=20)
        # Groups distribution
        # If there are groups, it will display them. Else it will display message
        if len(self.groups_list) > 0:
            self.distribution_menu = ttk.OptionMenu(self, self.distribution_menu_var, self.groups_list[0],
                                                    *self.groups_list, state='DISABLED')
            self.distribution_menu.grid(column=0, columnspan=2, row=11)
        else:
            self.distribution_title = ttk.Label(self, text="Choose user to display distribution lists ",
                                                font=self.titleFont)
            self.distribution_title.grid(column=0, columnspan=2, row=11)

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
        ttk.Button(self, text="START FOLLOW", command=self._search_followers).grid(column=1, row=10, pady=15)

    # Getting the username from the menu option, look for it on the list and sets username and password
    def _set_username_password_following(self, value):
        for account in self.accounts:
            if value == account[3]:
                self.username_following.set(account[3])
                self.password_following.set(account[4])
                self.account_username = account[3]
                self.distribution_list = db.Database().get_distribution_lists_by_username(value)
                for group in self.distribution_list:
                    self.groups_list.append(group[1])
                if len(self.groups_list) > 0:
                    self.distribution_menu = ttk.OptionMenu(self, self.distribution_menu_var, self.groups_list[0],
                                                            *self.groups_list)
                    self.distribution_menu.grid(column=0, columnspan=2, row=10, pady=20)
                    self.distribution_title.grid_forget()
                else:
                    self.distribution_title.grid(column=0, columnspan=2, row=10, pady=20)
                    self.distribution_menu.grid_forget()

    # Getting the username from the menu option, look for it on the list and sets username and password
    def _set_username_password_followers(self, value):
        for account in self.accounts:
            if value == account[3]:
                self.username_followers.set(account[3])
                self.password_followers.set(account[4])
                self.account_username = account[3]
                self.distribution_list = db.Database().get_distribution_lists_by_username(value)
                for group in self.distribution_list:
                    self.groups_list.append(group[1])
                if len(self.groups_list) > 0:
                    self.distribution_menu = ttk.OptionMenu(self, self.distribution_menu_var, self.groups_list[0],
                                                            *self.groups_list)
                    self.distribution_menu.grid(column=0, columnspan=2, row=11, pady=20)
                    self.distribution_title.grid_forget()
                else:
                    self.distribution_title.grid(column=0, columnspan=2, row=11, pady=20)
                    self.distribution_menu.grid_forget()

    def _search_followers(self):
        user_url = self.user_url_followers.get()
        username = self.username_followers.get()
        password = self.password_followers.get()
        num_of_following = self.num_following.get()
        distribution = self.check_box_distribution_list.get()
        group_id = ""

        if distribution:
            group_name = self.distribution_menu_var.get()
            for group in self.distribution_list:
                if group_name == group[1]:
                    group_id = group[0]
                    print(group_id)

        valid = self._check_form(username, password, user_url, num_of_following)
        if valid:
            bot = FollowFollowersBot(username, password)
            t = threading.Thread(target=bot.follow_after_followers, args=(user_url, self.account_username, num_of_following, distribution, group_id))
            t.start()
        else:
            messagebox.showerror('Missing data', 'Please enter URL')

    def _search_following(self):
        user_url = self.user_url_following.get()
        username = self.username_following.get()
        password = self.password_following.get()
        num_of_following = self.num_following.get()
        distribution = self.check_box_distribution_list.get()
        group_id = ""

        if distribution:
            group_name = self.distribution_menu_var.get()
            for group in self.distribution_list:
                if group_name == group[1]:
                    group_id = group[0]
                    print(group_id)

        valid = self._check_form(username, password, user_url, num_of_following)
        if valid:
            bot = FollowFollowersBot(username, password)
            t = threading.Thread(target=bot.follow_after_following, args=(user_url, self.account_username, num_of_following, distribution, group_id))
            t.start()

    def _check_form(self, username, password, user_url, num_of_following):
        if username == '' or password == '':
            messagebox.showerror('Credentials', 'Please enter your username or password')
            return False

        if user_url == '':
            messagebox.showerror('Search data', 'Please enter a user url')
            return False

        if num_of_following <= 0:
            messagebox.showerror('Only numbers', 'Please enter only numbers to amount entry')
            return False

        else:
            return True