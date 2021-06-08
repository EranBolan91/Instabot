from tkinter import *
from tkinter import ttk, messagebox
import tkinter.font as tkfont
from bot_folder.follow_followers.follow_followers_bot import FollowFollowersBot
from utils.schedule import ScheduleCalc
from database import db
from database.follow_followers.follow_followers import FollowFollowersDB
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
        self.groups_list = []
        self.check_box_distribution_list = IntVar()
        self.distribution_menu_var = StringVar()
        self.minutes_entry_value = IntVar()
        self.hours_entry_value = IntVar()
        self.days_entry_value = IntVar()
        self.num_skip = IntVar()
        self.check_box_schedule = IntVar()
        self.radio_var = IntVar()
        self.proxy = StringVar()
        self.port = StringVar()
        self.MINUTES = 0
        self.HOURS = 1
        self.DAYS = 2

        self.check_box_schedule.set(0)
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
        ttk.Label(self, text='username:', font=self.bold).grid(column=0, rowspan=3, row=4, padx=10, pady=(25, 0), sticky='w')
        ttk.Entry(self, textvariable=self.username_following, show='*', width=25).grid(column=0, rowspan=3, row=4, pady=(25, 0))
        ttk.Label(self, text='password:', font=self.bold).grid(column=0, rowspan=3, row=5, padx=10, pady=(10, 5), sticky='w')
        ttk.Entry(self, textvariable=self.password_following, show='*', width=25).grid(column=0, rowspan=3, row=5, pady=(10, 5))
        ttk.Button(self, text="START FOLLOW", command=self._search_following).grid(column=0, rowspan=3, row=6, pady=15)

        # Middle area - number of users to follow and distribution list
        ttk.Label(self, text='Enter the number of people to follow', font=self.titleFont).grid(column=0, columnspan=2, rowspan=4, row=6, pady=1)
        self.following_input = ttk.Entry(self, textvariable=self.num_following, width=20)
        self.following_input.grid(column=0, columnspan=2, rowspan=4, row=7, pady=(5, 0))

        ttk.Label(self, text='Enter the number to skip', font=self.titleFont).grid(column=0, columnspan=2, rowspan=4, row=8)
        self.skip_input = ttk.Entry(self, textvariable=self.num_skip, width=20).grid(column=0, columnspan=2, rowspan=4, row=9)

        self.distribution_check_box = ttk.Checkbutton(self, variable=self.check_box_distribution_list,
                                                      text='Save users in distribution list?')
        self.distribution_check_box.grid(column=0, columnspan=2, rowspan=4, row=11, pady=(70, 0), padx=(0, 5))
        ttk.Checkbutton(self, text='Schedule action', variable=self.check_box_schedule) \
            .grid(column=0, columnspan=2, rowspan=4, row=12, pady=(100, 0), padx=(1, 1))
        # Groups distribution
        # If there are groups, it will display them. Else it will display message
        if len(self.groups_list) > 0:
            self.distribution_menu = ttk.OptionMenu(self, self.distribution_menu_var, self.groups_list[0],
                                                    *self.groups_list, state='DISABLED')
            self.distribution_menu.grid(column=0, columnspan=2, rowspan=4, row=10, pady=(20, 0))
        else:
            self.distribution_title = ttk.Label(self, text="Choose user to display distribution lists ",
                                                font=self.titleFont)
            self.distribution_title.grid(column=0, columnspan=2, rowspan=4, row=10, pady=(20, 0))

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
        ttk.Label(self, text='username:', font=self.bold).grid(column=1, row=4, rowspan=3,  padx=10, pady=(25, 0), sticky='w')
        ttk.Entry(self, textvariable=self.username_followers, show='*', width=25).grid(column=1, row=4, rowspan=3, pady=(25, 0))
        ttk.Label(self, text='password:', font=self.bold).grid(column=1, row=5, rowspan=3, padx=10, pady=(10, 5), sticky='w')
        ttk.Entry(self, textvariable=self.password_followers, show='*', width=25).grid(column=1, row=5, rowspan=3, pady=(10, 5))
        ttk.Button(self, text="START FOLLOW", command=self._search_followers).grid(column=1, rowspan=3, row=6, pady=15)

        # Schedule Actions
        schedule_frame = ttk.LabelFrame(self, text='Schedule Action')
        schedule_frame.grid(column=2, row=2, rowspan=2, ipadx=25, ipady=10, padx=(30, 0))
        entry_frame = ttk.Frame(schedule_frame)
        radio_min = ttk.Radiobutton(schedule_frame, text='Minuts', variable=self.radio_var, value=self.MINUTES,
                                    command=self._enable_entry)
        radio_hours = ttk.Radiobutton(schedule_frame, text='Hours', variable=self.radio_var, value=self.HOURS,
                                      command=self._enable_entry)
        radio_days = ttk.Radiobutton(schedule_frame, text='Days', variable=self.radio_var, value=self.DAYS,
                                     command=self._enable_entry)
        self.minutes_entry = ttk.Entry(entry_frame, textvariable=self.minutes_entry_value)
        self.hours_entry = ttk.Entry(entry_frame, textvariable=self.hours_entry_value, state='disabled')
        self.days_entry = ttk.Entry(entry_frame, textvariable=self.days_entry_value, state='disabled')
        radio_min.place(relx=0.08, rely=0)
        radio_hours.place(relx=0.34, rely=0)
        radio_days.place(relx=0.6, rely=0)
        self.minutes_entry.pack(side=LEFT)
        self.hours_entry.pack(side=LEFT)
        self.days_entry.pack(side=LEFT)
        entry_frame.pack(side=LEFT, pady=(50, 0))

        # Proxy section
        proxy_frame = ttk.LabelFrame(self, text='Proxy')
        proxy_frame.grid(column=2, row=4, rowspan=2, ipadx=40, ipady=10, padx=(30, 0))
        entry_frame = ttk.Frame(proxy_frame)
        self.proxy_entry = ttk.Entry(entry_frame, textvariable=self.proxy, width=20)
        self.port_entry = ttk.Entry(entry_frame, textvariable=self.port)
        self.proxy_entry.pack(side=LEFT)
        self.port_entry.pack(side=LEFT)
        entry_frame.pack(side=LEFT, pady=(50, 0))

        # Users data box - right side
        ttk.Label(self, text='User data', font=self.headerFont).grid(column=2, row=5, rowspan=3, padx=(0, 50), pady=(0, 20))
        data_frame = ttk.Frame(self)
        data_frame.grid(column=2, row=6, rowspan=3, padx=0, pady=(70, 0))
        scrollbary = ttk.Scrollbar(data_frame)
        scrollbarx = ttk.Scrollbar(data_frame, orient=HORIZONTAL)
        scrollbary.pack(side=RIGHT, fill=Y)
        scrollbarx.pack(side=BOTTOM, fill=X)
        self.data_frame_box = Listbox(data_frame, width=70, height=10,
                                        yscrollcommand=scrollbary.set, xscrollcommand=scrollbarx.set)
        self.data_frame_box.pack()

    # Getting the username from the menu option, look for it on the list and sets username and password
    def _set_username_password_following(self, value):
        self.groups_list = []
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
                    self.distribution_menu.grid(column=0, columnspan=2, row=11, rowspan=4, pady=5)
                    self.distribution_title.grid_forget()
                else:
                    self.distribution_title.grid(column=0, columnspan=2, row=11, rowspan=4, pady=5)
                    self.distribution_menu.grid_forget()
                self._get_account_data_for_data_box(account[3])

    # Getting the username from the menu option, look for it on the list and sets username and password
    def _set_username_password_followers(self, value):
        self.groups_list = []
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
                    self.distribution_menu.grid(column=0, columnspan=2, row=11, rowspan=4, pady=5)
                    self.distribution_title.grid_forget()
                else:
                    self.distribution_title.grid(column=0, columnspan=2, row=11, rowspan=4, pady=5)
                    self.distribution_menu.grid_forget()
                self._get_account_data_for_data_box(account[3])

    def _get_account_data_for_data_box(self, account_name):
        account_data = FollowFollowersDB().get_account_data(account_name)
        self.data_frame_box.delete(0, 'end')
        for data in account_data:
            box = """ Date: {} | Follow: {} | Failed Follow: {} | Skip: {} | URL: {} """.format(
                data[8], data[3], data[4], data[9], data[2],)
            self.data_frame_box.insert(END, box)


    def _search_followers(self):
        user_url = self.user_url_followers.get()
        username = self.username_followers.get()
        password = self.password_followers.get()
        num_of_following = self.num_following.get()
        distribution = self.check_box_distribution_list.get()
        action = self.radio_var.get()
        schedule_action = self.check_box_schedule.get()
        minutes_entry = self.minutes_entry_value.get()
        hours_entry = self.hours_entry_value.get()
        days_entry = self.days_entry_value.get()
        num_skip = self.num_skip.get()
        proxy = self.proxy.get()
        port = self.port.get()
        group_id = ""
        group_name = ""

        if distribution:
            group_name = self.distribution_menu_var.get()
            for group in self.distribution_list:
                if group_name == group[1]:
                    group_id = group[0]

        valid = self._check_form(username, password, user_url, num_of_following)
        proxy_dict = {"proxy": proxy, "port": port}
        if valid:
            is_schedule = 0
            if schedule_action:
                is_schedule = 1
                time_schedule = ScheduleCalc().calc_schedule_time(action, minutes_entry, hours_entry, days_entry)
                bot = FollowFollowersBot(username, password, False, proxy_dict)
                timing_thread = threading.Timer(time_schedule, bot.follow_after_followers,
                      [user_url, self.account_username, num_of_following, distribution, group_name, group_id, is_schedule, num_skip])
                timing_thread.start()
            else:
                bot = FollowFollowersBot(username, password, False, proxy_dict)
                t = threading.Thread(target=bot.follow_after_followers,
                      args=(user_url, self.account_username, num_of_following, distribution, group_name, group_id, is_schedule, num_skip))
                t.start()
        else:
            messagebox.showerror('Missing data', 'Please enter URL')

    def _search_following(self):
        user_url = self.user_url_following.get()
        username = self.username_following.get()
        password = self.password_following.get()
        num_of_following = self.num_following.get()
        distribution = self.check_box_distribution_list.get()
        action = self.radio_var.get()
        schedule_action = self.check_box_schedule.get()
        minutes_entry = self.minutes_entry_value.get()
        hours_entry = self.hours_entry_value.get()
        days_entry = self.days_entry_value.get()
        num_skip = self.num_skip.get()
        proxy = self.proxy.get()
        port = self.port.get()
        group_id = ""
        group_name = ""

        if distribution:
            group_name = self.distribution_menu_var.get()
            for group in self.distribution_list:
                if group_name == group[1]:
                    group_id = group[0]
                    print(group_id)

        valid = self._check_form(username, password, user_url, num_of_following)
        proxy_dict = {"proxy": proxy, "port": port}
        if valid:
            is_schedule = 0
            if schedule_action:
                is_schedule = 1
                time_schedule = ScheduleCalc().calc_schedule_time(action, minutes_entry, hours_entry, days_entry)
                bot = FollowFollowersBot(username, password, False, proxy_dict)
                timing_thread = threading.Timer(time_schedule, bot.follow_after_following,
                      [user_url, self.account_username, num_of_following, distribution, group_name, group_id, is_schedule, num_skip])
                timing_thread.start()
            else:
                bot = FollowFollowersBot(username, password, False, proxy_dict)
                t = threading.Thread(target=bot.follow_after_following,
                      args=(user_url, self.account_username, num_of_following, distribution, group_name, group_id, is_schedule, num_skip))
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

    # method to enable and disable entry by clicking the radio button
    def _enable_entry(self):
        radio_selected = self.radio_var.get()
        if radio_selected == self.MINUTES:
            self.minutes_entry.config(state=NORMAL)
            self.hours_entry.config(state=DISABLED)
            self.days_entry.config(state=DISABLED)
        elif radio_selected == self.HOURS:
            self.minutes_entry.config(state=DISABLED)
            self.hours_entry.config(state=NORMAL)
            self.days_entry.config(state=DISABLED)
        elif radio_selected == self.DAYS:
            self.minutes_entry.config(state=DISABLED)
            self.hours_entry.config(state=DISABLED)
            self.days_entry.config(state=NORMAL)
