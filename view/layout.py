from .accounts import *
from .tab_follow_followers import *
from .tab_location import *
from .tab_followers import *
from .tab_hash_tag import *
from .settings import *
from .tab_dm import *
from .tab_statistics import *


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

        hash_tag_tab = TabHashTag(tab_control)
        followers_tab = TabFollowers(tab_control)
        location_tab = TabLocation(tab_control)
        follow_followers_tab = TabFollowFollowers(tab_control)
        dm_tab = TabDM(tab_control)
        statistics_tab = StatisticsTab(tab_control)

        tab_control.add(hash_tag_tab, text='Hash Tag')
        tab_control.add(followers_tab, text='Followers')
        tab_control.add(location_tab, text='Location')
        tab_control.add(follow_followers_tab, text='Follow Followers')
        tab_control.add(dm_tab, text='DM')
        tab_control.add(statistics_tab, text='Statistics')

        tab_control.pack(expand=1, fill="both")


        # status bar config
        status_bar = Label(window, text="status bar", bd=1, relief=SUNKEN, anchor=W)
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
