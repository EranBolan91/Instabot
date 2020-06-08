from tkinter import *
from tkinter import ttk, messagebox
import tkinter.font as tkfont
from database import db
from bot_folder.dm.dm_bot import DM
import threading


class TabDM(ttk.Frame):
    def __init__(self, window):
        super().__init__(window)

        self.headerFont = tkfont.Font(family="Helvetica", size=12, weight='bold')
        self.titleFont = tkfont.Font(family="Helvetica", size=9)
        self.h3 = tkfont.Font(family="Helvetica", size=11, weight='bold')
        self.bold = tkfont.Font(weight='bold', size=10)
        self.distribution_menu_var = StringVar()
        self.users_menu = StringVar()
        self.username = StringVar()
        self.password = StringVar()
        self.direct_message = StringVar()
        self.groups_list = []

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
            self.distribution_menu = ttk.OptionMenu(self, self.distribution_menu_var, self.groups_list[0], *self.groups_list, state='DISABLED')
            self.distribution_menu.grid(column=1, columnspan=3, row=3, rowspan=3)
        else:
            self.distribution_title = ttk.Label(self, text="Choose user to display distribution lists ", font=self.titleFont)
            self.distribution_title.grid(column=1, columnspan=3, row=3, rowspan=3)

        # Run the script button
        ttk.Button(self, text="SEND", command=self._run_script).grid(column=0, row=6, pady=16)

    def _run_script(self):
        username = self.username.get()
        password = self.password.get()
        message_text = self.text_message.get("1.0", END)
        group_name = self.distribution_menu_var.get()

        valid = self._check_form(username, password, message_text, group_name)

        if valid:
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
                            *self.groups_list)
                    self.distribution_menu.grid(column=1, columnspan=3, row=3, rowspan=3)
                    self.distribution_title.grid_forget()
                else:
                    self.distribution_title.grid(column=1, columnspan=3, row=3, rowspan=3)
                    self.distribution_menu.grid_forget()