from tkinter import *
from tkinter import ttk, messagebox
import tkinter.font as tkfont
from database.combination.combination import CombinationDM
from database import db
from bot_folder.like.like_bot import LikeBot
from utils.schedule import ScheduleCalc
import threading


class TabLikes(ttk.Frame):
    def __init__(self, window):
        super().__init__(window)

        self.dividerFont = tkfont.Font(family="Helvetica", size=25)
        self.headerFont = tkfont.Font(
            family="Helvetica", size=12, weight='bold')
        self.titleFont = tkfont.Font(family="Helvetica", size=9)
        self.h3 = tkfont.Font(family="Helvetica", size=11, weight='bold')
        self.bold = tkfont.Font(weight='bold', size=10)

        self.check_box_distribution_list = IntVar()
        self.distribution_menu_var = StringVar()
        self.check_box_schedule = IntVar()
        self.minutes_entry_value = IntVar()
        self.hours_entry_value = IntVar()
        self.days_entry_value = IntVar()
        self.amount_follows = IntVar()
        self.amount_likes = IntVar()
        self.username = StringVar()
        self.password = StringVar()
        self.skip_posts = IntVar()
        self.skip_users = IntVar()
        self.hashtag = StringVar()
        self.radio_var = IntVar()
        self.menu = StringVar()
        self.proxy_menu = StringVar()
        self.url = StringVar()
        self.groups_list = []
        self.MINUTES = 0
        self.HOURS = 1
        self.DAYS = 2

        self.check_box_distribution_list.set(0)

        self.accounts = db.Database().get_accounts()
        user_name_list = []
        for account in self.accounts:
            user_name_list.append(account[3])

        self.proxies = db.Database().get_proxy_data()
        proxies_list = []
        for proxy in self.proxies:
            proxies_list.append(proxy[2])

        ttk.Label(self, text='Likes - like photos', font=self.headerFont) \
            .grid(column=0, row=0, padx=10, pady=5)

        # username and password form
        ttk.Label(self, text='Please enter username and password', font=self.titleFont) \
            .grid(column=0, row=1, padx=10, pady=5)
        ttk.Label(self, text='username:', font=self.bold).grid(
            column=0, row=2, padx=(50, 0), pady=10, sticky='w')
        ttk.Entry(self, textvariable=self.username,
                  show='*').grid(column=0, row=2)
        ttk.Label(self, text='password:', font=self.bold).grid(
            column=0, row=3, padx=(50, 0), pady=10, sticky='w')
        ttk.Entry(self, textvariable=self.password,
                  show='*').grid(column=0, row=3)

        # Hash tag form - for example 'travel'
        ttk.Label(self, text='Enter the hash tag keyword ',
                  font=self.h3).grid(column=0, row=5, padx=10, pady=10)
        ttk.Entry(self, textvariable=self.hashtag).grid(column=0, row=6)

        # OR
        ttk.Label(self, text='<-- OR -->', font=self.dividerFont).grid(column=1,
                                                                       row=5, rowspan=2, padx=(0, 70), pady=(40, 0))

        # URL input
        ttk.Label(self, text='Enter the URL',
                  font=self.h3).grid(column=2, row=5)
        ttk.Entry(self, textvariable=self.url, width=50).grid(column=2, row=6)

        # Users menu
        ttk.Label(self, text='Choose user', font=self.titleFont).grid(
            column=1, row=1, padx=10, pady=(25, 0))
        if len(user_name_list) > 0:
            self.accounts_option_menu = ttk.OptionMenu(self, self.menu, user_name_list[0], *user_name_list,
                                                       command=self._set_username_password)
            self.accounts_option_menu.grid(column=1, row=2)
        else:
            ttk.Label(self, text='No Users, go to Accounts', font=self.titleFont) \
                .grid(column=1, row=2, padx=10, pady=10)

        ttk.Button(self, text='REFRESH LIST', compound=LEFT, command=self._get_accounts).grid(column=1, row=2, padx=(220, 0))

        # Proxy section
        ttk.Label(self, text='Choose proxy', font=self.titleFont).grid(column=2, row=1, padx=10, pady=(25, 0))
        if len(proxies_list) > 0:
            self.proxy_option_menu = ttk.OptionMenu(self, self.proxy_menu, proxies_list[0], *proxies_list)
            self.proxy_option_menu.grid(column=2, row=2)
        else:
            ttk.Label(self, text='No proxies, go to Settings', font=self.titleFont) \
                .grid(column=2, row=2, padx=10, pady=10)

        ttk.Button(self, text='REFRESH PROXY', compound=LEFT, command=self._get_proxies).grid(column=2, columnspan=3,
                                                                                                row=2, padx=(0, 0))

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
        ttk.Label(self, text='Enter the number of posts to like').grid(
            column=0, row=7, pady=(50, 0))
        ttk.Entry(self, textvariable=self.amount_likes).grid(
            column=0, row=8, pady=(25, 0))

        ttk.Label(self, text='Skip posts').grid(column=2, row=7, pady=(50, 0))
        ttk.Entry(self, textvariable=self.skip_posts).grid(
            column=2, row=8, pady=(25, 0))

        # Run the script button
        ttk.Button(self, text="RUN", command=self._run_script).grid(
            column=0, columnspan=2, row=10, pady=(40, 0), padx=(20, 0))
        # Schedule Button
        ttk.Checkbutton(self, text='Schedule action', variable=self.check_box_schedule) \
            .grid(column=0, columnspan=2, rowspan=2, row=11, pady=(20, 0), padx=(1, 1))


        # Schedule Actions
        schedule_frame = ttk.LabelFrame(self, text='Schedule Action')
        schedule_frame.grid(column=3, row=4, rowspan=2,
                            ipadx=25, ipady=10, padx=(30, 0))
        entry_frame = ttk.Frame(schedule_frame)
        radio_min = ttk.Radiobutton(schedule_frame, text='Minuts', variable=self.radio_var, value=self.MINUTES,
                                    command=self._enable_entry)
        radio_hours = ttk.Radiobutton(schedule_frame, text='Hours', variable=self.radio_var, value=self.HOURS,
                                      command=self._enable_entry)
        radio_days = ttk.Radiobutton(schedule_frame, text='Days', variable=self.radio_var, value=self.DAYS,
                                     command=self._enable_entry)
        self.minutes_entry = ttk.Entry(
            entry_frame, textvariable=self.minutes_entry_value)
        self.hours_entry = ttk.Entry(
            entry_frame, textvariable=self.hours_entry_value, state='disabled')
        self.days_entry = ttk.Entry(
            entry_frame, textvariable=self.days_entry_value, state='disabled')
        radio_min.place(relx=0.08, rely=0)
        radio_hours.place(relx=0.34, rely=0)
        radio_days.place(relx=0.6, rely=0)
        self.minutes_entry.pack(side=LEFT)
        self.hours_entry.pack(side=LEFT)
        self.days_entry.pack(side=LEFT)
        entry_frame.pack(side=LEFT, pady=(50, 0))

        # Users data box - right side
        ttk.Label(self, text='User data', font=self.headerFont).grid(
            column=3, row=5, rowspan=3, padx=(0, 50), pady=(50, 0))
        data_frame = ttk.Frame(self)
        data_frame.grid(column=3, row=6, rowspan=4, padx=0, pady=(70, 0))
        scrollbary = ttk.Scrollbar(data_frame)
        scrollbarx = ttk.Scrollbar(data_frame, orient=HORIZONTAL)
        scrollbary.pack(side=RIGHT, fill=Y)
        scrollbarx.pack(side=BOTTOM, fill=X)
        self.data_frame_box = Listbox(data_frame, width=70, height=10,
                                      yscrollcommand=scrollbary.set, xscrollcommand=scrollbarx.set)
        self.data_frame_box.pack()

    def _run_script(self):
        username = self.username.get()
        password = self.password.get()
        like = self.amount_likes.get()
        hash_tag = self.hashtag.get()
        url = self.url.get()
        skip_posts = self.skip_posts.get()
        action = self.radio_var.get()
        schedule_action = self.check_box_schedule.get()
        minutes_entry = self.minutes_entry_value.get()
        hours_entry = self.hours_entry_value.get()
        days_entry = self.days_entry_value.get()
        proxy_menu = self.proxy_menu.get()
        proxy = db.Database().get_proxy_data_by_username(proxy_menu)
        proxy_dict = {'host': proxy[1], 'port': proxy[-1], 'user': proxy[2], 'password': proxy[3]}

        valid = self._check_form(
            username, password, hash_tag, url, like)

        if valid:
            bot = LikeBot(username, password, False, proxy_dict)
            if schedule_action:
                time_schedule = ScheduleCalc().calc_schedule_time(
                    action, minutes_entry, hours_entry, days_entry)
                timing_thread = threading.Timer(time_schedule, bot.like(), [
                                                hash_tag, url, like, skip_posts])
                timing_thread.start()
            else:
                t = threading.Thread(target=bot.like, args=(
                    hash_tag, url, like, skip_posts))
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
                    #self.distribution_menu.grid_forget()
                self._get_account_data_for_data_box(account[3])

    def _check_form(self, username, password, hash_tag, url, likes):
        if username == '' or password == '':
            messagebox.showerror(
                'Credentials', 'Please enter your username or password')
            return False

        if not hash_tag and not url:
            messagebox.showerror(
                'Search data', 'Hash tag and url entry cannot be empty')
            return False

        if likes <= 0:
            messagebox.showerror('Invalid number of likes', 'Please enter number for likes')
            return False

        if url and hash_tag:
            messagebox.showerror(
                'Too many arguments', 'You can choose only one action! HASHTAG or URL')
            return False

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

    def _get_account_data_for_data_box(self, account_name):
        account_data = CombinationDM().get_account_data(account_name)
        self.data_frame_box.delete(0, 'end')
        for data in account_data:
            box = """ Date: {} | Follow: {} | Failed Follow: {} | Skip: {} | URL: {} """.format(
                data[11], data[6], data[5], data[12], data[2],)
            self.data_frame_box.insert(END, box)

    def _get_accounts(self):
        self.accounts = db.Database().get_accounts()
        user_name_list = []
        menu = self.accounts_option_menu['menu']
        menu.delete(0, 'end')
        for account in self.accounts:
            menu.add_command(label=account[3], command=self._set_username_password)
            user_name_list.append(account[3])

        if len(user_name_list) > 0:
            self.accounts_option_menu = ttk.OptionMenu(self, self.menu, user_name_list[0], *user_name_list,
                       command=self._set_username_password)
            self.accounts_option_menu.grid(column=1, row=2)
        else:
            ttk.Label(self, text='No Users, go to Accounts', font=self.titleFont)\
                .grid(column=1, row=2, padx=10, pady=10)

    def _get_proxies(self):
        self.proxies = db.Database().get_proxy_data()
        proxy_list = []
        try:
            menu = self.proxy_option_menu['menu']
        except Exception:
            self.proxy_option_menu = ttk.OptionMenu(self, self.proxy_menu, proxy_list[0], *proxy_list,
                       command="")
            self.proxy_option_menu.grid(column=2, row=2)

        menu.delete(0, 'end')
        for proxy in self.proxies:
            menu.add_command(label=proxy[2], command="")
            proxy_list.append(proxy[2])

        if len(proxy_list) > 0:
            self.proxy_option_menu = ttk.OptionMenu(self, self.proxy_menu, proxy_list[0], *proxy_list,
                       command="")
            self.proxy_option_menu.grid(column=2, row=2)
        else:
            ttk.Label(self, text='No proxies, go to Settings', font=self.titleFont)\
                .grid(column=2, row=2, padx=10, pady=10)
