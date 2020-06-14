from tkinter import *
from tkinter import ttk, messagebox
import tkinter.font as tkfont
from database import db
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
        self.direct_message = StringVar()
        self.groups_list = []
        self.check_box_distribution_list = IntVar()
        self.distribution_menu_var = StringVar()
        self.minutes_entry_value = IntVar()
        self.hours_entry_value = IntVar()
        self.days_entry_value = IntVar()
        self.check_box_schedule = IntVar()
        self.radio_var = IntVar()
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

        # Run the script button
        ttk.Button(self, text="SEND", command=self._run_script).grid(column=0, row=6, pady=16)

        # Display distribution users box
        self.listbox = Listbox(self, width=25, height=15)
        self.listbox.grid(column=2, row=3, rowspan=4, padx=(10, 0))
        self.title_amount_users_list = ttk.Label(self, text="{} Users".format(self.num_distribution_users), font=self.h3)
        self.title_amount_users_list.grid(column=2, row=7, pady=(10, 0))

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

        valid = self._check_form(username, password, message_text, group_name)

        if valid:
            if schedule_action:
                dm_users_list = db.Database().get_users_from_dm_users(group_name)
                time_schedule = ScheduleCalc().calc_schedule_time(action, minutes_entry, hours_entry, days_entry)
                print(time_schedule)
                bot = DM(username, password)
                timing_thread = threading.Timer(time_schedule, bot.send_message_to_distribution_group,
                                                                                          [message_text, dm_users_list])
                timing_thread.start()
            else:
                dm_users_list = db.Database().get_users_from_dm_users(group_name)
                bot = DM(username, password)
                t = threading.Thread(target=bot.send_message_to_distribution_group, args=(message_text, dm_users_list))
                t.start()

    def _check_form(self, username, password, message, group_name):
        if username == '' or password == '':
            messagebox.showerror('Credentials', 'Please enter your username or password')
            return False

        if message == '':
            messagebox.showerror('Message box', 'Message box cannot be empty')
            return False

        if not group_name:
            messagebox.showerror('Distribution list', 'Must choose distribution list')
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
                else:
                    self.distribution_title.grid(column=1, row=3, rowspan=3)
                    self.distribution_menu.grid_forget()

    # Getting name of distribution from distribution menu list, to set all its users in boxlist
    def _display_users_to_boxlist(self, value):
        distribution_users = db.Database().get_users_from_dm_users(value)
        self.listbox.delete(0, 'end')
        self.num_distribution_users = 0
        for user in distribution_users:
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