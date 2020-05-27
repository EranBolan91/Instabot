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
                        is_schedule BOOLEAN DEFAULT 0,
                        schedule_hour INT,
                        modify DATETIME )
                     """)
        # Init settings for first time
        # self.cur.execute(""" INSERT OR REPLACE INTO settings (amount_likes, is_schedule, schedule_hour)
        #                 VALUES(0,0,0)
        #                 """)
        # Table unfollow
        self.cur.execute(""" CREATE TABLE IF NOT EXISTS unfollow (
                         id INT PRIMARY KEY AUTOINCREMENT,
                         user_id INT,
                         username TEXT,
                         FOREIGN KEY(user_id) REFERENCES accounts(id))
                     """)
        # Table groups
        self.cur.execute(""" CREATE TABLE IF NOT EXISTS groups (
                         id INTEGER PRIMARY KEY AUTOINCREMENT,
                         group_name TEXT,
                         user_id INT,
                         FOREIGN KEY(user_id) REFERENCES accounts(id))
                     """)
        # Table DM users
        self.cur.execute(""" CREATE TABLE IF NOT EXISTS dm_users (
                         id INTEGER PRIMARY KEY AUTOINCREMENT,
                         username TEXT,
                         group_id INT,
                         FOREIGN KEY(group_id) REFERENCES groups(id))
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
                         (name, phone, username, password, dt.datetime.strftime(time_now, "%m/%d/%Y, %H:%M:%S"), ''))
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
                            (amount_likes, is_schedule, schedule_hour, modify)
                            VALUES(?,?,?,?)""", (0, 0, 0, modify_time))
        except Exception as e:
            print('_init_settings func: ', e)
        finally:
            conn.commit()
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

    def update_account(self, name, phone, username, password):
        conn = sqlite3.connect(self.database_name)
        cur = conn.cursor()
        is_update = False
        try:
            cur.execute("UPDATE accounts SET name='{}', phone='{}', username='{}', password='{}' WHERE username='{}' "
                        .format(name, phone, username, password, username))
            conn.commit()
            is_update = True
        except Exception as e:
            print(e)
            is_update = False
        finally:
            conn.close()
            return is_update

    def save_settings(self, likes_amount, schedule_hours, is_active):
        modify_time = dt.datetime.now()
        conn = sqlite3.connect(self.database_name)
        cur = conn.cursor()
        is_saved = False
        try:
            cur.execute("UPDATE settings SET amount_likes='{}', is_schedule='{}', schedule_hour='{}', modify='{}' WHERE id='{}' "
                        .format(likes_amount, is_active, schedule_hours, modify_time, 1))
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

    def save_unfollow_users(self, users_list, username):
        # TODO: Need to fix this method
        # user_id is a tuple - thats why i code user_id[0]
        user_id = self._get_user_id(username)
        print(user_id[0])
        conn = sqlite3.connect(self.database_name)
        cur = conn.cursor()
        try:
            # Instead to write another function for 1 username
            # Here i check if its a list of users or only one user to save to Database
            if len(users_list) > 1:
                for user in users_list:
                    cur.execute('INSERT INTO unfollow(user_id, username) VALUES(?,?)', (user_id[0], [user]))
                    conn.commit()
                    print("{} User saved in the database".format(user))
            else:
                cur.execute('INSERT INTO unfollow(user_id, username) VALUES(?,?)', (user_id[0], users_list[0]))
                conn.commit()
        except Exception as e:
            print(e)

        finally:
            conn.close()

    def get_unfollow_users(self, username):
        user_id = self._get_user_id(username)
        conn = sqlite3.connect(self.database_name)
        cur = conn.cursor()
        users = 0
        try:
            cur.execute("SELECT * FROM unfollow WHERE user_id='{}'".format(user_id))
            users = cur.fetchall()
        except Exception as e:
            print(e)
        finally:
            conn.close()
            return users

    def _get_user_id(self, username):
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
            return user_id
