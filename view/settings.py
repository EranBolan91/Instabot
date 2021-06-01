from tkinter import *
from tkinter import ttk, messagebox
import tkinter.font as tkfont
from database import db
from database.proxy.proxy import Proxy
from models.proxy import Proxy


class Settings:
    def __init__(self, window):
        self.window = window
        self.likes_amount = IntVar()
        self.followers_amount_input = IntVar()
        self.check_schedule = IntVar()
        self.schedule_hour = IntVar()
        self.username_option = StringVar()
        self.host_entry = StringVar()
        self.proxy_username_entry = StringVar()
        self.proxy_password_entry = StringVar()
        self.proxy_port_entry = IntVar()
        self.distribution_list_name = StringVar()
        self.headerFont = tkfont.Font(family="Helvetica", size=12, weight='bold')
        self.titleFont = tkfont.Font(family="Helvetica", size=9)
        self.bold = tkfont.Font(weight='bold', size=10)
        self.amount = 0
        self.followers_amount = 0

        self.accounts = db.Database().get_accounts()
        user_name_list = []

        if self.accounts:
            for account in self.accounts:
                user_name_list.append(account[3])

        ttk.Label(self.window, text='SETTINGS ', font=self.headerFont) \
                    .grid(column=0, row=0, padx=10, pady=10)

        self.title_amount = ttk.Label(self.window, text='LIKE/FOLLOW/COMMENT posts who have more then {} likes '
                                                                    .format(self.amount), font=self.titleFont)
        self.title_amount.grid(column=0, row=1, padx=10, pady=10)
        ttk.Entry(self.window, textvariable=self.likes_amount).grid(column=0, row=2)

        self.title_followers_amount = ttk.Label(self.window, text='Follow after users that have more then {} followers'
                                      .format(self.followers_amount), font=self.titleFont)
        self.title_followers_amount.grid(column=0, row=3, padx=10, pady=10)
        ttk.Entry(self.window, textvariable=self.followers_amount_input).grid(column=0, row=4)

        # Proxy
        proxy_frame = ttk.LabelFrame(self.window, text='Proxy')
        proxy_frame.grid(column=0, row=5, ipady=120, ipadx=400, padx=10, pady=(0, 20), rowspan=2, columnspan=2)
        proxy_host_title = Label(proxy_frame, text="Host", bg='gray23', font=self.titleFont, fg='gray67')
        proxy_host_entry = ttk.Entry(proxy_frame, textvariable=self.host_entry, width=35)
        proxy_username_title = Label(proxy_frame, text="Username", bg='gray23', font=self.titleFont, fg='gray67')
        proxy_username_entry = ttk.Entry(proxy_frame, textvariable=self.proxy_username_entry, width=35)
        proxy_password_title = Label(proxy_frame, text="Password", bg='gray23', font=self.titleFont, fg='gray67')
        proxy_password_entry = ttk.Entry(proxy_frame, textvariable=self.proxy_password_entry, width=35)
        proxy_port_title = Label(proxy_frame, text="Port", bg='gray23', font=self.titleFont, fg='gray67')
        proxy_port_entry = ttk.Entry(proxy_frame, textvariable=self.proxy_port_entry)
        proxy_save_button = ttk.Button(proxy_frame, text="SAVE", width=10, command=self.save_proxy)
        proxy_remove_button = ttk.Button(proxy_frame, text="REMOVE", width=10, command=self.remove_proxy)
        self.proxy_listbox = Listbox(proxy_frame, width=30, height=13)

        proxy_host_title.place(relx=0.08, rely=0.1)
        proxy_host_entry.place(relx=0.25, rely=0.1)
        proxy_username_title.place(relx=0.08, rely=0.3)
        proxy_username_entry.place(relx=0.25, rely=0.3)
        proxy_password_title.place(relx=0.08, rely=0.5)
        proxy_password_entry.place(relx=0.25, rely=0.5)
        proxy_port_title.place(relx=0.08, rely=0.7)
        proxy_port_entry.place(relx=0.25, rely=0.7)
        proxy_save_button.place(relx=0.2, rely=0.85)
        proxy_remove_button.place(relx=0.5, rely=0.85)
        self.proxy_listbox.place(relx=0.7, rely=0.09)


        # Schedule Frame configuration
        schedule_frame = ttk.LabelFrame(self.window, text='SCHEDULE UNFOLLOW')
        schedule_frame.grid(column=1, row=1, ipady=50, rowspan=3)
        title = Label(schedule_frame, text="Schedule the time to unfollow users that you followed them",
                                                                bg='gray23', font=self.bold, fg='gray67')
        self.check_active = Checkbutton(schedule_frame, text='Active function',
                                        bg='gray23', font=self.titleFont, pady=5,
                                        padx=5, fg='gray67', command=self._activate_check, variable=self.check_schedule)

        self.spin_hours = Spinbox(schedule_frame, from_=0, to=1000, bg='gray23', state=DISABLED,
                                                        width=8, textvariable=self.schedule_hour)
        hours_label = Label(schedule_frame, text="Hours", bg='gray23', fg='gray67')

        self.current_hours = Label(schedule_frame, text="HOURS:", bg='gray23', fg='gray67')

        title.pack(fill=X)
        self.check_active.place(anchor=NW, relx=0, rely=0.4)
        self.spin_hours.place(anchor=N, relx=0.4, rely=0.4)
        hours_label.place(anchor=N, relx=0.55, rely=0.4)
        self.current_hours.place(relx=0, rely=0.8)

        ttk.Button(self.window, text="SAVE CHANGES", command=self._save_changes, width=30)\
                                        .grid(column=0, columnspan=4, row=4, pady=15)

        # Distribution list for DM
        distribution_list = ttk.LabelFrame(self.window, text='Distribution list')
        distribution_list.grid(column=2, row=1, ipady=120, ipadx=50, padx=20, rowspan=4)
        title = Label(distribution_list, text="Create distribution lists to DM them ", bg='gray23', font=self.bold, fg='gray67')
        self.listbox = Listbox(distribution_list, width=20, height=10)
        list_name = Label(distribution_list, text="Enter list name ", bg='gray23', fg='gray67')
        input_list_name = ttk.Entry(distribution_list, textvariable=self.distribution_list_name)
        add_btn = ttk.Button(distribution_list, text="ADD", width=10, command=self._save_distribution_list)
        remove_btn = ttk.Button(distribution_list, text="REMOVE", width=10, command=self._remove_group_from_distribution_list)
        username_choose_title = Label(distribution_list, text="Please choose a username", bg='gray23', fg='gray67')

        title.pack(fill=X)
        list_name.place(relx=0.0, rely=0.2)
        input_list_name.place(relx=0.0, rely=0.3)
        username_choose_title.place(relx=0.0, rely=0.5)
        self.listbox.place(relx=0.6, rely=0.2)
        add_btn.place(relx=0.6, rely=0.9)
        remove_btn.place(relx=0.2, rely=0.9)

        if user_name_list:
            users_list_option = ttk.OptionMenu(distribution_list, self.username_option, user_name_list[0], *user_name_list, command=self._set_users_groups)
            users_list_option.place(relx=0.0, rely=0.6)
        else:
            users_lists_label = ttk.Label(distribution_list, text='No Accounts')
            users_lists_label.place(relx=0.0, rely=0.6)


        # Init data
        self._settings_data()

    def _settings_data(self):
        self.database = db.Database()
        data_settings = self.database.get_data_from_settings()
        # Init the box list of distribution groups
        username_menu = self.username_option.get()
        if username_menu:
            distribution_groups = self.database.get_distribution_lists_by_username(username_menu)
            for group in distribution_groups:
                self.listbox.insert(END, group[1])

        # This 'if' because when i run for the first time the program,
        # there is no 'data settings' - its empty. so i init it with 0
        if data_settings == '' or data_settings is None:
            self.amount = 0
            self.followers_amount = 0
            self.check_schedule.set(0)
            self.current_hours['text'] = "HOURS: {}".format(0)
            self.database.save_settings(0, 0, 0, 0)
        else:
            self.amount = data_settings[1]
            self.followers_amount = data_settings[2]
            self.check_schedule.set(data_settings[3])
            self.current_hours['text'] = "HOURS: {}".format(data_settings[4])

        # Set the CheckButton
        self.title_amount['text'] = 'LIKE/FOLLOW/COMMENT users who has more then {} likes'.format(self.amount)
        self.title_followers_amount['text'] = 'Follow after users that have more then {} followers'.format(self.followers_amount)
        self._activate_check()

    def _save_changes(self):
        database = db.Database()
        likes_amount = self.likes_amount.get()
        followers_amount = self.followers_amount_input.get()
        schedule_hour = self.schedule_hour.get()
        is_schedule = self.check_schedule.get()
        data = database.get_data_from_settings()
        update_likes_amount = data[1]
        update_followers_amount = data[2]
        update_is_schedule = data[3]
        update_schedule_hour = data[4]

        if likes_amount != 0 and likes_amount > 0:
            update_likes_amount = likes_amount
        if followers_amount != 0 and followers_amount > 0:
            update_followers_amount = followers_amount
        if schedule_hour != 0 and schedule_hour > 0:
            update_schedule_hour = schedule_hour
        if is_schedule != 0 and is_schedule > 0:
            update_is_schedule = is_schedule

        database.save_settings(update_likes_amount, update_followers_amount, update_is_schedule, update_schedule_hour)
        messagebox.showinfo('Settings', 'Changes has been saved')
        self.likes_amount.set(0)
        self.followers_amount_input.set(0)
        data = database.get_data_from_settings()
        self.title_followers_amount['text'] = 'Follow after users that have more then {} followers'.format(data[2])
        self.title_amount['text'] = 'LIKE/FOLLOW/COMMENT users who has more then {} likes '.format(data[1])
        self.current_hours['text'] = "HOURS: {}".format(data[3])

    def _activate_check(self):
        if self.check_schedule.get() == 1:  # whenever checked
            self.spin_hours.config(state=NORMAL)
        elif self.check_schedule.get() == 0:  # whenever unchecked
            self.spin_hours.config(state=DISABLED)

    def _save_distribution_list(self):
        list_name = self.distribution_list_name.get()
        username_menu = self.username_option.get()
        # If list name is not empty, than enter to this block (save the name list in db)
        if list_name and username_menu:
            database = db.Database()
            is_saved = database.create_distribution_group(list_name, username_menu)
            if is_saved:
                self.listbox.insert(END, list_name)
                self.distribution_list_name.set('')
            else:
                print('Did not saved')

    def _remove_group_from_distribution_list(self):
        username_menu = self.username_option.get()
        group_selection = self.listbox.get(self.listbox.curselection())
        if group_selection:
            database = db.Database()
            is_deleted = database.remove_group_from_distribution_list(group_selection, username_menu)
            if is_deleted:
                self.listbox.delete(self.listbox.curselection())

    def _set_users_groups(self, value):
        self.listbox.delete(0, 'end')
        distribution_groups = self.database.get_distribution_lists_by_username(value)
        for group in distribution_groups:
            self.listbox.insert(END, group[1])

    def save_proxy(self):
        host = self.host_entry.get()
        username = self.proxy_username_entry.get()
        password = self.proxy_password_entry.get()
        port = self.proxy_port_entry.get()
        proxy_obj = Proxy(host, username, password, port)
        Proxy().save_in_db(proxy_obj)
        print("proxy saved")

    def remove_proxy(self):
        pass