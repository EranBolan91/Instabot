from tkinter import *
from tkinter import ttk, messagebox
import tkinter.font as tkfont
from bot_folder.followers.followers_bot import FollowersBot
from database import db
import threading
import concurrent.futures

from utils.schedule import ScheduleCalc


class TabFollowers(ttk.Frame):
    def __init__(self, window):
        super().__init__(window)

        self.headerFont = tkfont.Font(family="Helvetica", size=12, weight='bold')
        self.titleFont = tkfont.Font(family="Helvetica", size=9)
        self.h3 = tkfont.Font(family="Helvetica", size=11, weight='bold')
        self.bold = tkfont.Font(weight='bold', size=10)
        self.results = tkfont.Font(size=11, weight='bold')
        self.check_box_reverse = IntVar()
        self.limit_unfollow_everyone = IntVar()
        self.remove_not_found_user = BooleanVar()
        self.limit_unfollow_list = IntVar()
        self.minutes_entry_value = IntVar()
        self.hours_entry_value = IntVar()
        self.days_entry_value = IntVar()
        self.check_box_schedule = IntVar()
        self.radio_var = IntVar()
        self.username = StringVar()
        self.password = StringVar()
        self.menu = StringVar()
        self.amount_not_following = 0
        self.amount_unfollow_users = 0
        self.proxy = StringVar()
        self.port = StringVar()
        self.MINUTES = 0
        self.HOURS = 1
        self.DAYS = 2

        self.check_box_reverse.set(0)
        self.accounts = db.Database().get_accounts()
        user_name_list = []
        for account in self.accounts:
            user_name_list.append(account[3])

        ttk.Label(self, text='Check which users you follow don\'t follow you back', font=self.headerFont)\
                                                                        .grid(column=0, row=0, padx=10, pady=(5, 0))
        # Users menu
        ttk.Label(self, text='Choose user', font=self.titleFont).grid(column=0, row=1, padx=10)
        if len(user_name_list) > 0:
            ttk.OptionMenu(self, self.menu, user_name_list[0], *user_name_list,
                       command=self._set_username_password).grid(column=0, row=2)
        else:
            ttk.Label(self, text='No Users, go to Accounts', font=self.titleFont).grid(column=0, row=2, padx=10, pady=10)

        # username and password form
        ttk.Label(self, text='username:', font=self.bold).grid(column=0, row=3, rowspan=1, padx=10, pady=0, sticky='w')
        ttk.Entry(self, textvariable=self.username, width=30, show='*').grid(column=0, row=3, rowspan=1)
        ttk.Label(self, text='password:', font=self.bold).grid(column=0, row=4, rowspan=1, padx=10, pady=0, sticky='w')
        ttk.Entry(self, textvariable=self.password, width=30, show='*').grid(column=0, row=4, rowspan=1)
        ttk.Button(self, text="RUN", command=self._check_form).grid(column=0, row=5)

        # box list display all users that the account has followed them
        self.unfollow_title = ttk.Label(self, text='You are following {}'.format(self.amount_not_following), font=self.bold)
        self.unfollow_title.grid(column=0, row=6, pady=20)
        self.unfollow_users_list_box = Listbox(self, width=25, height=16)
        self.unfollow_users_list_box.grid(column=0, row=7, rowspan=3)
        ttk.Button(self, text="REMOVE", command=self._remove_from_unfollow_list).grid(column=0, row=11, rowspan=1, pady=(10, 0))
        ttk.Button(self, text="UNFOLLOW LIST", command=lambda: self._unfollow_users_list(self.unfollow_users, 1))\
            .grid(column=0, columnspan=2, row=11, pady=(10, 0), padx=(0, 270))
        ttk.Button(self, text="UNFOLLOW USER", command=self._unfollow_user)\
            .grid(column=0, columnspan=2, row=11, pady=(10, 0), padx=(160, 0))
        ttk.Label(self, text="Limit unfollowers").grid(column=1, columnspan=2, row=11, pady=(10, 0), padx=(0, 0))
        ttk.Entry(self, textvariable=self.limit_unfollow_list).grid(column=1, columnspan=2, row=12, pady=(10, 0), padx=(0, 0))
        ttk.Label(self, text='unfollow users that are not following back from the above list').grid(column=0, row=12, pady=(10, 5))
        ttk.Button(self, text="REMOVE UNFOLLOWERS USERS", command=lambda: self._remove_users_who_not_follow_back(self.unfollow_users)).grid(column=0, row=13, padx=(15, 0), pady=(10, 0))

        ttk.Checkbutton(self, text='Remove not found users?', variable=self.remove_not_found_user).grid(column=2, columnspan=2,rowspan=2, row=8, padx=(0, 160))
        ttk.Checkbutton(self, text='To reverse?', variable=self.check_box_reverse).grid(column=2, columnspan=2, row=9, padx=(0, 230))
        # Schedule Button
        ttk.Checkbutton(self, text='Schedule action', variable=self.check_box_schedule) \
            .grid(column=2, columnspan=2, rowspan=2, row=9, pady=(75, 0), padx=(1, 200))

        # box list display all the names of people that are not following you back
        ttk.Label(self, text='Search results:', font=self.titleFont).grid(column=3, row=1)
        self.listbox = Listbox(self, width=30, height=13)
        self.listbox.grid(column=3, rowspan=5, row=2)

        ttk.Button(self, text="SEARCH", command=self._search_user).grid(column=3, row=5, rowspan=3, pady=(8, 8))

        # right side - unfollow all users in list box
        schedule_frame = ttk.LabelFrame(self, text='UNFOLLOW EVERYONE')
        schedule_frame.grid(column=4, row=1, ipady=50, rowspan=2, padx=40)
        title = Label(schedule_frame, text="By click this button, the program will go to your 'following' list "
                                           "and will unfollow all of them",
                      bg='gray23', font=self.bold, fg='gray67')
        limit_title = Label(schedule_frame, text="limit unfollowers", bg='gray23', font=self.bold, fg='gray67')
        limit_entry_box = ttk.Entry(schedule_frame, textvariable=self.limit_unfollow_everyone)
        unfollow_btn = ttk.Button(schedule_frame, text="UNFOLLOW", command=self._unfollow_all_users_account_follow_them)
        title.pack(fill=X)
        limit_title.place(relx=0.2, rely=0.45)
        limit_entry_box.place(relx=0.4, rely=0.45)
        unfollow_btn.place(relx=0.35, rely=0.7)

        # Proxy section
        proxy_frame = ttk.LabelFrame(self, text='Proxy')
        proxy_frame.grid(column=4, row=3, rowspan=2, ipadx=40, ipady=10, padx=(30, 0))
        entry_frame = ttk.Frame(proxy_frame)
        self.proxy_entry = ttk.Entry(entry_frame, textvariable=self.proxy, width=20)
        self.port_entry = ttk.Entry(entry_frame, textvariable=self.port)
        self.proxy_entry.pack(side=LEFT)
        self.port_entry.pack(side=LEFT)
        entry_frame.pack(side=LEFT, pady=(50, 0))

        # Schedule Actions
        schedule_frame = ttk.LabelFrame(self, text='Schedule Action')
        schedule_frame.grid(column=4, row=6, rowspan=2, ipadx=25, ipady=10, padx=(30, 0))
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

    def _check_form(self):
        username = self.username.get()
        password = self.password.get()
        proxy = self.proxy.get()
        port = self.port.get()
        proxy_dict = {"proxy": proxy, "port": port}

        if username == '' or password == '':
            messagebox.showerror('Credentials', 'Please enter your username or password')
            return False
        else:
            users_list = []
            self.amount_not_following = 0
            self.bot = FollowersBot(username, password, False, proxy_dict)
            # TODO: write thread that return's data
            # que = queue.Queue()
            # t = threading.Thread(target=self.bot.get_unfollowers, args=(que))
            # t.start()
            users_list = self.bot.get_unfollowers()
            if users_list:
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
                    ttk.Button(self, text="Click here", command=lambda: self._unfollow_users_list(users_list, 0))\
                                                        .grid(column=3, row=10, rowspan=2, pady=(8, 8))

                return True
            else:
                ttk.Label(self, text='It did not worked, run it again', font=self.results) \
                    .grid(column=3, row=6, rowspan=2, pady=(8, 8))

    # open selected user instagram page
    def _search_user(self):
        name_selection = self.listbox.get(self.listbox.curselection())
        if name_selection:
            self.bot._nav_user(name_selection)

    def _unfollow_user(self):
        name_selection = self.unfollow_users_list_box.get(self.unfollow_users_list_box.curselection())
        if name_selection:
            username = self.username.get()
            password = self.password.get()
            proxy = self.proxy.get()
            port = self.port.get()
            proxy_dict = {"proxy": proxy, "port": port}
            if self.accounts:
                for account in self.accounts:
                    if account[3] == username:
                        account_id = account[0]
            bot = FollowersBot(username, password, False, proxy_dict)
            t = threading.Thread(target=bot.unfollow_user, args=(name_selection, account_id))
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

    def _unfollow_users_list(self, user_list, is_unfollow_list):
        to_delete = messagebox.askyesno('UNFOLLOW', 'Are you sure you want to UNFOLLOW them?')
        if to_delete:
            users_name_list = []
            if is_unfollow_list:
                for username in user_list:
                    users_name_list.append(username[2])
            else:
                for username in user_list:
                    users_name_list.append(username)

            remove_not_found_users = self.remove_not_found_user.get()
            limit_unfollow_list = self.limit_unfollow_list.get()
            to_reverse = self.check_box_reverse.get()
            action = self.radio_var.get()
            schedule_action = self.check_box_schedule.get()
            minutes_entry = self.minutes_entry_value.get()
            hours_entry = self.hours_entry_value.get()
            days_entry = self.days_entry_value.get()
            username = self.username.get()
            password = self.password.get()
            proxy = self.proxy.get()
            port = self.port.get()

            proxy_dict = {"proxy": proxy, "port": port}
            bot = FollowersBot(username, password, False, proxy_dict)
            account_id = -1
            # check if the list is not empty and getting the account id
            if self.accounts:
                for account in self.accounts:
                    if account[3] == username:
                        account_id = account[0]
            if schedule_action:
                time_schedule = ScheduleCalc().calc_schedule_time(action, minutes_entry, hours_entry, days_entry)
                timing_thread = threading.Timer(time_schedule, bot.unfollow_users, [users_name_list, is_unfollow_list, account_id, 1, to_reverse, limit_unfollow_list, remove_not_found_users])
                timing_thread.start()
            else:
                t = threading.Thread(target=bot.unfollow_users, args=(users_name_list, is_unfollow_list, account_id, 1, to_reverse, limit_unfollow_list, remove_not_found_users))
                t.start()

    def _unfollow_all_users_account_follow_them(self):
        to_delete = messagebox.askyesno('UNFOLLOW', 'Are you sure you want to UNFOLLOW all of them?')
        if to_delete:
            username = self.username.get()
            password = self.password.get()
            limit_unfollowers = self.limit_unfollow_everyone.get()
            action = self.radio_var.get()
            schedule_action = self.check_box_schedule.get()
            minutes_entry = self.minutes_entry_value.get()
            hours_entry = self.hours_entry_value.get()
            days_entry = self.days_entry_value.get()
            proxy = self.proxy.get()
            port = self.port.get()
            proxy_dict = {"proxy": proxy, "port": port}
            if not username and not password:
                messagebox.showerror('Credentials', 'Please enter your username or password')
            else:
                bot = FollowersBot(username, password, False, proxy_dict)
                if schedule_action:
                    time_schedule = ScheduleCalc().calc_schedule_time(action, minutes_entry, hours_entry, days_entry)
                    timing_thread = threading.Timer(time_schedule, bot.unfollow_all_users, [limit_unfollowers])
                    timing_thread.start()
                else:
                    t = threading.Thread(target=bot.unfollow_all_users, args=[limit_unfollowers])
                    t.start()

    def _remove_from_unfollow_list(self):
        name_selection = self.unfollow_users_list_box.get(self.unfollow_users_list_box.curselection())
        account_id = -1
        # check if the list is not empty and getting the account id
        account_id = self._get_account_id()
        if name_selection:
            index = self.unfollow_users_list_box.get(0, END).index(name_selection)
            self.unfollow_users_list_box.delete(index)
            db.Database().remove_username_from_unfollow_list(name_selection, account_id)

    def _get_account_id(self):
        if self.accounts:
            for account in self.accounts:
                if account[3] == self.username.get():
                    return account[0]
        else: return -1

    def _remove_users_who_not_follow_back(self, unfollow_list):
        to_delete = messagebox.askyesno('UNFOLLOW', 'Are you sure you want to UNFOLLOW them?')
        if to_delete:
            users_name_list = []
            for username in unfollow_list:
                users_name_list.append(username[2])
            limit_unfollow_list = self.limit_unfollow_list.get()
            to_reverse = self.check_box_reverse.get()
            action = self.radio_var.get()
            schedule_action = self.check_box_schedule.get()
            minutes_entry = self.minutes_entry_value.get()
            hours_entry = self.hours_entry_value.get()
            days_entry = self.days_entry_value.get()
            account_id = self._get_account_id()
            username = self.username.get()
            password = self.password.get()
            proxy = self.proxy.get()
            port = self.port.get()
            proxy_dict = {"proxy": proxy, "port": port}
            bot = FollowersBot(username, password, False, proxy_dict)

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(bot.unfollow_users_who_not_return_follow, users_name_list, account_id, to_reverse)
                unfollow_users_list = future.result()

            bot = FollowersBot(username, password, False, proxy_dict)
            if schedule_action:
                time_schedule = ScheduleCalc().calc_schedule_time(action, minutes_entry, hours_entry, days_entry)
                timing_thread = threading.Timer(time_schedule, bot.unfollow_users, [unfollow_users_list, 1, account_id, 1, to_reverse, limit_unfollow_list])
                timing_thread.start()
            else:
                t = threading.Thread(target=bot.unfollow_users, args=(unfollow_users_list, 1, account_id, 1, to_reverse, limit_unfollow_list))
                t.start()

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
