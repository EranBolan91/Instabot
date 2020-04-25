from tkinter import *
from tkinter import ttk, messagebox
import tkinter.font as tkfont
from bot import *
from database import db


class TabFollowers(ttk.Frame):
    def __init__(self, window):
        super().__init__(window)

        self.headerFont = tkfont.Font(family="Helvetica", size=12, weight='bold')
        self.titleFont = tkfont.Font(family="Helvetica", size=9)
        self.h3 = tkfont.Font(family="Helvetica", size=11, weight='bold')
        self.bold = tkfont.Font(weight='bold', size=10)
        self.results = tkfont.Font(size=11, weight='bold')
        self.username = StringVar()
        self.password = StringVar()
        self.menu = StringVar()
        self.amount_not_following = 0

        self.accounts = db.Database().get_accounts()
        user_name_list = []
        for account in self.accounts:
            user_name_list.append(account[2])

        ttk.Label(self, text='Check which users you follow don\'t follow you back', font=self.headerFont)\
                                                                        .grid(column=0, row=0, padx=10, pady=10)
        # Users menu
        ttk.Label(self, text='Choose user', font=self.titleFont).grid(column=0, row=1, padx=10, pady=10)
        if len(user_name_list) > 0:
            ttk.OptionMenu(self, self.menu, user_name_list[0], *user_name_list,
                       command=self._set_username_password).grid(column=0, row=2)
        else:
            ttk.Label(self, text='No Users, go to Accounts', font=self.titleFont).grid(column=0, row=2, padx=10, pady=10)

        # username and password form
        ttk.Label(self, text='username:', font=self.bold).grid(column=0, row=3, padx=10, pady=10, sticky='w')
        ttk.Entry(self, textvariable=self.username, width=30, show='*').grid(column=0, row=3)
        ttk.Label(self, text='password:', font=self.bold).grid(column=0, row=4, padx=10, pady=10, sticky='w')
        ttk.Entry(self, textvariable=self.password, width=30, show='*').grid(column=0, row=4)
        ttk.Button(self, text="RUN", command=self._check_form).grid(column=0, row=5)

        # box list display all the names of people that are not following you back
        ttk.Label(self, text='Search results:', font=self.titleFont).grid(column=3, row=1)
        self.listbox = Listbox(self, width=25, height=13)
        self.listbox.grid(column=3, rowspan=4, row=2)

        ttk.Button(self, text="SEARCH", command=self._search_user).grid(column=3, row=8, pady=(8, 8))

    def _check_form(self):
        username = self.username.get()
        password = self.password.get()

        database = db.Database()
        is_schedule = database.get_data_from_settings()

        if username == '' or password == '':
            messagebox.showerror('Credentials', 'Please enter your username or password')
            return False
        else:
            self.bot = InstagramBot(username, password)
            self.bot.login()
            users_list = []
            self.amount_not_following = 0
            users_list = self.bot.get_unfollowers()

            # This if check if in the settings, the user Activate the Schedule function ( Set time to unfollow users)
            if is_schedule[3] == 1:
                database.save_unfollow_users(users_list)

            for user in users_list:
                self.listbox.insert(END, user)
                self.amount_not_following += 1

            if self.amount_not_following == 0:
                ttk.Label(self, text='Everyone following you back!', font=self.results)\
                                                    .grid(column=3, row=6, pady=(8, 8))
            else:
                ttk.Label(self, text='{} Not following you!'.format(self.amount_not_following),
                          font=self.results).grid(column=3, row=6, pady=(8, 8))
                ttk.Label(self, text='Do you want to UNFOLLOW them? ',
                          font=self.results).grid(column=3, row=9, pady=(16, 16))
                ttk.Button(self, text="Click here", command=lambda: self._unfollow_users(users_list))\
                                                    .grid(column=3, row=10, pady=(8, 8))

            return True

    # open selected user instagram page
    def _search_user(self):
        name_selection = self.listbox.get(self.listbox.curselection())
        self.bot.nav_user(name_selection)

    # Getting the username from the menu option, look for it on the list and sets username and password
    def _set_username_password(self, value):
        for account in self.accounts:
            if value == account[2]:
                self.username.set(account[2])
                self.password.set(account[3])

    def _unfollow_users(self, user_list):
        to_delete = messagebox.askyesno('UNFOLLOW', 'Are you sure you want to UNFOLLOW them?')
        if to_delete:
            self.bot.unfollow_users(user_list)
