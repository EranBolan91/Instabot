from tkinter import *
from tkinter import ttk, messagebox
import tkinter.font as tkfont
from bot_folder.strategy.strategy_bot import StrategyBot
import threading
from database import db

class StrategyTab(ttk.Frame):
    def __init__(self, window, clients, proxy_manager):
        super().__init__(window)

        self.__clients = clients
        self.__proxy_manager = proxy_manager

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

        ttk.Label(self, text='Combination - Follow after user who liked post', font=self.headerFont) \
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
        # Input of amount for likes and follow
        ttk.Label(self, text='Enter the number of posts to like').grid(
            column=0, row=7, pady=(50, 0))
        ttk.Entry(self, textvariable=self.amount_likes).grid(
            column=0, row=8, pady=(25, 0))

        # Run the script button
        ttk.Button(self, text="RUN", command=self._run_script).grid(
            column=0, columnspan=2, row=10, pady=(40, 0), padx=(20, 0))

    def _run_script(self):
        username = self.username.get()
        password = self.password.get()
        like = self.amount_likes.get()
        hash_tag = self.hashtag.get()
        url = self.url.get()

        valid = self._check_form(
            username, password, hash_tag, url, like)

        if valid:
            try:
                peoxy_username = self.__proxy_manager.add_user(username)
            except Exception as e:
                messagebox.showerror('', e)
                return

            proxy = db.Database().get_proxy_data_by_username(peoxy_username)
            proxy_dict = {'host': proxy[1], 'port': proxy[-1], 'user': proxy[2], 'password': proxy[3]}

            bot = StrategyBot(username, password, False, proxy_dict)
            t = threading.Thread(target=bot.strategy, args=(
                hash_tag, url, like, self.__clients, self.__proxy_manager))
            t.start()
            self.__clients[username] = 'running'

    # Getting the username from the menu option, look for it on the list and sets username and password
    def _set_username_password(self, value):
        self.groups_list = []
        for account in self.accounts:
            if value == account[3]:
                self.username.set(account[3])
                self.password.set(account[4])

    def _check_form(self, username, password, hash_tag, url, likes):
        if username == '' or password == '':
            messagebox.showerror(
                'Credentials', 'Please enter your username or password')
            return False

        if not hash_tag and not url:
            messagebox.showerror(
                'Search data', 'Hash tag and url entry cannot be empty')
            return False

        if likes < 0:
            messagebox.showerror('Invalid number', 'Please enter number for likes')
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
            ttk.Label(self, text='No Users, go to Accounts', font=self.titleFont) \
                .grid(column=1, row=2, padx=10, pady=10)

    def _get_proxies(self):
        self.proxies = db.Database().get_proxy_data()
        proxy_list = []

        self.proxy_option_menu = ttk.OptionMenu(self, self.proxy_menu, proxy_list[0], *proxy_list,
                                                command="")
        self.proxy_option_menu.grid(column=2, row=2)

        menu = self.proxy_option_menu['menu']

        menu.delete(0, 'end')
        for proxy in self.proxies:
            menu.add_command(label=proxy[2], command="")
            proxy_list.append(proxy[2])

        if len(proxy_list) > 0:
            self.proxy_option_menu = ttk.OptionMenu(self, self.proxy_menu, proxy_list[0], *proxy_list,
                                                    command="")
            self.proxy_option_menu.grid(column=2, row=2)
        else:
            ttk.Label(self, text='No proxies, go to Settings', font=self.titleFont) \
                .grid(column=2, row=2, padx=10, pady=10)
