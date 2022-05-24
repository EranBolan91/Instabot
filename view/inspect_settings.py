from tkinter import *
from tkinter import ttk, messagebox
import tkinter.font as tkfont


class InspectSettings:
    def __init__(self, window):
        self.window = window
        self.block_url = StringVar()
        self.scroll_box_xml = StringVar()
        self.like_buttons_xml = StringVar()
        self.page_not_avi_txt = StringVar()
        self.user_not_avi_txt = StringVar()
        self.block_change_password = StringVar()
        self.second_like_buttons_xml = StringVar()
        self.scroll_box_close_button_xml = StringVar()
        self.headerFont = tkfont.Font(family="Helvetica", size=12, weight='bold')
        self.titleFont = tkfont.Font(family="Helvetica", size=9)
        self.bold = tkfont.Font(weight='bold', size=10)

        # Configuration for scrollbar
        wrap = LabelFrame(window)
        canvas = Canvas(wrap)
        canvas.pack(side=LEFT, fill="both", expand="yes")
        yscrollbar = ttk.Scrollbar(self.window, orient="vertical", command=canvas.yview)
        yscrollbar.pack(side=RIGHT, fill="y")
        canvas.configure(yscrollcommand=yscrollbar.set)
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        myFrame = Frame(canvas)
        canvas.create_window((0, 0), window=myFrame, anchor="nw")
        wrap.pack(fill="both", expand="yes")

        ttk.Label(myFrame, text='Inspect Settings', font=self.headerFont).grid(column=0, row=0, padx=10, pady=(10, 0))

        # Block Frame
        block_frame = ttk.LabelFrame(myFrame, text='Block Settings')
        block_frame.grid(column=0, row=2, rowspan=2, pady=(0, 0), ipady=120, ipadx=250)
        title_block_url = ttk.Label(block_frame, text='Block URL : ', font=self.titleFont)
        input_block_url = ttk.Entry(block_frame, textvariable=self.block_url, width=80)
        title_block_change_password = ttk.Label(block_frame, text='Block Change Password URL : ', font=self.titleFont)
        input_block_change_password = ttk.Entry(block_frame, textvariable=self.block_change_password, width=80)

        title_block_url.place(relx=0.01, rely=0.1)
        input_block_url.place(relx=0.01, rely=0.2)
        title_block_change_password.place(relx=0.01, rely=0.4)
        input_block_change_password.place(relx=0.01, rely=0.5)

        # Scroll Box Frame
        scroll_box_frame = ttk.LabelFrame(myFrame, text='Scroll Box')
        scroll_box_frame.grid(column=0, row=4, rowspan=2, pady=(0, 0), ipady=120, ipadx=250)
        title_scroll_box_xml = ttk.Label(scroll_box_frame, text='Scroll Box XML : ', font=self.titleFont)
        input_scroll_box_xml = ttk.Entry(scroll_box_frame, textvariable=self.scroll_box_xml, width=80)
        title_scroll_box_close_button_xml = ttk.Label(scroll_box_frame, text='Scroll Box Close Button XML :', font=self.titleFont)
        input_scroll_box_close_button_xml = ttk.Entry(scroll_box_frame, textvariable=self.scroll_box_close_button_xml, width=80)

        title_scroll_box_xml.place(relx=0.01, rely=0.1)
        input_scroll_box_xml.place(relx=0.01, rely=0.2)
        title_scroll_box_close_button_xml.place(relx=0.01, rely=0.4)
        input_scroll_box_close_button_xml.place(relx=0.01, rely=0.5)

        # Like Buttons Frame
        like_buttons_frame = ttk.LabelFrame(myFrame, text='Like Buttons')
        like_buttons_frame.grid(column=1, row=2, rowspan=2, padx=(100, 0), ipady=120, ipadx=250)
        title_like_buttons_xml = ttk.Label(like_buttons_frame, text='Like Button XML : ', font=self.titleFont)
        input_like_buttons_xml = ttk.Entry(like_buttons_frame, textvariable=self.like_buttons_xml, width=80)
        title_second_like_buttons_xml = ttk.Label(like_buttons_frame, text='Second Like Button XML :', font=self.titleFont)
        input_second_like_buttons_xml = ttk.Entry(like_buttons_frame, textvariable=self.second_like_buttons_xml, width=80)

        title_like_buttons_xml.place(relx=0.01, rely=0.1)
        input_like_buttons_xml.place(relx=0.01, rely=0.2)
        title_second_like_buttons_xml.place(relx=0.01, rely=0.4)
        input_second_like_buttons_xml.place(relx=0.01, rely=0.5)

        # Page not available Frame
        page_not_avi_frame = ttk.LabelFrame(myFrame, text='Page not available')
        page_not_avi_frame.grid(column=1, row=4, rowspan=2, padx=(100, 0), ipady=120, ipadx=250)
        title_page_not_avi_txt = ttk.Label(page_not_avi_frame, text='Page Not Available Text : ', font=self.titleFont)
        input_page_not_avi_txt = ttk.Entry(page_not_avi_frame, textvariable=self.page_not_avi_txt, width=80)
        title_user_not_avi_txt = ttk.Label(page_not_avi_frame, text='User Not Found Text :', font=self.titleFont)
        input_user_not_avi_txt = ttk.Entry(page_not_avi_frame, textvariable=self.user_not_avi_txt, width=80)

        title_page_not_avi_txt.place(relx=0.01, rely=0.1)
        input_page_not_avi_txt.place(relx=0.01, rely=0.2)
        title_user_not_avi_txt.place(relx=0.01, rely=0.4)
        input_user_not_avi_txt.place(relx=0.01, rely=0.5)

        ttk.Button(myFrame, text='SAVE', command="").grid(column=0, columnspan=2, row=6, pady=(40, 0))

        # Initialize data
        self._init_data()

    def _init_data(self):
        pass

