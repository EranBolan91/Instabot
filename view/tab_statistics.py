from tkinter import *
from tkinter import ttk
import tkinter.font as tkfont
from database.dm.dm import DMDB
from database.follow_followers.follow_followers import FollowFollowersDB
from database.hashtag.hashtag import HashtagDB
from database.location.location import LocationDB
from database.follow_back.follow_back import FollowBackDB


class StatisticsTab(ttk.Frame):
    def __init__(self, window):
        super().__init__(window)

        self.headerFont = tkfont.Font(family="Helvetica", size=12, weight='bold')
        self.titleFont = tkfont.Font(family="Helvetica", size=9)
        self.h3 = tkfont.Font(family="Helvetica", size=11, weight='bold')
        self.bold = tkfont.Font(weight='bold', size=10)

        # Configuration for scrollbar
        wrap = Frame(self)
        canvas = Canvas(wrap)
        canvas.pack(side=LEFT, fill="both", expand="yes")
        yscrollbar = ttk.Scrollbar(wrap, orient="vertical", command=canvas.yview)
        yscrollbar.pack(side=RIGHT, fill="y")
        canvas.configure(yscrollcommand=yscrollbar.set)
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        stateFrame = Frame(canvas)
        canvas.create_window((0, 0), window=stateFrame, anchor="nw")
        wrap.pack(fill="both", expand="yes")

        # Frames
        hashtag_frame = ttk.Frame(stateFrame)
        location_frame = ttk.Frame(stateFrame)
        follow_followers_frame = ttk.Frame(stateFrame)
        dm_frame = ttk.Frame(stateFrame)
        follow_back_frame = ttk.Frame(stateFrame)

        hashtag_frame.pack(expand=TRUE)
        location_frame.pack(expand=TRUE)
        follow_followers_frame.pack(expand=TRUE)
        dm_frame.pack(expand=TRUE)
        follow_back_frame.pack(expand=TRUE)

        # Titles
        ttk.Label(hashtag_frame, text='HashTag', font=self.headerFont).pack()
        ttk.Label(location_frame, text='Location', font=self.headerFont).pack()
        ttk.Label(follow_followers_frame, text='Follow Followers', font=self.headerFont).pack()
        ttk.Label(dm_frame, text='DM', font=self.headerFont).pack()
        ttk.Label(follow_back_frame, text='Follow back', font=self.headerFont).pack()

        # Creating Scroll bars
        hash_tag_scrollbary = ttk.Scrollbar(hashtag_frame)
        hash_tag_scrollbarx = ttk.Scrollbar(hashtag_frame, orient=HORIZONTAL)
        follow_followers_scrollbary = ttk.Scrollbar(follow_followers_frame)
        follow_followers_scrollbarx = ttk.Scrollbar(follow_followers_frame, orient=HORIZONTAL)
        location_scrollbary = ttk.Scrollbar(location_frame)
        location_scrollbarx = ttk.Scrollbar(location_frame, orient=HORIZONTAL)
        dm_scrollbary = ttk.Scrollbar(dm_frame)
        dm_scrollbarx = ttk.Scrollbar(dm_frame, orient=HORIZONTAL)
        follow_back_scrollbary = ttk.Scrollbar(follow_back_frame)
        follow_back_scrollbarx = ttk.Scrollbar(follow_back_frame, orient=HORIZONTAL)

        hash_tag_scrollbary.pack(side=RIGHT, fill=Y)
        hash_tag_scrollbarx.pack(side=BOTTOM, fill=X)
        follow_followers_scrollbary.pack(side=RIGHT, fill=Y)
        follow_followers_scrollbarx.pack(side=BOTTOM, fill=X)
        location_scrollbary.pack(side=RIGHT, fill=Y)
        location_scrollbarx.pack(side=BOTTOM, fill=X)
        dm_scrollbary.pack(side=RIGHT, fill=Y)
        dm_scrollbarx.pack(side=BOTTOM, fill=X)
        follow_back_scrollbary.pack(side=RIGHT, fill=Y)
        follow_back_scrollbarx.pack(side=BOTTOM, fill=X)

        # Creating the list boxes
        self.hashtag_list_box = Listbox(hashtag_frame, width=220, height=20,
                                        yscrollcommand=hash_tag_scrollbary.set, xscrollcommand=hash_tag_scrollbarx.set)
        self.location_list_box = Listbox(location_frame, width=220, height=20,
                                         yscrollcommand=location_scrollbary.set, xscrollcommand=location_scrollbarx.set)
        self.follow_followers_list_box = Listbox(follow_followers_frame, width=220, height=20,
                         yscrollcommand=follow_followers_scrollbary.set, xscrollcommand=follow_followers_scrollbarx.set)
        self.dm_list_box = Listbox(dm_frame, width=220, height=20,
                                   yscrollcommand=dm_scrollbary.set, xscrollcommand=dm_scrollbarx.set)
        self.follow_back_list_box = Listbox(follow_back_frame, width=220, height=20,
                                       yscrollcommand=follow_back_scrollbary.set, xscrollcommand=follow_back_scrollbarx.set)

        # Connect the scrollbar to listbox
        hash_tag_scrollbary.config(command=self.hashtag_list_box.yview)
        hash_tag_scrollbarx.config(command=self.hashtag_list_box.xview)
        follow_followers_scrollbary.config(command=self.follow_followers_list_box.yview)
        follow_followers_scrollbarx.config(command=self.follow_followers_list_box.xview)
        location_scrollbary.config(command=self.location_list_box.yview)
        location_scrollbarx.config(command=self.location_list_box.xview)
        dm_scrollbary.config(command=self.dm_list_box.yview)
        dm_scrollbarx.config(command=self.dm_list_box.xview)
        follow_back_scrollbary.config(command=self.follow_back_list_box.yview)
        follow_back_scrollbarx.config(command=self.follow_back_list_box.xview)

        # Refresh button
        refresh_button = ttk.Button(stateFrame, text='REFRESH', command=self._init_data)
        refresh_button.pack(expand=TRUE)

        # Packing the boxes
        self.hashtag_list_box.pack()
        self.location_list_box.pack()
        self.follow_followers_list_box.pack()
        self.dm_list_box.pack()
        self.follow_back_list_box.pack()

        # Initialize data
        self._init_data()

    def _init_data(self):
        hashtag_data = HashtagDB().get_hashtag_data()
        location_data = LocationDB().get_location_data()
        follow_followers_data = FollowFollowersDB().get_follow_followers_data()
        dm_data = DMDB().get_dm_data()
        follow_back_data =  FollowBackDB().get_follow_back_data()

        self.hashtag_list_box.delete(0, 'end')
        self.location_list_box.delete(0, 'end')
        self.follow_followers_list_box.delete(0, 'end')
        self.dm_list_box.delete(0, 'end')
        self.follow_back_list_box.delete(0, 'end')

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

        for data in follow_back_data:
            self.follow_back_list_box.insert(END, data)

