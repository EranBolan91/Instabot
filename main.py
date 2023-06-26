#from ttkthemes import ThemedTk
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from view.layout import Layout

import tkinter as tk
# TODO: need to change the logic in follow followers to scroll and the follow (like combination)
# TODO: need to fix when the account follow after a user he wants to access to his followers list. It returns -1 buttons
# TODO: need to change the logic of unfollow only users who are not following back.-**changed-still need to run tests **
#  need to get first the names, close it and again open new window and start unfollow
# TODO: add check how many posts user has
# TODO: display combination window on statistic tab
# TODO: write error message function on 'main_bot' to use on all other classes - ** added **
# TODO: add limit box on unfollowers that limits how many users to unfollow - *** added - just need to run few tests **
# TODO: on the statistic page, create box details for every account that display his all actions
# TODO: add on the statistic a drop list with box that display actions of every account
# TODO: add table to unfollow that counts how many users follow back when i unfollow them **created table, just need to display **
# TODO: create table for UI so i can change it dynamic when the UI of insta changes
#   need to create new window under settings. A lot of work

window = ttk.Window(themename="darkly")
#window.iconbitmap("insta_bot.ico")
window.attributes('-fullscreen', True)
Layout(window)

window.mainloop()

