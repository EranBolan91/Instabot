from .accounts import *
from .tab_follow_followers import *
from .tab_location import *
from .tab_followers import *
from .tab_hash_tag import *
from .settings import *
from .inspect_settings import *
from .tab_dm import *
from .tab_statistics import *
from .tab_combination import *
import tkinter as tkr


class Layout:
    def __init__(self, window):
        self.window = window

        window.title('Insta Bot')

        # menu config
        menu = Menu(window)
        sub_menu = Menu(menu, tearoff=0)
        sub_menu.add_command(label='Accounts', command=self._accounts)
        sub_menu.add_command(label='Settings', command=self._settings)
        sub_menu.add_command(label='Inspect Settings', command=self._inspect_settings)
        sub_menu.add_command(label='Exit', command=self._exit)
        menu.add_cascade(label='Main', menu=sub_menu)
        window.config(menu=menu)

        # tab config
        tab_control = ttk.Notebook(window)

        hash_tag_tab = TabHashTag(tab_control)
        followers_tab = TabFollowers(tab_control)
        location_tab = TabLocation(tab_control)
        follow_followers_tab = TabFollowFollowers(tab_control)
        dm_tab = TabDM(tab_control)
        statistics_tab = StatisticsTab(tab_control)
        combination_tab = TabCombination(tab_control)

        tab_control.add(hash_tag_tab, text='Hash Tag')
        tab_control.add(followers_tab, text='Followers')
        tab_control.add(location_tab, text='Location')
        tab_control.add(follow_followers_tab, text='Follow Followers')
        tab_control.add(dm_tab, text='DM')
        tab_control.add(combination_tab, text='Combination')
        tab_control.add(statistics_tab, text='Statistics')
        
        tab_control.pack(expand=1, fill="both")

        # status bar config
        status_bar = Label(window, text="status bar", bd=1, relief=SUNKEN, anchor=W)
        status_bar.pack(side=BOTTOM, fill=X)

    def _accounts(self):
        win = Toplevel(self.window)
        #win.iconbitmap('insta_bot.ico')
        AccountsNew(win)

    def _settings(self):
        win = Toplevel(self.window)
        w, h = self.window.winfo_screenwidth(), self.window.winfo_screenheight()
        win.geometry("%dx%d+0+0" % (w, h))
        #win.iconbitmap('insta_bot.ico')
        Settings(win)

    def _inspect_settings(self):
        win = Toplevel(self.window)
        w, h = self.window.winfo_screenwidth(), self.window.winfo_screenheight()
        win.geometry("%dx%d+0+0" % (w, h))
        #win.iconbitmap('insta_bot.ico')
        InspectSettings(win)

    def _exit(self):
        self.window.destroy()
