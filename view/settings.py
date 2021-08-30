from tkinter import *
from tkinter import ttk, messagebox
import tkinter.font as tkfont
from database import db
from database.proxy.proxy import Proxy
from models.proxy import Proxy as ProxyModel
from models.website import Website as WebsiteModel
from database.website.website import Website


class Settings:
    def __init__(self, window):
        self.window = window
        self.likes_amount = IntVar()
        self.posts_amount = IntVar()
        self.followers_amount_input = IntVar()
        self.headless_value = BooleanVar()
        self.username_option = StringVar()
        self.host_entry = StringVar()
        self.website_link_entry = StringVar()
        self.proxy_username_entry = StringVar()
        self.proxy_password_entry = StringVar()
        self.proxy_port_entry = IntVar()
        self.distribution_list_name = StringVar()
        self.headerFont = tkfont.Font(family="Helvetica", size=12, weight='bold')
        self.titleFont = tkfont.Font(family="Helvetica", size=9)
        self.bold = tkfont.Font(weight='bold', size=10)
        self.amount = 0
        self.followers_amount = 0
        self.posts = 0

        self.accounts = db.Database().get_accounts()
        user_name_list = []

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

        if self.accounts:
            for account in self.accounts:
                user_name_list.append(account[3])

        ttk.Label(myFrame, text='SETTINGS ', font=self.headerFont).grid(column=0, row=0, padx=10, pady=(10, 0))
        # Main settings
        main_settings_frame = ttk.LabelFrame(myFrame, text='Main settings')
        main_settings_frame.grid(column=0, row=2, rowspan=2, pady=(0, 0), ipady=120, ipadx=250)
        self.title_amount = ttk.Label(main_settings_frame, text='LIKE/FOLLOW/COMMENT posts who have more then {} likes '
                                                                    .format(self.amount), font=self.titleFont)
        input_likes_amount = ttk.Entry(main_settings_frame, textvariable=self.likes_amount)

        self.title_posts_amount = ttk.Label(main_settings_frame, text='Follow after users who have more then {} posts'
                                      .format(self.posts), font=self.titleFont)
        input_posts_amount = ttk.Entry(main_settings_frame, textvariable=self.posts_amount)

        self.title_followers_amount = ttk.Label(main_settings_frame, text='Follow after users that have more then {} followers'
                                      .format(self.followers_amount), font=self.titleFont)
        input_amount_followers = ttk.Entry(main_settings_frame, textvariable=self.followers_amount_input)
        headless_check_box = ttk.Checkbutton(main_settings_frame, text='Headless', variable=self.headless_value)

        self.title_amount.place(relx=0.08, rely=0.1)
        input_likes_amount.place(relx=0.08, rely=0.2)
        self.title_posts_amount.place(relx=0.08, rely=0.3)
        input_posts_amount.place(relx=0.08, rely=0.4)
        self.title_followers_amount.place(relx=0.08, rely=0.5)
        input_amount_followers.place(relx=0.08, rely=0.6)
        headless_check_box.place(relx=0.08, rely=0.8)

        # Proxy
        proxy_frame = ttk.LabelFrame(myFrame, text='Proxy')
        proxy_frame.grid(column=0, row=5, ipady=120, ipadx=400, padx=10, pady=(0, 20), rowspan=2, columnspan=2)
        proxy_host_title = Label(proxy_frame, text="Host", bg='gray23', font=self.titleFont, fg='gray67')
        proxy_host_entry = ttk.Entry(proxy_frame, textvariable=self.host_entry, width=35)
        proxy_username_title = Label(proxy_frame, text="Username", bg='gray23', font=self.titleFont, fg='gray67')
        proxy_username_entry = ttk.Entry(proxy_frame, textvariable=self.proxy_username_entry, width=35)
        proxy_password_title = Label(proxy_frame, text="Password", bg='gray23', font=self.titleFont, fg='gray67')
        proxy_password_entry = ttk.Entry(proxy_frame, textvariable=self.proxy_password_entry, width=35)
        proxy_port_title = Label(proxy_frame, text="Port", bg='gray23', font=self.titleFont, fg='gray67')
        proxy_port_entry = ttk.Entry(proxy_frame, textvariable=self.proxy_port_entry)
        proxy_save_button = ttk.Button(proxy_frame, text="SAVE", width=10, command=self.save_proxy)
        proxy_remove_button = ttk.Button(proxy_frame, text="REMOVE", width=10, command=self.remove_proxy)
        self.proxy_listbox = Listbox(proxy_frame, width=30, height=13)

        proxy_host_title.place(relx=0.08, rely=0.1)
        proxy_host_entry.place(relx=0.25, rely=0.1)
        proxy_username_title.place(relx=0.08, rely=0.3)
        proxy_username_entry.place(relx=0.25, rely=0.3)
        proxy_password_title.place(relx=0.08, rely=0.5)
        proxy_password_entry.place(relx=0.25, rely=0.5)
        proxy_port_title.place(relx=0.08, rely=0.7)
        proxy_port_entry.place(relx=0.25, rely=0.7)
        proxy_save_button.place(relx=0.2, rely=0.85)
        proxy_remove_button.place(relx=0.5, rely=0.85)
        self.proxy_listbox.place(relx=0.7, rely=0.09)

        # Websites
        website_frame = ttk.LabelFrame(myFrame, text='Websites')
        website_frame.grid(column=0, row=7, ipady=70, ipadx=400, padx=10, pady=(0, 20), rowspan=2, columnspan=2)
        website_link = Label(website_frame, text="Website", bg='gray23', font=self.titleFont, fg='gray67')
        website_link_entry = ttk.Entry(website_frame, textvariable=self.website_link_entry, width=47)
        website_save_button = ttk.Button(website_frame, text="SAVE", width=10, command=self.save_website)
        website_remove_button = ttk.Button(website_frame, text="REMOVE", width=10, command=self.remove_website)
        self.website_listbox = Listbox(website_frame, width=30, height=13)

        website_link.place(relx=0.08, rely=0.1)
        website_link_entry.place(relx=0.2, rely=0.1)
        website_save_button.place(relx=0.2, rely=0.45)
        website_remove_button.place(relx=0.42, rely=0.45)
        self.website_listbox.place(relx=0.7, rely=0.0)

        ttk.Button(myFrame, text="SAVE CHANGES", command=self._save_changes, width=30)\
                                        .grid(column=0, columnspan=4, row=4, pady=15)

        # Distribution list for DM
        distribution_list = ttk.LabelFrame(myFrame, text='Distribution list')
        distribution_list.grid(column=2, row=1, ipady=120, ipadx=50, padx=20, rowspan=4)
        title = Label(distribution_list, text="Create distribution lists to DM them ", bg='gray23', font=self.bold, fg='gray67')
        self.listbox = Listbox(distribution_list, width=20, height=10)
        list_name = Label(distribution_list, text="Enter list name ", bg='gray23', fg='gray67')
        input_list_name = ttk.Entry(distribution_list, textvariable=self.distribution_list_name)
        add_btn = ttk.Button(distribution_list, text="ADD", width=10, command=self._save_distribution_list)
        remove_btn = ttk.Button(distribution_list, text="REMOVE", width=10, command=self._remove_group_from_distribution_list)
        username_choose_title = Label(distribution_list, text="Please choose a username", bg='gray23', fg='gray67')

        title.pack(fill=X)
        list_name.place(relx=0.0, rely=0.2)
        input_list_name.place(relx=0.0, rely=0.3)
        username_choose_title.place(relx=0.0, rely=0.5)
        self.listbox.place(relx=0.6, rely=0.2)
        add_btn.place(relx=0.6, rely=0.9)
        remove_btn.place(relx=0.2, rely=0.9)

        if user_name_list:
            users_list_option = ttk.OptionMenu(distribution_list, self.username_option, user_name_list[0], *user_name_list, command=self._set_users_groups)
            users_list_option.place(relx=0.0, rely=0.6)
        else:
            users_lists_label = ttk.Label(distribution_list, text='No Accounts')
            users_lists_label.place(relx=0.0, rely=0.6)


        # Init data
        self._settings_data()

    def _settings_data(self):
        self.database = db.Database()
        data_settings = self.database.get_data_from_settings()
        proxies = self.database.get_proxy_data()
        websites = self.database.get_websites_data()
        # Init the box list of distribution groups
        username_menu = self.username_option.get()
        if username_menu:
            distribution_groups = self.database.get_distribution_lists_by_username(username_menu)
            for group in distribution_groups:
                self.listbox.insert(END, group[1])

        for proxy in proxies:
            self.proxy_listbox.insert(END, proxy[2])

        for website in websites:
            self.website_listbox.insert(END, website[1])

        self.headless_value.set(data_settings[6])

        # This 'if' because when i run for the first time the program,
        # there is no 'data settings' - its empty. so i init it with 0
        if data_settings == '' or data_settings is None:
            self.amount = 0
            self.followers_amount = 0
            self.database.save_settings(0, 0, 0, 0, 0, 0)
        else:
            self.amount = data_settings[1]
            self.followers_amount = data_settings[2]

        # Set the CheckButton
        self.title_amount['text'] = 'LIKE/FOLLOW/COMMENT users who has more then {} likes'.format(self.amount)
        self.title_followers_amount['text'] = 'Follow after users that have more then {} followers'.format(self.followers_amount)
        self.title_posts_amount['text'] = 'Follow after users who have more then {} posts '.format(data_settings[7])

    def _save_changes(self):
        database = db.Database()
        likes_amount = self.likes_amount.get()
        followers_amount = self.followers_amount_input.get()
        headless = self.headless_value.get()
        posts_amount = self.posts_amount.get()

        # Getting the data again, in order when i save only 1 thing, so i'll save the others
        # with the same value. for example, if i change only the amount of posts,
        # so i'll get others data and save it again
        data = database.get_data_from_settings()
        update_likes_amount = data[1]
        update_followers_amount = data[2]
        update_is_schedule = data[3]
        update_schedule_hour = data[4]
        update_posts_amount = data[7]

        if likes_amount != 0 and likes_amount > 0:
            update_likes_amount = likes_amount
        if followers_amount != 0 and followers_amount > 0:
            update_followers_amount = followers_amount
        if posts_amount > 0:
            update_posts_amount = posts_amount

        database.save_settings(update_likes_amount, update_followers_amount, update_is_schedule, update_schedule_hour, headless, update_posts_amount)
        messagebox.showinfo('Settings', 'Changes has been saved')
        self.likes_amount.set(0)
        self.followers_amount_input.set(0)
        self.posts_amount.set(0)
        data = database.get_data_from_settings()
        self.title_followers_amount['text'] = 'Follow after users that have more then {} followers'.format(data[2])
        self.title_amount['text'] = 'LIKE/FOLLOW/COMMENT users who has more then {} likes '.format(data[1])
        self.title_posts_amount['text'] = 'Follow after users who have more then {} posts '.format(data[7])

    def _save_distribution_list(self):
        list_name = self.distribution_list_name.get()
        username_menu = self.username_option.get()
        # If list name is not empty, than enter to this block (save the name list in db)
        if list_name and username_menu:
            database = db.Database()
            is_saved = database.create_distribution_group(list_name, username_menu)
            if is_saved:
                self.listbox.insert(END, list_name)
                self.distribution_list_name.set('')
            else:
                print('Did not saved')

    def _remove_group_from_distribution_list(self):
        username_menu = self.username_option.get()
        group_selection = self.listbox.get(self.listbox.curselection())
        if group_selection:
            database = db.Database()
            is_deleted = database.remove_group_from_distribution_list(group_selection, username_menu)
            if is_deleted:
                self.listbox.delete(self.listbox.curselection())

    def _set_users_groups(self, value):
        self.listbox.delete(0, 'end')
        distribution_groups = self.database.get_distribution_lists_by_username(value)
        for group in distribution_groups:
            self.listbox.insert(END, group[1])

    def save_proxy(self):
        is_saved = -1
        host = self.host_entry.get()
        username = self.proxy_username_entry.get()
        password = self.proxy_password_entry.get()
        port = self.proxy_port_entry.get()
        # checking if host, username... are not empty
        if not host and not username and not password and not port:
            proxy_obj = ProxyModel(host, username, password, port)
            is_saved = Proxy().save_in_db(proxy_obj)
        if is_saved:
            self.proxy_listbox.insert(END, username)
            self.host_entry.set('')
            self.proxy_username_entry.set('')
            self.proxy_password_entry.set('')
            self.proxy_port_entry.set('')

    def remove_proxy(self):
        proxy_to_remove_id = -1
        # getting proxy host name
        proxy_to_remove = self.proxy_listbox.get(self.proxy_listbox.curselection())
        proxies = self.database.get_proxy_data()
        # looping over the proxy list in order to match the right one and get his id
        for proxy in proxies:
            if proxy[2] == proxy_to_remove:
                proxy_to_remove_id = proxy[0]
        is_removed = Proxy().remove_from_db(proxy_to_remove_id)
        if is_removed:
            self.proxy_listbox.delete(self.proxy_listbox.curselection())

    def save_website(self):
        is_saved = False
        website_link = self.website_link_entry.get()
        website_obj = WebsiteModel(website_link)
        # checking if the string is not empty
        if website_link:
            is_saved = Website().save_in_db(website_obj)
        if is_saved:
            self.website_listbox.insert(END, website_link)
            self.website_link_entry.set('')

    def remove_website(self):
        website_to_remove_id = -1
        website_to_remove = self.website_listbox.get(self.website_listbox.curselection())
        websites = Website().get_websites_data()
        for website in websites:
            if website[1] == website_to_remove:
                website_to_remove_id = website[0]
        is_removed = Website().remove_from_db(website_to_remove_id)
        if is_removed:
            self.website_listbox.delete(self.website_listbox.curselection())