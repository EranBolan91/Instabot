import sys
import tkinter as tkr
from bot_folder.proxy_manager import ProxyManager
from .accounts import *
from .tab_follow_followers import *
from .tab_location import *
from .tab_followers import *
from .tab_hash_tag import *
from .settings import *
from .tab_dm import *
from .tab_statistics import *
from .tab_combination import *
from .tab_likes import *
from .tab_clients import *
from .tab_dm_to_followers import *
from .tab_gains import *
from .tab_actions import *


class Layout:
    def __init__(self, window):
        self.window = window

        # width_of_window = 1280
        # height_of_window = 800

        window.title('Insta Bot')
        # Center the program video: https://www.youtube.com/watch?v=gjU3Lx8XMS8
        # screen_width = window.winfo_screenwidth()
        # screen_height = window.winfo_screenheight()
        # x_coordinate = (screen_width/2) - (width_of_window/2)
        # y_coordinate = (screen_height / 2) - (height_of_window / 2)
        # window.geometry("%dx%d+%d+%d" % (width_of_window, height_of_window, x_coordinate, y_coordinate))

        scroll_bar = tkr.Scrollbar(window)
        scroll_bar.pack(side=tkr.RIGHT, fill="y")

        # menu config
        menu = Menu(window)
        sub_menu = Menu(menu, tearoff=0)
        sub_menu.add_command(label='Accounts', command=self._accounts)
        sub_menu.add_command(label='Settings', command=self._settings)
        sub_menu.add_command(label='Exit', command=self._exit)
        menu.add_cascade(label='Main', menu=sub_menu)
        window.config(menu=menu)

        # tab config
        tab_control = ttk.Notebook(window)

        clients = {}
        proxy_manager = ProxyManager()

        followers_dm_tab = TabFollowersToDM(tab_control, proxy_manager)
        combination_tab = TabCombination(tab_control, clients, proxy_manager)
        clients_tab = TabClients(tab_control, clients)
        gains_tab = TabGains(tab_control)
        actions_tab = TabActions(tab_control)

        tab_control.add(combination_tab, text='Combination')
        tab_control.add(clients_tab, text="Clients")
        tab_control.add(followers_dm_tab, text="dm to followers")
        tab_control.add(gains_tab, text="Gains")
        tab_control.add(actions_tab, text="Actions")

        tab_control.pack(expand=1, fill="both")

        # status bar config
        status_bar = Label(window, text="status bar",
                           bd=1, relief=SUNKEN, anchor=W)
        status_bar.pack(side=BOTTOM, fill=X)

    def _accounts(self):
        win = Toplevel(self.window)
        win.iconbitmap('insta_bot.ico')
        AccountsNew(win)

    def _settings(self):
        win = Toplevel(self.window)
        win.iconbitmap('insta_bot.ico')
        Settings(win)

    def _exit(self):
        self.window.destroy()
        sys.exit()
