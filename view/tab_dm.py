from tkinter import *
from tkinter import ttk, messagebox
import tkinter.font as tkfont
from database import db
from database.dm import dm
from bot_folder.dm.dm_bot import DM
from utils.schedule import ScheduleCalc
import threading


class TabDM(ttk.Frame):
    def __init__(self, window):
        super().__init__(window)

        self.headerFont = tkfont.Font(family="Helvetica", size=12, weight='bold')
        self.titleFont = tkfont.Font(family="Helvetica", size=9)
        self.h3 = tkfont.Font(family="Helvetica", size=11, weight='bold')
        self.bold = tkfont.Font(weight='bold', size=10)
        self.distribution_menu_var = StringVar()
        self.num_distribution_users = 0
        self.users_menu = StringVar()
        self.username = StringVar()
        self.password = StringVar()
        self.groups_list = []
        self.check_box_distribution_list = IntVar()
        self.distribution_menu_var = StringVar()
        self.minutes_entry_value = IntVar()
        self.hours_entry_value = IntVar()
        self.days_entry_value = IntVar()
        self.check_box_schedule = IntVar()
        self.limit_msg = IntVar()
        self.radio_var = IntVar()
        self.proxy = StringVar()
        self.port = StringVar()
        self.MINUTES = 0
        self.HOURS = 1
        self.DAYS = 2

        self.check_box_schedule.set(0)
        self.accounts = db.Database().get_accounts()
        user_name_list = []
        for account in self.accounts:
            user_name_list.append(account[3])

        ttk.Label(self, text='Send direct messages to distribution groups', font=self.headerFont)\
                 .grid(column=0, row=0, padx=10, pady=10)

        # username and password form
        ttk.Label(self, text='Please enter username and password', font=self.titleFont)\
            .grid(column=0, row=1, padx=10, pady=10)
        ttk.Label(self, text='username:', font=self.bold).grid(column=0, row=2, padx=10, pady=10, sticky='w')
        ttk.Entry(self, textvariable=self.username, show='*').grid(column=0, row=2)
        ttk.Label(self, text='password:', font=self.bold).grid(column=0, row=3, padx=10, pady=10, sticky='w')
        ttk.Entry(self, textvariable=self.password, show='*').grid(column=0, row=3)

        ttk.Label(self, text='Choose user', font=self.titleFont).grid(column=1, row=1, padx=10, pady=10)
        if len(user_name_list) > 0:
            ttk.OptionMenu(self, self.users_menu, user_name_list[0], *user_name_list,
                       command=self._set_username_password).grid(column=1, row=2)
        else:
            ttk.Label(self, text='No Users, go to Accounts', font=self.titleFont)\
                .grid(column=1, row=2, padx=10, pady=10)

        # Direct Messages
        ttk.Label(self, text='Type your message', font=self.titleFont).grid(column=0, row=4, padx=10, pady=10)
        self.text_message = Text(self, height=7, width=50)
        self.text_message.grid(column=0, row=5, padx=20)

        # Groups distribution
        # If there are groups, it will display them. Else it will display message
        if len(self.groups_list) > 0:
            self.distribution_menu = ttk.OptionMenu(self, self.distribution_menu_var, self.groups_list[0],
                                *self.groups_list, command=self._display_users_to_boxlist)
            self.distribution_menu.grid(column=1, row=3, rowspan=3)
        else:
            self.distribution_title = ttk.Label(self, text="Choose user to display distribution lists ", font=self.titleFont)
            self.distribution_title.grid(column=1, row=3, rowspan=3)

        ttk.Label(self, text='Limit messages', font=self.bold).grid(column=0, row=6, pady=16)
        ttk.Entry(self, textvariable=self.limit_msg).grid(column=0, row=7, pady=8)

        # Run the script button
        ttk.Button(self, text="SEND", command=self._run_script).grid(column=0, row=8, pady=16)

        # Display distribution users box
        self.listbox = Listbox(self, width=25, height=15)
        self.listbox.grid(column=2, row=3, rowspan=4, padx=(10, 0))
        self.title_amount_users_list = ttk.Label(self, text="{} Users".format(self.num_distribution_users), font=self.h3)
        self.title_amount_users_list.grid(column=2, row=7, pady=(10, 0))
        ttk.Button(self, text="CLEAR LIST", command=lambda: self._remove_all_dm_list(self.distribution_users))\
            .grid(column=2, row=8, padx=(0, 100), pady=(10, 0))
        ttk.Button(self, text="REMOVE USER", command=self._remove_user).grid(column=2, row=8, padx=(150, 0), pady=(10, 0))

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

        ttk.Checkbutton(self, text='Schedule action', variable=self.check_box_schedule) \
            .grid(column=3, row=4, pady=10, padx=20)

        # Send messages to the current user's followers
        message_frame = ttk.LabelFrame(self, text='Messages to current following account')
        message_frame.grid(column=3, row=5, rowspan=4, ipady=120, ipadx=200, pady=(20, 0))
        ttk.Label(message_frame, text='Write your message and send it to all your following list').place(relx=0.1, rely=0.1)
        self.text_message_current_account = Text(message_frame, height=7, width=40)
        self.text_message_current_account.place(relx=0.1, rely=0.2)
        ttk.Button(message_frame, text="SEND", command=self._send_msgs_current_account_following).place(relx=0.4, rely=0.8)

        # Proxy section
        proxy_frame = ttk.LabelFrame(self, text='Proxy')
        proxy_frame.grid(column=1, row=9, columnspan=2, ipadx=40, ipady=10, padx=(30, 0))
        entry_frame = ttk.Frame(proxy_frame)
        self.proxy_entry = ttk.Entry(entry_frame, textvariable=self.proxy, width=20)
        self.port_entry = ttk.Entry(entry_frame, textvariable=self.port)
        self.proxy_entry.pack(side=LEFT)
        self.port_entry.pack(side=LEFT)
        entry_frame.pack(side=LEFT, pady=(50, 0))

    def _send_msgs_current_account_following(self):
        username = self.username.get()
        password = self.password.get()
        message_text = self.text_message_current_account.get("1.0", END)
        action = self.radio_var.get()
        schedule_action = self.check_box_schedule.get()
        minutes_entry = self.minutes_entry_value.get()
        hours_entry = self.hours_entry_value.get()
        days_entry = self.days_entry_value.get()

        valid = self._check_form(username, password, message_text)

        if valid:
            is_schedule = 0
            if schedule_action:
                is_schedule = 1
                time_schedule = ScheduleCalc().calc_schedule_time(action, minutes_entry, hours_entry, days_entry)
                bot = DM(username, password, True)
                timing_thread = threading.Timer(time_schedule, bot.send_message_to_following_list,
                                                    [message_text, is_schedule])
                timing_thread.start()
            else:
                bot = DM(username, password, True)
                t = threading.Thread(target=bot.send_message_to_following_list, args=(message_text, is_schedule))
                t.start()

    def _run_script(self):
        username = self.username.get()
        password = self.password.get()
        message_text = self.text_message.get("1.0", END)
        group_name = self.distribution_menu_var.get()
        action = self.radio_var.get()
        schedule_action = self.check_box_schedule.get()
        minutes_entry = self.minutes_entry_value.get()
        hours_entry = self.hours_entry_value.get()
        days_entry = self.days_entry_value.get()
        limit_msg = self.limit_msg.get()
        proxy = self.proxy.get()
        port = self.port.get()

        # check if the list is not empty and getting the account id
        account_id = self._get_account_id()
        group_id = self._get_group_id(group_name)
        valid = self._check_form(username, password, message_text)
        proxy_dict = {"proxy": proxy, "port": port}

        if valid:
            is_schedule = 0
            if schedule_action:
                is_schedule = 1
                dm_users_list = db.Database().get_users_from_dm_users(group_name, username)
                time_schedule = ScheduleCalc().calc_schedule_time(action, minutes_entry, hours_entry, days_entry)
                bot = DM(username, password, True, proxy_dict)
                timing_thread = threading.Timer(time_schedule, bot.send_message_to_distribution_group,
                                               [message_text, dm_users_list, group_name, is_schedule, True, account_id, group_id, limit_msg])
                timing_thread.start()
            else:
                dm_users_list = db.Database().get_users_from_dm_users(group_name, username)
                bot = DM(username, password, True, proxy_dict)
                t = threading.Thread(target=bot.send_message_to_distribution_group, args=(message_text, dm_users_list,
                                                                            group_name, is_schedule, True, account_id, group_id, limit_msg))
                t.start()

    def _check_form(self, username, password, message):
        if username == '' or password == '':
            messagebox.showerror('Credentials', 'Please enter your username or password')
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
                else:
                    self.distribution_title.grid(column=1, row=3, rowspan=3)
                    self.distribution_menu.grid_forget()

    # Getting name of distribution from distribution menu list, to set all its users in boxlist
    def _display_users_to_boxlist(self, value):
        username = self.users_menu.get()
        self.distribution_users = db.Database().get_users_from_dm_users(value, username)
        self.listbox.delete(0, 'end')
        self.num_distribution_users = 0
        for user in self.distribution_users:
            self.listbox.insert(END, user[0])
            self.num_distribution_users += 1
        self.title_amount_users_list.config(text="{} Users".format(self.num_distribution_users), font=self.h3)

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
        to_delete = messagebox.askyesno('Remove', 'Are you sure you want to REMOVE all of them?')
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