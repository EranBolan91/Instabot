from tkinter import *
from tkinter import ttk, messagebox
import tkinter.font as tkfont
from database import db
from database.dm import dm
from bot_folder.combination.combination_bot import CombinationBot
from utils.schedule import ScheduleCalc
import threading


class TabCombination(ttk.Frame):
    def __init__(self, window):
        super().__init__(window)

        self.dividerFont = tkfont.Font(family="Helvetica", size=25)
        self.headerFont = tkfont.Font(family="Helvetica", size=12, weight='bold')
        self.titleFont = tkfont.Font(family="Helvetica", size=9)
        self.h3 = tkfont.Font(family="Helvetica", size=11, weight='bold')
        self.bold = tkfont.Font(weight='bold', size=10)

        self.check_box_distribution_list = IntVar()
        self.distribution_menu_var = StringVar()
        self.amount_follows = IntVar()
        self.amount_likes = IntVar()
        self.username = StringVar()
        self.password = StringVar()
        self.hashtag = StringVar()
        self.menu = StringVar()
        self.url = StringVar()
        self.groups_list = []

        self.check_box_distribution_list.set(0)

        self.accounts = db.Database().get_accounts()
        user_name_list = []
        for account in self.accounts:
            user_name_list.append(account[3])

        ttk.Label(self, text='Combination - Follow after user who liked post', font=self.headerFont) \
            .grid(column=0, row=0, padx=10, pady=5)

        # username and password form
        ttk.Label(self, text='Please enter username and password', font=self.titleFont) \
            .grid(column=0, row=1, padx=10, pady=5)
        ttk.Label(self, text='username:', font=self.bold).grid(column=0, row=2, padx=(50, 0), pady=10, sticky='w')
        ttk.Entry(self, textvariable=self.username, show='*').grid(column=0, row=2)
        ttk.Label(self, text='password:', font=self.bold).grid(column=0, row=3, padx=(50, 0), pady=10, sticky='w')
        ttk.Entry(self, textvariable=self.password, show='*').grid(column=0, row=3)

        # Hash tag form - for example 'travel'
        ttk.Label(self, text='Enter the hash tag keyword ', font=self.h3).grid(column=0, row=5, padx=10, pady=10)
        ttk.Entry(self, textvariable=self.hashtag).grid(column=0, row=6)

        # OR
        ttk.Label(self, text='<-- OR -->', font=self.dividerFont).grid(column=1, row=5, rowspan=2, padx=(0, 70), pady=(40, 0))

        # URL input
        ttk.Label(self, text='Enter the URL', font=self.h3).grid(column=2, row=5)
        ttk.Entry(self, textvariable=self.url, width=50).grid(column=2, row=6)

        # Users menu
        ttk.Label(self, text='Choose user', font=self.titleFont).grid(column=1, row=1, padx=10, pady=(25, 0))
        if len(user_name_list) > 0:
            self.accounts_option_menu = ttk.OptionMenu(self, self.menu, user_name_list[0], *user_name_list,
                                                       command=self._set_username_password)
            self.accounts_option_menu.grid(column=1, row=2)
        else:
            ttk.Label(self, text='No Users, go to Accounts', font=self.titleFont) \
                .grid(column=1, row=2, padx=10, pady=10)

        # Groups distribution
        # If there are groups, it will display them. Else it will display message
        if len(self.groups_list) > 0:
            self.distribution_menu = ttk.OptionMenu(self, self.distribution_menu_var, self.groups_list[0],
                                                    *self.groups_list, state='DISABLED')
            self.distribution_menu.grid(column=1, row=3)
        else:
            self.distribution_title = ttk.Label(self, text="Choose user to display distribution lists ",
                                                font=self.titleFont)
            self.distribution_title.grid(column=1, row=3)

        self.distribution_check_box = ttk.Checkbutton(self, variable=self.check_box_distribution_list,
                                                      text='Save users in distribution list?')
        self.distribution_check_box.grid(column=2, row=3, pady=10)

        # Input of amount for likes and follow
        ttk.Label(self, text='Enter the number of posts to like').grid(column=0, row=7, pady=(50, 0))
        ttk.Entry(self, textvariable=self.amount_likes).grid(column=0, row=8, pady=(25, 0))

        ttk.Label(self, text='Enter the number of users to follow').grid(column=1, row=7, pady=(50, 0))
        ttk.Entry(self, textvariable=self.amount_follows).grid(column=1, row=8, pady=(25, 0))

        # Run the script button
        ttk.Button(self, text="RUN", command=self._run_script).grid(column=0, columnspan=2, row=10, pady=(40, 0), padx=(20, 0))

    def _run_script(self):
        username = self.username.get()
        password = self.password.get()
        distribution = self.check_box_distribution_list.get()
        follow = self.amount_follows.get()
        like = self.amount_likes.get()
        hash_tag = self.hashtag.get()
        url = self.url.get()

        if distribution:
            group_name = self.distribution_menu_var.get()
            for group in self.distribution_list:
                if group_name == group[1]:
                    group_id = group[0]
        else:
            group_name = ""
            group_id = ""

        valid = self._check_form(username, password, hash_tag, url, follow, like)

        if valid:
            bot = CombinationBot(username, password, False)
            t = threading.Thread(target=bot.combination, args=(hash_tag, url, like, follow, distribution, 0, group_name, group_id))
            t.start()

    # Getting the username from the menu option, look for it on the list and sets username and password
    def _set_username_password(self, value):
        self.groups_list = []
        for account in self.accounts:
            if value == account[3]:
                self.username.set(account[3])
                self.password.set(account[4])
                self.distribution_list = db.Database().get_distribution_lists_by_username(value)
                for group in self.distribution_list:
                    self.groups_list.append(group[1])
                if len(self.groups_list) > 0:
                    self.distribution_menu = ttk.OptionMenu(self, self.distribution_menu_var, self.groups_list[0],
                                                            *self.groups_list)
                    self.distribution_menu.grid(column=1, row=3)
                    self.distribution_title.grid_forget()
                else:
                    self.distribution_title.grid(column=1, row=3)
                    self.distribution_menu.grid_forget()

    def _check_form(self, username, password, hash_tag, url, follows, likes):
        if username == '' or password == '':
            messagebox.showerror('Credentials', 'Please enter your username or password')
            return False

        if not hash_tag and not url:
            messagebox.showerror('Search data', 'Hash tag and url entry cannot be empty')
            return False

        if follows == 0:
            messagebox.showerror('No number', 'Please enter number for follow')
            return False

        if likes == 0:
            messagebox.showerror('No number', 'Please enter number for likes')
            return False

        if url and hash_tag:
            messagebox.showerror('Too many arguments', 'You can choose only one action! HASHTAG or URL')
            return False

        return True
