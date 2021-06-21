from tkinter import *
from tkinter import ttk, messagebox
import tkinter.font as tkfont
from database import db
from database.dm import dm
from bot_folder.dm_to_followers.dm_to_followers_bot import DMTtoFollowers
from utils.schedule import ScheduleCalc
import threading


class TabFollowersToDM(ttk.Frame):
    def __init__(self, window, proxy_manager):
        super().__init__(window)

        self.__proxy_manager = proxy_manager

        self.headerFont = tkfont.Font(
            family="Helvetica", size=12, weight='bold')
        self.titleFont = tkfont.Font(family="Helvetica", size=9)
        self.h3 = tkfont.Font(family="Helvetica", size=11, weight='bold')
        self.bold = tkfont.Font(weight='bold', size=10)

        self.users_menu = StringVar()
        self.username = StringVar()
        self.password = StringVar()
        self.limit_msg = IntVar()

        self.accounts = db.Database().get_accounts()
        user_name_list = []
        for account in self.accounts:
            user_name_list.append(account[3])

        ttk.Label(self, text='Send direct messages to distribution groups', font=self.headerFont)\
            .grid(column=0, row=0, padx=10, pady=10)

        # username and password form
        ttk.Label(self, text='Please enter username and password', font=self.titleFont)\
            .grid(column=0, row=1, padx=10, pady=10)
        ttk.Label(self, text='username:', font=self.bold).grid(
            column=0, row=2, padx=10, pady=10, sticky='w')
        ttk.Entry(self, textvariable=self.username,
                  show='*').grid(column=0, row=2)
        ttk.Label(self, text='password:', font=self.bold).grid(
            column=0, row=3, padx=10, pady=10, sticky='w')
        ttk.Entry(self, textvariable=self.password,
                  show='*').grid(column=0, row=3)

        ttk.Label(self, text='Choose user', font=self.titleFont).grid(
            column=1, row=1, padx=10, pady=10)
        if len(user_name_list) > 0:
            ttk.OptionMenu(self, self.users_menu, user_name_list[0], *user_name_list,
                           command=self._set_username_password).grid(column=1, row=2)
        else:
            ttk.Label(self, text='No Users, go to Accounts', font=self.titleFont)\
                .grid(column=1, row=2, padx=10, pady=10)

        # Direct Messages
        ttk.Label(self, text='Type your message', font=self.titleFont).grid(
            column=0, row=4, padx=10, pady=10)
        self.text_message = Text(self, height=7, width=50)
        self.text_message.grid(column=0, row=5, padx=20)

        ttk.Label(self, text='Limit messages', font=self.bold).grid(
            column=0, row=6, pady=16)
        ttk.Entry(self, textvariable=self.limit_msg).grid(
            column=0, row=7, pady=8)

        # Run the script button
        ttk.Button(self, text="SEND", command=self._run_script).grid(
            column=0, row=8, pady=16)

    def _run_script(self):
        username = self.username.get()
        password = self.password.get()
        message_text = self.text_message.get("1.0", END)
        limit_msg = self.limit_msg.get()

        valid = self._check_form(username, password, message_text)

        if valid:
            try:
                peoxy_username = self.__proxy_manager.add_user(username)
            except Exception as e:
                messagebox.showerror('', e)
                return

            proxy = db.Database().get_proxy_data_by_username(peoxy_username)
            proxy_dict = {
                'host': proxy[1], 'port': proxy[-1], 'user': proxy[2], 'password': proxy[3]}

            bot = DMTtoFollowers(username, password, False, proxy_dict)
            t = threading.Thread(
                target=bot.send_message_to_followers, args=(message_text, limit_msg))
            t.start()

    def _check_form(self, username, password, message):
        if username == '' or password == '':
            messagebox.showerror(
                'Credentials', 'Please enter your username or password')
            return False

        if message == '':
            messagebox.showerror('Message box', 'Message box cannot be empty')
            return False

        else:
            return True

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
                                                            *self.groups_list, command=self._display_users_to_boxlist)
                    self.distribution_menu.grid(column=1, row=3, rowspan=3)
                    self.distribution_title.grid_forget()
                    self.listbox.delete(0, 'end')
                    self.num_distribution_users = 0
                    self.title_amount_users_list.config(text="{} Users".format(self.num_distribution_users),
                                                        font=self.h3)

    # Getting name of distribution from distribution menu list, to set all its users in boxlist
    def _display_users_to_boxlist(self, value):
        username = self.users_menu.get()
        self.distribution_users = db.Database().get_users_from_dm_users(value, username)
        self.listbox.delete(0, 'end')
        self.num_distribution_users = 0
        for user in self.distribution_users:
            self.listbox.insert(END, user[0])
            self.num_distribution_users += 1
        self.title_amount_users_list.config(text="{} Users".format(
            self.num_distribution_users), font=self.h3)

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

    def _remove_all_dm_list(self, users_list):
        to_delete = messagebox.askyesno(
            'Remove', 'Are you sure you want to REMOVE all of them?')
        if to_delete:
            group_id = self._get_group_id(self.distribution_menu_var.get())
            for user in users_list:
                dm.DMDB().remove_dm_user_from_list(user[0], group_id)
            self.listbox.delete(0, 'end')

    def _remove_user(self):
        name_selection = self.listbox.get(self.listbox.curselection())
        index = self.listbox.get(0, END).index(name_selection)
        group_id = self._get_group_id(self.distribution_menu_var.get())
        self.listbox.delete(index)
        dm.DMDB.remove_dm_user_from_list(name_selection, group_id)

    def _get_account_id(self):
        if self.accounts:
            for account in self.accounts:
                if account[3] == self.username.get():
                    return account[0]
        else:
            return -1

    def _get_group_id(self, group_name):
        if self.distribution_list:
            for group in self.distribution_list:
                if group[1] == group_name:
                    return group[0]
        else:
            return -1
