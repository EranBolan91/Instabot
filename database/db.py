import sqlite3
import datetime as dt


# TODO: should change all to Try and Catch
class Database:
    def __init__(self):
        self.database_name = "instabot.db"
        self.conn = sqlite3.connect(self.database_name)
        self.cur = self.conn.cursor()
        # Table accounts
        self.cur.execute(""" CREATE TABLE IF NOT EXISTS accounts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,  
                        name TEXT,
                        phone TEXT,
                        username TEXT,
                        password TEXT,
                        creation_date DATETIME,
                        last_login DATETIME)
                        """)
        # Table settings
        self.cur.execute(""" CREATE TABLE IF NOT EXISTS settings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        amount_likes TEXT DEFAULT 0,
                        amount_followers TEXT DEFAULT 0,
                        is_schedule BOOLEAN DEFAULT 0,
                        schedule_hour INT DEFAULT 0,
                        modify DATETIME)
                        """)
        # Table unfollow
        self.cur.execute(""" CREATE TABLE IF NOT EXISTS unfollow (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INT NOT NULL,
                        username TEXT NOT NULL,
                        FOREIGN KEY(user_id) REFERENCES accounts(id))
                        """)
        # Table groups
        self.cur.execute(""" CREATE TABLE IF NOT EXISTS groups (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        group_name TEXT NOT NULL,
                        user_id INT NOT NULL,
                        FOREIGN KEY(user_id) REFERENCES accounts(id))
                        """)
        # Table DM users
        self.cur.execute(""" CREATE TABLE IF NOT EXISTS dm_users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL,
                        group_id INT NOT NULL,
                        FOREIGN KEY(group_id) REFERENCES groups(id),
                        FOREIGN KEY(username) REFERENCES unfollow(username))
                        """)
        # Table Hashtag
        self.cur.execute(""" CREATE TABLE IF NOT EXISTS hashtag (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        account TEXT,
                        hashtag TEXT,
                        num_posts INT,
                        num_failed_posts INT,
                        action_like BOOLEAN,
                        action_follow BOOLEAN,
                        action_comment BOOLEAN,
                        distribution BOOLEAN,
                        group_name TEXT,
                        comment TEXT,
                        schedule BOOLEAN,
                        date DATETIME)
                        """)
        # Table Location
        self.cur.execute(""" CREATE TABLE IF NOT EXISTS location (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        account TEXT,
                        url TEXT,
                        num_posts INT,
                        num_failed_posts INT,
                        action_like BOOLEAN,
                        action_follow BOOLEAN,
                        action_comment BOOLEAN,
                        distribution BOOLEAN,
                        group_name TEXT,
                        comment TEXT,
                        schedule BOOLEAN,
                        date DATETIME)
                        """)
        # Table Follow followers
        self.cur.execute(""" CREATE TABLE IF NOT EXISTS follow_followers (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        account TEXT,
                        url TEXT,
                        num_follow INT,
                        num_failed_follow INT,
                        distribution BOOLEAN,
                        group_name TEXT,
                        schedule BOOLEAN,
                        date DATETIME,
                        skip INT)
                        """)
        # Table DM
        self.cur.execute(""" CREATE TABLE IF NOT EXISTS dm (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        account TEXT,
                        message TEXT,
                        group_name TEXT,
                        num_members INT,
                        num_failed_members INT,
                        schedule BOOLEAN,
                        date DATETIME)
                        """)
        # Table Combination
        self.cur.execute(""" CREATE TABLE IF NOT EXISTS combination (
                               id INTEGER PRIMARY KEY AUTOINCREMENT,
                               account TEXT,
                               url TEXT,
                               hashtag TEXT,
                               num_likes INT,
                               num_failed_likes INT,
                               num_followers INT,
                               num_failed_followers INT,
                               schedule BOOLEAN,
                               distribution BOOLEAN,
                               group_name TEXT,
                               date DATETIME)
                               """)

        # Table Follow back
        self.cur.execute(""" CREATE TABLE IF NOT EXISTS follow_back (
                               id INTEGER PRIMARY KEY AUTOINCREMENT,
                               user_id INT,
                               account TEXT,
                               follow_back INT,
                               date DATETIME)
                               """)

        # Table Account actions
        self.cur.execute(""" CREATE TABLE IF NOT EXISTS account_actions (
                               id INTEGER PRIMARY KEY AUTOINCREMENT,
                               user_id INT,
                               account TEXT,
                               action TEXT,
                               amount INT,
                               amount_success INT,
                               date DATETIME,
                               FOREIGN KEY(user_id) REFERENCES accounts(id))
                               """)

        # Commit changes
        self.conn.commit()
        # Close every time you finish with db
        self.conn.close()

    def save_account(self, name, phone, username, password):
        time_now = dt.datetime.now()
        conn = sqlite3.connect(self.database_name)
        cur = conn.cursor()
        cur.execute("INSERT INTO accounts (name,phone,username,password,creation_date,last_login) VALUES(?,?,?,?,?,?)",
                    (name, phone, username, password, dt.datetime.strftime(time_now, "%d/%m/%Y, %H:%M:%S"), ''))
        conn.commit()
        conn.close()
        self._init_settings()

    def _init_settings(self):
        modify_time = dt.datetime.now()
        conn = sqlite3.connect(self.database_name)
        cur = conn.cursor()
        try:
            is_exists = cur.execute("SELECT * FROM settings").fetchone()
            print("From _init_settings: {}".format(is_exists))
            if not is_exists:
                cur.execute("""INSERT INTO settings
                            (amount_likes, amount_followers, is_schedule, schedule_hour, modify)
                            VALUES(?,?,?,?,?)""", (0, 0, 0, 0, modify_time))
                conn.commit()
        except Exception as e:
            print('_init_settings func: ', e)
        finally:
            conn.close()

    def get_accounts(self):
        conn = sqlite3.connect(self.database_name)
        cur = conn.cursor()
        cur.execute("SELECT * FROM accounts")
        accounts = cur.fetchall()
        conn.commit()
        conn.close()
        return accounts

    def delete_account(self, username):
        conn = sqlite3.connect(self.database_name)
        cur = conn.cursor()
        is_deleted = False
        try:
            cur.execute("DELETE FROM accounts WHERE username='{}' ".format(str(username)))
            conn.commit()
            is_deleted = True
        except Exception as e:
            print(e)
            is_deleted = False
        finally:
            conn.close()
            return is_deleted

    def update_account(self, account_id, name, phone, username, password):
        conn = sqlite3.connect(self.database_name)
        cur = conn.cursor()
        is_update = False
        try:
            cur.execute("UPDATE accounts SET name='{}', phone='{}', username='{}', password='{}' WHERE id='{}' "
                        .format(name, phone, username, password, account_id))
            conn.commit()
            is_update = True
        except Exception as e:
            print(e)
            is_update = False
        finally:
            conn.close()
            return is_update

    def save_settings(self, likes_amount, followers_amount, schedule_hours, is_active):
        modify_time = dt.datetime.now()
        conn = sqlite3.connect(self.database_name)
        cur = conn.cursor()
        is_saved = False
        try:
            cur.execute("UPDATE settings SET amount_likes='{}',"
                        "amount_followers='{}', is_schedule='{}', schedule_hour='{}', modify='{}' WHERE id='{}' "
                        .format(likes_amount, followers_amount, is_active, schedule_hours, modify_time, 1))
            conn.commit()
            is_saved = True
        except Exception as e:
            print('save_settings func:', e)
            is_saved = False
        finally:
            conn.close()
            return is_saved

    def get_data_from_settings(self):
        conn = sqlite3.connect(self.database_name)
        cur = conn.cursor()
        try:
            cur.execute("SELECT * FROM settings WHERE id=1")
            data = cur.fetchone()
            conn.commit()
        except Exception as e:
            print(e)
        finally:
            conn.close()
            return data

    def save_unfollow_users(self, user, account_username):
        user_id = self.get_user_id(account_username)
        conn = sqlite3.connect(self.database_name)
        cur = conn.cursor()
        try:
            cur.execute('INSERT INTO unfollow(user_id, username) VALUES(?,?)', (user_id, user))
            conn.commit()
        except Exception as e:
            print(e)
        finally:
            conn.close()

    def get_unfollow_users(self, username):
        user_id = self.get_user_id(username)
        conn = sqlite3.connect(self.database_name)
        cur = conn.cursor()
        users = []
        try:
            cur.execute("SELECT * FROM unfollow WHERE user_id='{}'".format(user_id))
            users = cur.fetchall()
        except Exception as e:
            print(e)
        finally:
            conn.close()
            return users

    def get_user_id(self, username):
        conn = sqlite3.connect(self.database_name)
        cur = conn.cursor()
        user_id = -1
        try:
            cur.execute("SELECT id FROM accounts WHERE username='{}'".format(username))
            user_id = cur.fetchone()
        except Exception as e:
            print(e)

        finally:
            conn.close()
            # It return Tuple user_id(id)
            return user_id[0]

    def create_distribution_group(self, group_name, username):
        is_saved = False
        user_id = self.get_user_id(username)
        conn = sqlite3.connect(self.database_name)
        cur = conn.cursor()
        try:
            cur.execute('INSERT INTO groups(group_name, user_id) VALUES(?,?)', (group_name, user_id))
            conn.commit()
            is_saved = True
        except Exception as e:
            print("Create distribution group func: ", e)
        finally:
            conn.close()
            return is_saved

    def get_distribution_lists_by_username(self, username):
        user_id = self.get_user_id(username)
        conn = sqlite3.connect(self.database_name)
        cur = conn.cursor()
        try:
            cur.execute("SELECT * FROM groups WHERE user_id={}".format(user_id))
            groups = cur.fetchall()
        except Exception as e:
            print("get distribution lists by username ", e)
        finally:
            conn.close()
            return groups

    def remove_group_from_distribution_list(self, group_name, owner_username):
        owner_group_id = self.get_user_id(owner_username)
        is_deleted = False
        conn = sqlite3.connect(self.database_name)
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM groups WHERE group_name='{}' AND user_id='{}'".format(group_name, owner_group_id))
            conn.commit()
            is_deleted = True
        except Exception as e:
            print("remove group from distribution list: ", e)
        finally:
            conn.close()
            return is_deleted

    def add_username_to_distribution_group(self, user, group_id):
        conn = sqlite3.connect(self.database_name)
        cur = conn.cursor()
        try:
            cur.execute('INSERT INTO dm_users(username, group_id) VALUES(?,?)', (user, group_id))
            conn.commit()
        except Exception as e:
            print("add username to distribution group: ", e)
        finally:
            conn.close()

    def remove_username_from_unfollow_list(self, username, user_id):
        conn = sqlite3.connect(self.database_name)
        cur = conn.cursor()
        try:
            cur.execute(" DELETE FROM unfollow WHERE username='{}' AND user_id={} ".format(username, user_id))
            conn.commit()
        except Exception as e:
            print('remove username from distribution group: ', e)
        finally:
            conn.close()

    def get_group_id_by_group_name_and_id(self, group_name, owner_group_name):
        owner_group_id = self.get_user_id(owner_group_name)
        conn = sqlite3.connect(self.database_name)
        cur = conn.cursor()
        group_id = -1
        try:
            cur.execute(
                "SELECT id FROM groups WHERE group_name = '{}' AND user_id='{}' ".format(group_name, owner_group_id))
            group_id = cur.fetchone()
        except Exception as e:
            print("get group id by group name: ", e)
        finally:
            conn.close()
            return group_id[0]

    # Getting all the users name from DM_users to a specific group
    def get_users_from_dm_users(self, group_name, owner_group_name):
        group_id = self.get_group_id_by_group_name_and_id(group_name, owner_group_name)
        conn = sqlite3.connect(self.database_name)
        cur = conn.cursor()
        dm_users = []
        try:
            cur.execute("SELECT username FROM dm_users WHERE group_id={}".format(group_id))
            dm_users = cur.fetchall()
        except Exception as e:
            print("get users from dm users ", e)
        finally:
            conn.close()
            return dm_users

    def save_data_account_action(self, data_action):
        conn = sqlite3.connect(self.database_name)
        cur = conn.cursor()
        try:
            cur.execute(
                'INSERT INTO account_actions(user_id, account, action, amount,amount_success, date) VALUES(?,?,?,?,?,?)',
                (data_action.user_id, data_action.username, data_action.action, data_action.amount,
                 data_action.amount_success, data_action.date))
            conn.commit()
        except Exception as e:
            print("Database Error: save data account action: ", e)
        finally:
            conn.close()

