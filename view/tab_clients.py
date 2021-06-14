from tkinter import *
from tkinter import ttk, messagebox
import tkinter.font as tkfont
from database import db

STATUS = {'running': 'green', 'finished': 'yellow', 'crashed': 'red'}
TABLE_ROW = 3
TABLE_COL = 5

lst = [(1,'Raj','Mumbai',19),
       (2,'Aaryan','Pune',18),
       (3,'Vaishnavi','Mumbai',20),
       (4,'Rachna','Mumbai',21),
       (5,'Shubham','Delhi',21)]

class TabClients(ttk.Frame):
    def __init__(self, window, clients):
        super().__init__(window)
        self.window = window
        self.__clients = clients

        self._build_table()

        ttk.Button(self, text="refresh", command=self._build_table).grid(
            column=0, columnspan=2, row=10, pady=(40, 0), padx=(20, 0))

    def _build_table(self):
        i = 0
        for client in self.__clients:
            self.e = Entry(self, width=20, fg='black',
                           font=('Arial',16,'bold'))

            self.e.grid(row=i, column=0)
            self.e.insert(END, client)

            self.e = Entry(self, width=20, fg=STATUS[self.__clients[client]],
                           font=('Arial',16,'bold'))

            self.e.grid(row=i, column=1)
            self.e.insert(END, self.__clients[client])
            i += 1
