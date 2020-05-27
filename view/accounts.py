from tkinter import *
from tkinter import ttk, messagebox
import tkinter.font as tkfont
from database.db import Database


class AccountsNew:
    def __init__(self, window):
        self.window = window
        self.username = StringVar()
        self.password = StringVar()
        self.name = StringVar()
        self.phone = StringVar()
        self.SAVE = 1
        self.UPDATE = 0

        self.headerFont = tkfont.Font(family="Helvetica", size=12, weight='bold')
        self.titleFont = tkfont.Font(family="Helvetica", size=9)
        self.h3 = tkfont.Font(family="Helvetica", size=11, weight='bold')
        self.h4 = tkfont.Font(family="Helvetica", size=10, weight='bold')
        self.bold = tkfont.Font(weight='bold', size=10)
        self.list_box_text = tkfont.Font(family="Verdana", size=11, weight='bold')

        # Add account form (left side)
        ttk.Label(self.window, text='Manage your accounts', font=self.headerFont).grid(column=0, row=0, padx=10, pady=10)
        ttk.Label(self.window, text='Add account', font=self.h3).grid(column=0, row=1, padx=10, pady=10, columnspan=2)

        register_frame = ttk.LabelFrame(self.window, text='REGISTER')
        register_frame.grid(column=0, row=2, ipady=150, ipadx=150, rowspan=3, padx=(10, 0))

        ttk.Label(register_frame, text='Name', font=self.bold).place(relx=0, rely=0.15)
        ttk.Entry(register_frame, textvariable=self.name, width=25).place(relx=0.3, rely=0.15)
        ttk.Label(register_frame, text='Phone', font=self.bold).place(relx=0, rely=0.25)
        ttk.Entry(register_frame, textvariable=self.phone, width=25).place(relx=0.3, rely=0.25)
        ttk.Label(register_frame, text='Username*', font=self.bold).place(relx=0, rely=0.35)
        ttk.Entry(register_frame, textvariable=self.username, width=25).place(relx=0.3, rely=0.35)
        ttk.Label(register_frame, text='Password*', font=self.bold).place(relx=0, rely=0.45)
        ttk.Entry(register_frame, textvariable=self.password, width=25).place(relx=0.3, rely=0.45)

        ttk.Button(register_frame, text="ADD", command=lambda: self._save(self.SAVE)).place(relx=0.4, rely=0.8)

        # Displaying accounts (right - side)
        self.accounts = self._get_accounts()
        print(self.accounts)
        ttk.Label(self.window, text='Your accounts', font=self.headerFont, width=30)\
                            .grid(column=3, columnspan=2, row=1, padx=30, pady=10, sticky=W)
        self.scroll_bar = Scrollbar(self.window, orient="vertical")
        self.list_box = Listbox(self.window, font=('Verdana', 11), width=40, height=25)
        ttk.Label(self.window, text='Accounts details', font=self.headerFont).grid(column=4, row=1, sticky=W)
        self.frame_list_box = Listbox(self.window, font=self.list_box_text, width=45, height=10)

        self.scroll_bar.grid(column=3, row=2, rowspan=4)
        self.list_box.grid(column=3, row=2, padx=20, rowspan=4)
        self.frame_list_box.grid(column=4, row=2, rowspan=2, columnspan=2, sticky=N)

        self.list_box.bind("<Double-Button-1>", self._display_content)

        self.scroll_bar.config(command=self.list_box.yview)
        self.list_box.config(yscrollcommand=self.scroll_bar.set)

        ttk.Button(self.window, text='EDIT', command=self._edit_account).grid(column=3, row=6, pady=8)
        ttk.Button(self.window, text='DELETE', command=self._delete_account).grid(column=3, columnspan=2, row=6, pady=8)
        self.update_button = ttk.Button(self.window, text='UPDATE', command=lambda: self._save(self.UPDATE), state='disabled')
        self.update_button.grid(column=1, columnspan=2, row=6, pady=8)

        if self.accounts:
            self._set_accounts(self.accounts)

    def _set_accounts(self, accounts):
        self.list_box.delete(0, END)
        for account in accounts:
            str = """Name: {}     Phone: {}    Username: {}     Password: {}  """.format(account[1], account[2],
                                                                                         account[3], account[4])
            self.list_box.insert(END, str)

    def _save(self, update_or_save):
        database = Database()
        name = self.name.get()
        phone = self.phone.get()
        username = self.username.get()
        password = self.password.get()
        if username != '' or password != '':
            if update_or_save:
                database.save_account(name, phone, username, password)
                messagebox.showinfo('INFO', 'Account saved')
                self._reset()
                accounts = self._get_accounts()
                self._set_accounts(accounts)
            else:
                database.update_account(name, phone, username, password)
                messagebox.showinfo('INFO', 'Account update')
                self._reset()
                self.update_button.config(state='disabled')
                accounts = self._get_accounts()
                self._set_accounts(accounts)
        else:
            messagebox.showerror('Credentials', 'Please enter username or password')

    def _get_accounts(self):
        database = Database()
        accounts = database.get_accounts()
        return accounts

    def _reset(self):
        self.username.set("")
        self.password.set("")
        self.name.set("")
        self.phone.set("")

    def _display_content(self, event):
        self.frame_list_box.delete(0, END)
        content = self.list_box.get(ACTIVE)
        str = content.split()
        i = 0
        line = ''
        for word in str:
            if i % 2 == 0:
                line += word
                i += 1
            else:
                line += word
                self.frame_list_box.insert(END, line)
                line = ''
                i += 1

    def _delete_account(self):
        # curselection return Tuple. I converted to a list (This tuple returns line numbers or elements)
        index = list(self.list_box.curselection())
        # Index returning the first item in its list
        accounts = self._get_accounts()
        username = accounts[index[0]]
        answer = messagebox.askyesno('Remove account!', 'Are you sure you want to remove?')
        if answer:
            db = Database()
            is_deleted = db.delete_account(username[3])
            if is_deleted:
                accounts = db.get_accounts()
                self._set_accounts(accounts)
                self.frame_list_box.delete(0, END)
            else:
                messagebox.showerror('SQL Error', 'There is problem with delete function')

    def _edit_account(self):
        index = list(self.list_box.curselection())
        try:
            account = self.accounts[index[0]]
        except:
            accounts = self._get_accounts()
            account = accounts[index[0]]
        finally:
            if account:
                self.update_button.config(state=NORMAL)
                self.name.set(account[1])
                self.phone.set(account[2])
                self.username.set(account[3])
                self.password.set(account[4])