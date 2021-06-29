from tkinter import *
from tkinter import ttk
import tkinter.font as tkfont
from database import db


class TabActions(ttk.Frame):
    def __init__(self, window):
        super().__init__(window)

        self.__accounts()

    def __accounts(self):
        self.menu = StringVar()
        self.accounts = db.Database().get_accounts()
        user_name_list = []
        for account in self.accounts:
            user_name_list.append(account[3])
        ttk.Label(self, text='Choose user').grid(
            sticky='NE', padx=10, pady=(25, 0))
        self.accounts_option_menu = ttk.OptionMenu(self, self.menu, "", *user_name_list,
                                                   command=self.__refresh)
        self.accounts_option_menu.grid(sticky='NE')

    def __update_data(self, username):
        user_id = db.Database().get_user_id(username)
        data = db.Database().get_statistics(user_id)

        dates = []
        gains = []
        likes = []
        follow = []
        unfollow = []
        for day in data:
            dates.append(day[0])
            gains.append(day[1])
            likes.append(day[2])
            follow.append(day[3])
            unfollow.append(day[4])

        return {'Date': dates, 'Gains': gains, 'likes': likes, 'follow': follow, 'unfollow': unfollow}

    def __build_table(self, data):
        i = 0

        for key in data:
            i += 1
            self.__create_cell(key, 'black', i, 0)

        for y in range(len(data['Date'])):
            x = 0
            for key in data:
                x += 1
                if key == 'Date':
                    self.__create_cell(data[key][y], 'red', x, y + 1)
                else:
                    self.__create_cell(data[key][y], 'blue', x, y + 1)

    def __create_cell(self, text, color, x, y):
        e = Entry(self, width=20, fg=color,
                  font=('Arial', 16, 'bold'))

        e.grid(row=y, column=x)
        e.insert(END, text)

    def __refresh(self, username):
        self.__build_table(self.__update_data(username))
