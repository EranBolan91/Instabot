from tkinter import *
from tkinter import ttk, messagebox
import tkinter.font as tkfont
from database import db
import schedule


class Settings:
    def __init__(self, window):
        self.window = window
        self.likes_amount = StringVar()
        self.check_schedule = IntVar()
        self.schedule_hour = IntVar()
        self.list_name = StringVar()
        self.headerFont = tkfont.Font(family="Helvetica", size=12, weight='bold')
        self.titleFont = tkfont.Font(family="Helvetica", size=9)
        self.bold = tkfont.Font(weight='bold', size=10)
        self.amount = 0

        ttk.Label(self.window, text='SETTINGS ', font=self.headerFont) \
                    .grid(column=0, row=0, padx=10, pady=10)

        self.title_amount = ttk.Label(self.window, text='LIKE/FOLLOW/COMMENT posts who have more then {} likes '
                                                                    .format(self.amount), font=self.titleFont)
        self.title_amount.grid(column=0, row=1, padx=10, pady=10)
        ttk.Entry(self.window, textvariable=self.likes_amount).grid(column=0, row=2)

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
                                        .grid(column=0, columnspan=2, row=4, pady=15)

        # Distribution list for DM
        distribution_list = ttk.LabelFrame(self.window, text='Distribution list')
        distribution_list.grid(column=2, row=1, ipady=100, ipadx=50, padx=20, rowspan=3)
        title = Label(distribution_list, text="Create distribution lists to DM them ", bg='gray23', font=self.bold, fg='gray67')
        listbox = Listbox(distribution_list, width=20, height=10)
        list_name = Label(distribution_list, text="Enter list name ", bg='gray23', fg='gray67')
        input_list_name = ttk.Entry(distribution_list, textvariable=self.list_name)

        title.pack(fill=X)
        listbox.place(relx=0.6, rely=0.2)
        list_name.place(relx=0.0, rely=0.4)
        input_list_name.place(relx=0.0, rely=0.5)


        # Init data
        self._settings_data()

    def _settings_data(self):
        self.database = db.Database()
        data_settings = self.database.get_data_from_settings()
        # This 'if' because when i run for the first time the program,
        # there is no 'data settings' - its empty. so i init it with 0
        if data_settings == '' or data_settings is None:
            self.amount = 0
        else:
            self.amount = data_settings[1]

        # Set the CheckButton
        self.title_amount['text'] = 'LIKE/FOLLOW/COMMENT users who has more then {} likes '.format(data_settings[1])
        self.check_schedule.set(data_settings[3])
        self.current_hours['text'] = "HOURS: {}".format(data_settings[4])
        self._activate_check()

    def _save_changes(self):
        database = db.Database()
        likes_amount = self.likes_amount.get()
        schedule_hour = self.schedule_hour.get()
        is_schedule = self.check_schedule.get()

        if likes_amount.isnumeric() and not int(likes_amount) < 0:
            database.save_settings(likes_amount, schedule_hour, is_schedule)
            messagebox.showinfo('Settings', 'Changes has been saved')
            self.likes_amount.set("")
            data = database.get_data_from_settings()
            self.title_amount['text'] = 'LIKE/FOLLOW/COMMENT users who has more then {} likes '.format(data[1])
            self.current_hours['text'] = "HOURS: {}".format(data[4])
        else:
            messagebox.showerror('Only numbers', 'Please enter only numbers to amount entry')

    def _activate_check(self):
        if self.check_schedule.get() == 1:  # whenever checked
            self.spin_hours.config(state=NORMAL)
        elif self.check_schedule.get() == 0:  # whenever unchecked
            self.spin_hours.config(state=DISABLED)
