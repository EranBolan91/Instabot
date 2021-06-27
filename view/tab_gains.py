from tkinter import *
from tkinter import ttk
from pandas import DataFrame
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import MaxNLocator
from database import db


class TabGains(ttk.Frame):
    def __init__(self, window):
        super().__init__(window)

        self.__accounts()

    def __build_graph(self, data):
        try:
            self.line._tkcanvas.destroy()
        except Exception:
            pass

        df = DataFrame(data, columns=['Gains', 'Date'])

        figure = plt.Figure(figsize=(5, 4), dpi=100)
        ax = figure.add_subplot(111)
        self.line = FigureCanvasTkAgg(figure, self)

        self.line.get_tk_widget().pack()
        self.line._tkcanvas.pack(side=LEFT, fill=BOTH)
        df = df[['Gains', 'Date']].groupby('Date').sum()
        df.plot(kind='line', legend=True, ax=ax,
                color='r', marker='o', fontsize=10)
        ax.set_title('Gains Vs. Date')
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))

    def __update_data(self, username):
        user_id = db.Database().get_user_id(username)
        data = db.Database().get_gains(user_id)

        dates = []
        gains = []
        for day in data:
            dates.append(day[0])
            gains.append(day[1])

        return {'Date': dates, 'Gains': gains}

    def __refresh(self, username):
        self.__build_graph(self.__update_data(username))

    def __accounts(self):
        self.menu = StringVar()
        self.accounts = db.Database().get_accounts()
        user_name_list = []
        for account in self.accounts:
            user_name_list.append(account[3])
        self.accounts_option_menu = ttk.OptionMenu(self, self.menu, "", *user_name_list,
                                                   command=self.__refresh)
        self.accounts_option_menu.pack(side=RIGHT, padx=130, pady=100)
