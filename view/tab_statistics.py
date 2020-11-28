from tkinter import *
from tkinter import ttk
import tkinter.font as tkfont
from database.dm.dm import DMDB
from database.follow_followers.follow_followers import FollowFollowersDB
from database.hashtag.hashtag import HashtagDB
from database.location.location import LocationDB


class StatisticsTab(ttk.Frame):
    def __init__(self, window):
        super().__init__(window)

        self.headerFont = tkfont.Font(family="Helvetica", size=12, weight='bold')
        self.titleFont = tkfont.Font(family="Helvetica", size=9)
        self.h3 = tkfont.Font(family="Helvetica", size=11, weight='bold')
        self.bold = tkfont.Font(weight='bold', size=10)

        canvas = ttk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        # Frames
        hashtag_frame = ttk.Frame(self)
        location_frame = ttk.Frame(self)
        follow_followers_frame = ttk.Frame(self)
        dm_frame = ttk.Frame(self)
        hashtag_frame.grid(column=0, row=1, padx=10, pady=(20, 0))
        location_frame.grid(column=0, row=2, padx=10, pady=(20, 0))
        follow_followers_frame.grid(column=1, row=1, padx=10, pady=(20, 0))
        dm_frame.grid(column=1, row=2, padx=10, pady=(20, 0))

        # Titles
        ttk.Label(hashtag_frame, text='HashTag', font=self.headerFont).pack()
        ttk.Label(location_frame, text='Location', font=self.headerFont).pack()
        ttk.Label(follow_followers_frame, text='Follow Followers', font=self.headerFont).pack()
        ttk.Label(dm_frame, text='DM', font=self.headerFont).pack()

        # Creating Scroll bars
        scrollbary = ttk.Scrollbar(hashtag_frame)
        scrollbarx = ttk.Scrollbar(hashtag_frame, orient=HORIZONTAL)
        follow_followers_scrollbary = ttk.Scrollbar(follow_followers_frame)
        follow_followers_scrollbarx = ttk.Scrollbar(follow_followers_frame, orient=HORIZONTAL)

        scrollbary.pack(side=RIGHT, fill=Y)
        scrollbarx.pack(side=BOTTOM, fill=X)
        follow_followers_scrollbary.pack(side=RIGHT, fill=Y)
        follow_followers_scrollbarx.pack(side=BOTTOM, fill=X)

        # Creating the list boxes
        self.hashtag_list_box = Listbox(hashtag_frame, width=110, height=15,
                                        yscrollcommand=scrollbary.set, xscrollcommand=scrollbarx.set)
        self.location_list_box = Listbox(location_frame, width=110, height=15)
        self.follow_followers_list_box = Listbox(follow_followers_frame, width=110, height=15,
                        yscrollcommand=follow_followers_scrollbary.set, xscrollcommand=follow_followers_scrollbarx.set)
        self.dm_list_box = Listbox(dm_frame, width=110, height=15)

        # Connect the scrollbar to listbox
        scrollbary.config(command=self.hashtag_list_box.yview)
        scrollbarx.config(command=self.hashtag_list_box.xview)
        follow_followers_scrollbary.config(command=self.follow_followers_list_box.yview)
        follow_followers_scrollbarx.config(command=self.follow_followers_list_box.xview)

        # Refresh button
        refresh_button = ttk.Button(self, text='REFRESH', command=self._init_data)
        refresh_button.grid(column=0, columnspan=2, row=3, pady=(20,0))

        # Packing the boxes
        self.hashtag_list_box.pack()
        self.location_list_box.pack()
        self.follow_followers_list_box.pack()
        self.dm_list_box.pack()

        # Initialize data
        self._init_data()

    def _init_data(self):
        hashtag_data = HashtagDB().get_hashtag_data()
        location_data = LocationDB().get_location_data()
        follow_followers_data = FollowFollowersDB().get_follow_followers_data()
        dm_data = DMDB().get_dm_data()

        self.hashtag_list_box.delete(0, 'end')
        self.location_list_box.delete(0, 'end')
        self.follow_followers_list_box.delete(0, 'end')
        self.dm_list_box.delete(0, 'end')
        for data in hashtag_data:
            box = """ Account: {} , Hashtag: {} , Num Posts: {} , Failed Posts: {} , Action Like: {} , Action Follow: {} , Action Comment: {} , Distribution: {} , Group Name: {} , Comment: {} , Schedule: {} , Time: {}""".format(
                data[1], data[2], data[3], data[4], data[5], data[6], data[7], data[8], data[9], data[10], data[11],
                data[12])
            self.hashtag_list_box.insert(END, box)

        for data in location_data:
            self.location_list_box.insert(END, data)

        for data in follow_followers_data:
            self.follow_followers_list_box.insert(END, data)

        for data in dm_data:
            self.dm_list_box.insert(END, data)

