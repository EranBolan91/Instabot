from tkinter import *
from tkinter import ttk, messagebox
import tkinter.font as tkfont
from bot_folder.location.location_bot import LocationBot
from database import db


class TabLocation(ttk.Frame):
    def __init__(self, window):
        super().__init__(window)
        self.location_url = StringVar()
        self.location = StringVar()
        self.check_box_like = IntVar()
        self.check_box_follow = IntVar()
        self.check_box_comment = IntVar()
        self.amount = StringVar()
        self.menu = StringVar()
        self.username = StringVar()
        self.password = StringVar()

        self.check_box_comment.set(0)
        self.check_box_like.set(0)
        self.check_box_follow.set(0)

        self.headerFont = tkfont.Font(family="Helvetica", size=14, weight='bold')
        self.titleFont = tkfont.Font(family="Helvetica", size=9)
        self.h3 = tkfont.Font(family="Helvetica", size=11, weight='bold')
        self.bold = tkfont.Font(weight='bold', size=10)

        self.accounts = db.Database().get_accounts()
        user_name_list = []
        for account in self.accounts:
            user_name_list.append(account[3])

        ttk.Label(self, text='Find posts by Location', font=self.headerFont).grid(column=0, row=0, padx=10, pady=10)
        # Search location by URL
        ttk.Label(self, text='Find location by its URL', font=self.h3).grid(column=0, row=1, padx=10, pady=10)
        ttk.Entry(self, textvariable=self.location_url, width=40).grid(column=0, row=2)
        ttk.Label(self, text='*For example: \' https://www.instagram.com/explore/locations/212988663/new-york-new-york/ \' ', font=self.titleFont)\
                                                                                .grid(column=0, row=3, padx=10, pady=10)
        # Search location by name
        ttk.Label(self, text='Find location by its name', font=self.h3).grid(column=0, row=4, padx=10, pady=10)
        ttk.Entry(self, textvariable=self.location, width=40, state=DISABLED).grid(column=0, row=5)
        ttk.Label(self, text='*For example: \'New York, Shalvata, Lighthouse hotel...(Not active now...) \' ',
                  font=self.titleFont).grid(column=0, row=6, padx=10, pady=10)

        # Amount of posts to like/comment/follow
        ttk.Label(self, text='Enter the number of posts to like/comment/follow', font=self.titleFont).grid(column=0, row=7, padx=10,
                                                                                         pady=10)
        ttk.Entry(self, textvariable=self.amount).grid(column=0, row=8)

        # title for the checkbox
        ttk.Label(self, text='You can choose more then one action', font=self.h3).grid(column=0, row=9, padx=10,
                                                                                       pady=10)

        # Checkbox buttons
        ttk.Checkbutton(self, text='LIKE posts', variable=self.check_box_like) \
            .grid(column=0, row=11, padx=20, pady=20, sticky='w')
        ttk.Checkbutton(self, variable=self.check_box_follow, text='FOLLOW users') \
            .grid(column=0, row=12, padx=20, pady=20, sticky='w')
        ttk.Checkbutton(self, text='Write you\'re COMMENT on post ', variable=self.check_box_comment,
                        command=self._activate_check, ) \
            .grid(column=0, row=13, padx=20, pady=20, sticky='w')

        self.comment_entry = ttk.Entry(self, state='disabled', width=50)
        self.comment_entry.grid(column=0, row=14)
        ttk.Label(self, text="To comment on posts enter more then one word, use ' , ' to separate each word  ", font=self.titleFont)\
                                                                               .grid(column=0, row=15, padx=10, pady=10)
        ttk.Label(self, text="For example: Nice picture,Looking good,I like it  ", font=self.titleFont)\
                                                                                    .grid(column=0, row=16)

        # Users menu
        ttk.Label(self, text='Choose user', font=self.titleFont).grid(column=1, row=1, padx=10, pady=10, columnspan=2)
        if len(user_name_list) > 0:
            print(user_name_list)
            ttk.OptionMenu(self, self.menu, user_name_list[0], *user_name_list,
                       command=self._set_username_password).grid(column=1, row=2, columnspan=2)
        else:
            ttk.Label(self, text='No Users, go to Accounts', font=self.titleFont).grid(column=1, row=2, padx=10, pady=10)

        ttk.Label(self, text='Please enter username and password', font=self.titleFont) \
            .grid(column=1, row=3, padx=10, pady=10, columnspan=2)
        ttk.Label(self, text='username:', font=self.bold).grid(column=1, row=4, padx=(60, 0), pady=10, sticky='w')
        ttk.Entry(self, textvariable=self.username, show='*', width=30).grid(column=2, row=4)
        ttk.Label(self, text='password:', font=self.bold).grid(column=1, row=5, padx=(60, 0), pady=10, sticky='w')
        ttk.Entry(self, textvariable=self.password, show='*', width=30).grid(column=2, row=5)

        ttk.Button(self, text="SEARCH", command=self._run_script).grid(column=0, row=17, pady=8)

    def _run_script(self):
        location_url = self.location_url.get()
        location = self.location.get()
        amount = self.amount.get()
        like = self.check_box_like.get()
        comment = self.check_box_comment.get()
        follow = self.check_box_follow.get()
        entry_comment = self.comment_entry.get()
        username = self.username.get()
        password = self.password.get()
        split_comment = ""

        # This split the comment for a list of comments
        if entry_comment != "":
            split_comment = self._split_comment(entry_comment)

        valid = self._check_form(location_url, location, amount, username, password)
        if valid:
            if location_url != '':
                bot = LocationBot(username, password)
                bot.search_location_by_url(location_url, amount, like, follow, comment, split_comment)
            elif location != '':
                bot = LocationBot(username, password)
                bot.search_location_by_name(location, amount, like, follow, comment, split_comment)

    def _check_form(self, location_url, location, amount, username, password):
        if username == '' or password == '':
            messagebox.showerror('Credentials', 'Please enter your username or password')
            return False

        if location_url == '' and location == '':
            messagebox.showerror('Search data', 'Please provide URL or location name')
            return False

        if amount.isnumeric() and not int(amount) <= 0:
            return True
        else:
            messagebox.showerror('Only numbers', 'Please enter only numbers to amount entry')
            return False

    def _activate_check(self):
        if self.check_box_comment.get() == 1:  # whenever checked
            self.comment_entry.config(state=NORMAL)
        elif self.check_box_comment.get() == 0:  # whenever unchecked
            self.comment_entry.config(state=DISABLED)

    # Getting the username from the menu option, look for it on the list and sets username and password
    def _set_username_password(self, value):
        for account in self.accounts:
            if value == account[3]:
                self.username.set(account[3])
                self.password.set(account[4])

    def _split_comment(self, comment):
        split_comment = comment.split(',')
        return split_comment