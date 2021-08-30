from tkinter import *
from tkinter import ttk, messagebox
import tkinter.font as tkfont
from database import db
from database.proxy.proxy import Proxy
from models.proxy import Proxy as ProxyModel


class Testing:
    def __init__(self, window):
        self.window = window

        wrap = LabelFrame(window)
        canvas = Canvas(wrap, width=600, height=400)
        #canvas.grid(row=0, column=0, sticky='news')
        canvas.pack(side=LEFT, fill="both", expand="yes")
        yscrollbar = ttk.Scrollbar(self.window, orient="vertical", command=canvas.yview)
        yscrollbar.pack(side=RIGHT, fill="y")
        canvas.configure(yscrollcommand=yscrollbar.set)
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        myFrame = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=myFrame, anchor="nw")
        wrap.pack(fill="both", expand="yes")

        for i in range(20):
            Button(myFrame, text="My Button").pack()