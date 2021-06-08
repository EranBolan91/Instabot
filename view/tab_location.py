from tkinter import *
from tkinter import ttk, messagebox
import tkinter.font as tkfont
from bot_folder.location.location_bot import LocationBot
from utils.schedule import ScheduleCalc
from database import db
import threading


class TabLocation(ttk.Frame):
    def __init__(self, window):
        super().__init__(window)
        self.location_url = StringVar()
        self.location = StringVar()
        self.check_box_like = IntVar()
        self.check_box_follow = IntVar()
        self.check_box_comment = IntVar()
        self.check_box_distribution_list = IntVar()
        self.check_box_schedule = IntVar()
        self.distribution_menu_var = StringVar()
        self.minutes_entry_value = IntVar()
        self.hours_entry_value = IntVar()
        self.days_entry_value = IntVar()
        self.amount = StringVar()
        self.menu = StringVar()
        self.username = StringVar()
        self.password = StringVar()
        self.groups_list = []
        self.radio_var = IntVar()
        self.proxy = StringVar()
        self.port = StringVar()
        self.MINUTES = 0
        self.HOURS = 1
        self.DAYS = 2

        self.check_box_schedule.set(0)
        self.check_box_comment.set(0)
        self.check_box_like.set(0)
        self.check_box_follow.set(0)
        self.check_box_distribution_list.set(0)

        self.headerFont = tkfont.Font(family="Helvetica", size=14, weight='bold')
        self.titleFont = tkfont.Font(family="Helvetica", size=9)
        self.h3 = tkfont.Font(family="Helvetica", size=11, weight='bold')
        self.bold = tkfont.Font(weight='bold', size=10)

        self.accounts = db.Database().get_accounts()
        user_name_list = []
        for account in self.accounts:
            user_name_list.append(account[3])

        ttk.Label(self, text='Find posts by Location', font=self.headerFont).grid(column=0, row=0, padx=10, pady=5)
        # Search location by URL
        ttk.Label(self, text='Find location by its URL', font=self.h3).grid(column=0, row=1, padx=10, pady=5)
        ttk.Entry(self, textvariable=self.location_url, width=40).grid(column=0, row=2)
        ttk.Label(self, text='*For example: \' https://www.instagram.com/explore/locations/212988663/new-york-new-york/ \' ', font=self.titleFont)\
                                                                                .grid(column=0, row=3, padx=10, pady=5)
        # Search location by name
        ttk.Label(self, text='Find location by its name', font=self.h3).grid(column=0, row=4, padx=10, pady=5)
        ttk.Entry(self, textvariable=self.location, width=40, state=DISABLED).grid(column=0, row=5)
        ttk.Label(self, text='*For example: \'New York, Shalvata, Lighthouse hotel...(Not active now...) \' ',
                  font=self.titleFont).grid(column=0, row=6, padx=10, pady=5)

        # Amount of posts to like/comment/follow
        ttk.Label(self, text='Enter the number of posts to like/comment/follow', font=self.titleFont).grid(column=0, row=7, padx=10,
                                                                                         pady=10)
        ttk.Entry(self, textvariable=self.amount).grid(column=0, row=8)

        # title for the checkbox
        ttk.Label(self, text='You can choose more then one action', font=self.h3).grid(column=0, row=9, padx=10,
                                                                                       pady=10)

        # Checkbox buttons
        ttk.Checkbutton(self, text='LIKE posts', variable=self.check_box_like) \
            .grid(column=0, row=11, padx=20, pady=10, sticky='w')
        ttk.Checkbutton(self, variable=self.check_box_follow, text='FOLLOW users', command=self._activate_distribution_check_box) \
            .grid(column=0, row=12, padx=20, pady=10, sticky='w')
        self.distribution_check_box = ttk.Checkbutton(self, variable=self.check_box_distribution_list,
                                                      text='Save users in distribution list?', state='disabled')
        self.distribution_check_box.grid(column=0, row=12, pady=10)
        # Groups distribution
        # If there are groups, it will display them. Else it will display message
        if len(self.groups_list) > 0:
            self.distribution_menu = ttk.OptionMenu(self, self.distribution_menu_var, self.groups_list[0],
                                                    *self.groups_list, state='DISABLED')
            self.distribution_menu.grid(column=0, row=12)
        else:
            self.distribution_title = ttk.Label(self, text="Choose user to display distribution lists ",
                                                font=self.titleFont)
            self.distribution_title.grid(column=1, columnspan=1, row=12)

        ttk.Checkbutton(self, text='Write you\'re COMMENT on post ', variable=self.check_box_comment,
                        command=self._activate_check, ) \
            .grid(column=0, row=13, padx=20, pady=10, sticky='w')

        ttk.Checkbutton(self, text='Schedule action', variable=self.check_box_schedule) \
            .grid(column=0, row=14, pady=10, padx=20, sticky='w')

        self.comment_entry = ttk.Entry(self, state='disabled', width=50)
        self.comment_entry.grid(column=0, row=15)
        ttk.Label(self, text="To comment on posts enter more then one word, use ' , ' to separate each word  ", font=self.titleFont)\
                                                                               .grid(column=0, row=16, padx=10, pady=10)
        ttk.Label(self, text="For example: Nice picture,Looking good,I like it  ", font=self.titleFont)\
                                                                                    .grid(column=0, row=17)

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

        # Schedule Actions
        schedule_frame = ttk.LabelFrame(self, text='Schedule Action')
        schedule_frame.grid(column=3, row=2, rowspan=2, ipadx=25, ipady=10, padx=(30, 0))
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
        proxy_frame.grid(column=3, row=4, rowspan=2, ipadx=40, ipady=10, padx=(30, 0))
        entry_frame = ttk.Frame(proxy_frame)
        self.proxy_entry = ttk.Entry(entry_frame, textvariable=self.proxy, width=20)
        self.port_entry = ttk.Entry(entry_frame, textvariable=self.port)
        self.proxy_entry.pack(side=LEFT)
        self.port_entry.pack(side=LEFT)
        entry_frame.pack(side=LEFT, pady=(50, 0))

        ttk.Button(self, text="SEARCH", command=self._run_script).grid(column=0, row=18, pady=8)

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
        distribution = self.check_box_distribution_list.get()
        split_comment = ""
        action = self.radio_var.get()
        schedule_action = self.check_box_schedule.get()
        minutes_entry = self.minutes_entry_value.get()
        hours_entry = self.hours_entry_value.get()
        days_entry = self.days_entry_value.get()
        proxy = self.proxy.get()
        port = self.port.get()

        if distribution:
            group_name = self.distribution_menu_var.get()
            for group in self.distribution_list:
                if group_name == group[1]:
                    group_id = group[0]
        else:
            group_name = ""
            group_id = ""

        # This split the comment for a list of comments
        if entry_comment != "":
            split_comment = self._split_comment(entry_comment)

        valid = self._check_form(location_url, location, amount, username, password, proxy, port)
        proxy_dict = {"proxy": proxy, "port": port}
        if valid:
            if location_url != '':
                is_schedule = 0
                if schedule_action:
                    is_schedule = 1
                    time_schedule = ScheduleCalc().calc_schedule_time(action, minutes_entry, hours_entry, days_entry)
                    bot = LocationBot(username, password, False, proxy_dict)
                    timing_thread = threading.Timer(time_schedule, bot.search_location_by_url,
                                        [location_url, amount, like, follow, comment, split_comment,
                                        distribution, group_name, group_id, is_schedule])
                    timing_thread.start()
                else:
                    bot = LocationBot(username, password, False, proxy_dict)
                    t = threading.Thread(target=bot.search_location_by_url, args=(location_url, amount,
                                like, follow, comment, split_comment, distribution, group_name, group_id, is_schedule))
                    t.start()
            elif location != '':
                if schedule_action:
                    time_schedule = ScheduleCalc().calc_schedule_time(action, minutes_entry, hours_entry, days_entry)
                    bot = LocationBot(username, password, False, proxy_dict)
                    timing_thread = threading.Timer(time_schedule, bot.search_location_by_name,
                          [location, amount, like, follow, comment, split_comment,distribution, group_name,group_id])
                    timing_thread.start()
                else:
                    bot = LocationBot(username, password, False, proxy_dict)
                    t = threading.Thread(target=bot.search_location_by_name, args=(location, amount,
                                              like, follow, comment, split_comment, distribution, group_name, group_id))
                    t.start()

    def _check_form(self, location_url, location, amount, username, password, proxy, port):
        if username == '' or password == '':
            messagebox.showerror('Credentials', 'Please enter your username or password')
            return False

        if location_url == '' and location == '':
            messagebox.showerror('Search data', 'Please provide URL or location name')
            return False

        if proxy and not port:
            messagebox.showerror('PROXY', 'Please enter port number for the proxy')
            return False

        if not proxy and port:
            messagebox.showerror('PROXY', 'Please enter proxy address')
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
                self.distribution_list = db.Database().get_distribution_lists_by_username(value)
                for group in self.distribution_list:
                    self.groups_list.append(group[1])
                if len(self.groups_list) > 0:
                    self.distribution_menu = ttk.OptionMenu(self, self.distribution_menu_var, self.groups_list[0],
                                                            *self.groups_list)
                    self.distribution_menu.grid(column=0, columnspan=3, row=12)
                    self.distribution_title.grid_forget()
                else:
                    self.distribution_title.grid(column=1, columnspan=3, row=12)
                    self.distribution_menu.grid_forget()

    def _split_comment(self, comment):
        split_comment = comment.split(',')
        return split_comment

    # Active distribution check box
    def _activate_distribution_check_box(self):
        if self.check_box_follow.get() == 1:  # whenever checked
            self.distribution_check_box.config(state=NORMAL)
        elif self.check_box_follow.get() == 0:  # whenever unchecked
            self.distribution_check_box.config(state=DISABLED)

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
