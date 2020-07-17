from tkinter import *
from tkinter import ttk, messagebox
import tkinter.font as tkfont
from bot_folder.followers.followers_bot import FollowersBot
from database import db
import threading


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
        self.amount_unfollow_users = 0

        self.accounts = db.Database().get_accounts()
        user_name_list = []
        for account in self.accounts:
            user_name_list.append(account[3])

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

        # box list display all users that the account has followed them
        self.unfollow_title = ttk.Label(self, text='You are following {}'.format(self.amount_not_following), font=self.bold)
        self.unfollow_title.grid(column=0, row=6, pady=20)
        self.unfollow_users_list_box = Listbox(self, width=25, height=16)
        self.unfollow_users_list_box.grid(column=0, row=7, rowspan=3)
        ttk.Button(self, text="REMOVE", command=self._remove_from_unfollow_list).grid(column=0, row=11, rowspan=1, pady=(10, 0))
        ttk.Button(self, text="UNFOLLOW LIST", command=lambda: self._unfollow_users_list(self.unfollow_users))\
            .grid(column=0, columnspan=2, row=11, pady=(10, 0), padx=(0, 200))
        ttk.Button(self, text="UNFOLLOW USER", command=self._unfollow_user)\
            .grid(column=0, columnspan=2, row=11, pady=(10, 0), padx=(200, 0))

        # box list display all the names of people that are not following you back
        ttk.Label(self, text='Search results:', font=self.titleFont).grid(column=3, row=1)
        self.listbox = Listbox(self, width=30, height=13)
        self.listbox.grid(column=3, rowspan=5, row=2)

        ttk.Button(self, text="SEARCH", command=self._search_user).grid(column=3, row=8, rowspan=3, pady=(8, 8))

        # right side - unfollow all users in list box
        schedule_frame = ttk.LabelFrame(self, text='UNFOLLOW EVERYONE')
        schedule_frame.grid(column=4, row=1, ipady=30, rowspan=2, padx=40)
        title = Label(schedule_frame, text="By click this button, the program will go to your 'following' list "
                                           "and will unfollow all of them",
                      bg='gray23', font=self.bold, fg='gray67')
        unfollow_btn = ttk.Button(schedule_frame, text="UNFOLLOW", command=self._unfollow_all_users_account_follow_them)
        title.pack(fill=X)
        unfollow_btn.place(anchor=S, relx=0.5, rely=0.8)

    def _check_form(self):
        username = self.username.get()
        password = self.password.get()

        if username == '' or password == '':
            messagebox.showerror('Credentials', 'Please enter your username or password')
            return False
        else:
            users_list = []
            self.amount_not_following = 0
            self.bot = FollowersBot(username, password, False)
            # TODO: write thread that return's data
            # que = queue.Queue()
            # t = threading.Thread(target=self.bot.get_unfollowers, args=(que))
            # t.start()
            users_list = self.bot.get_unfollowers()

            self.listbox.delete(0, 'end')
            for user in users_list:
                self.listbox.insert(END, user)
                self.amount_not_following += 1

            if self.amount_not_following == 0:
                ttk.Label(self, text='Everyone following you back!', font=self.results)\
                                                    .grid(column=3, row=6, rowspan=2, pady=(8, 8))
            else:
                ttk.Label(self, text='{} Not following you!'.format(self.amount_not_following),
                          font=self.results).grid(column=3, row=6, rowspan=2, pady=(8, 8))
                ttk.Label(self, text='Do you want to UNFOLLOW them? ',
                          font=self.results).grid(column=3, row=9, rowspan=2, pady=(16, 16))
                ttk.Button(self, text="Click here", command=lambda: self._unfollow_users_list(users_list))\
                                                    .grid(column=3, row=10, rowspan=2, pady=(8, 8))

            return True

    # open selected user instagram page
    def _search_user(self):
        name_selection = self.listbox.get(self.listbox.curselection())
        print(name_selection)
        if name_selection:
            self.bot._nav_user(name_selection)

    def _unfollow_user(self):
        name_selection = self.unfollow_users_list_box.get(self.unfollow_users_list_box.curselection())
        if name_selection:
            username = self.username.get()
            password = self.password.get()
            bot = FollowersBot(username, password, False)
            t = threading.Thread(target=bot.unfollow_user, args=(name_selection,))
            t.start()

    # Getting the username from the menu option, look for it on the list and sets username and password
    def _set_username_password(self, value):
        for account in self.accounts:
            if value == account[3]:
                self.username.set(account[3])
                self.password.set(account[4])

                self.unfollow_users_list_box.delete(0, 'end')
                self.amount_not_following = 0
                self.unfollow_users = db.Database().get_unfollow_users(account[3])
                for user in self.unfollow_users:
                    self.unfollow_users_list_box.insert(END, user[2])
                    self.amount_not_following += 1
                self.unfollow_title.config(text='You are following {}'.format(self.amount_not_following))

    def _unfollow_users_list(self, user_list):
        to_delete = messagebox.askyesno('UNFOLLOW', 'Are you sure you want to UNFOLLOW them?')
        if to_delete:
            users_name_list = []
            for username in user_list:
                users_name_list.append(username[2])
            username = self.username.get()
            password = self.password.get()
            bot = FollowersBot(username, password, False)
            t = threading.Thread(target=bot.unfollow_users, args=(users_name_list, ))
            t.start()

    def _unfollow_all_users_account_follow_them(self):
        to_delete = messagebox.askyesno('UNFOLLOW', 'Are you sure you want to UNFOLLOW all of them?')
        if to_delete:
            username = self.username.get()
            password = self.password.get()
            if not username and not password:
                messagebox.showerror('Credentials', 'Please enter your username or password')
            else:
                bot = FollowersBot(username, password, False)
                t = threading.Thread(target=bot.unfollow_all_users)
                t.start()

    def _remove_from_unfollow_list(self):
        name_selection = self.unfollow_users_list_box.get(self.unfollow_users_list_box.curselection())
        if name_selection:
            index = self.unfollow_users_list_box.get(0, END).index(name_selection)
            self.unfollow_users_list_box.delete(index)
            db.Database().remove_username_from_unfollow_list(name_selection)