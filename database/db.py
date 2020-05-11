import sqlite3
import datetime as dt

#TODO: should change all to Try and Catch
class Database:
    def __init__(self):
        self.conn = sqlite3.connect('users.db')
        self.cur = self.conn.cursor()
        # Table accounts
        self.cur.execute(""" CREATE TABLE IF NOT EXISTS accounts (
                      name TEXT,
                      phone TEXT,
                      username TEXT,
                      password TEXT,
                      creation_date DATETIME,
                      last_login DATETIME)
                    """)
        # Table settings
        self.cur.execute(""" CREATE TABLE IF NOT EXISTS settings (
                        id PRIMARY KEY,
                        amount_likes TEXT DEFAULT 0,
                        is_schedule BOOLEAN DEFAULT 0,
                        schedule_hour INT,
                        modify DATETIME )
                     """)
        # Unfollow table
        self.cur.execute(""" CREATE TABLE IF NOT EXISTS unfollow (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                username TEXT)
                         """)
        # List of comments that the user can save
        # self.cur.execute(""" CREATE TABLE IF NOT EXISTS commentsList (
        #                                 id INTEGER PRIMARY KEY AUTOINCREMENT,
        #                                 username TEXT)
        #                          """)
        # Commit changes
        self.conn.commit()
        # Close every time you finish with db
        self.conn.close()

    def register(self, username, password, email):
        time_now = dt.datetime.now()
        self.cur.execute("INSERT INTO user VALUES(?,?,?,?,?)", (username, password, email, dt.datetime.strftime(time_now,"%m/%d/%Y, %H:%M:%S"), ''))

        self.conn.commit()
        self.conn.close()

    def login(self, username, password):
        self.cur.execute("SELECT * FROM user WHERE username=(?) AND password=(?)", (username, password))
        user = self.cur.fetchone()
        self.conn.commit()
        self.conn.close()

        return user

    def save_account(self, name, phone, username, password):
        time_now = dt.datetime.now()
        conn = sqlite3.connect('users.db')
        cur = conn.cursor()
        cur.execute("INSERT INTO accounts VALUES(?,?,?,?,?,?)",
                         (name, phone, username, password, dt.datetime.strftime(time_now, "%m/%d/%Y, %H:%M:%S"), ''))
        conn.commit()
        conn.close()

    def get_accounts(self):
        conn = sqlite3.connect('users.db')
        cur = conn.cursor()
        cur.execute("SELECT * FROM accounts")
        accounts = cur.fetchall()
        conn.commit()
        conn.close()
        return accounts

    def delete_account(self, username):
        conn = sqlite3.connect('users.db')
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
        conn = sqlite3.connect('users.db')
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
        time_now = dt.datetime.now()
        conn = sqlite3.connect('users.db')
        cur = conn.cursor()
        is_saved = False
        try:
            cur.execute("INSERT OR REPLACE INTO settings (id,amount_likes,modify,is_schedule,schedule_hour) VALUES (1,'{}','{}',{},{})"
                        .format(likes_amount, time_now, is_active, schedule_hours))
            conn.commit()
            is_saved = True
        except Exception as e:
            print(e)
            is_saved = False
        finally:
            conn.close()
            return is_saved

    def get_data_from_settings(self):
        conn = sqlite3.connect('users.db')
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

    def save_unfollow_users(self, users_list):
        conn = sqlite3.connect('users.db')
        cur = conn.cursor()
        try:
            # Instead to write another function for 1 username
            # Here i check if its a list of users or only on user to save to Database
            if len(users_list) > 1:
                for user in users_list:
                    cur.execute('INSERT INTO unfollow(username) VALUES(?)', [user])
                    conn.commit()
            else:
                cur.execute('INSERT INTO unfollow(username) VALUES(?)', users_list)
                conn.commit()
        except Exception as e:
            print(e)

        finally:
            conn.close()

    def get_unfollow_users(self):
        conn = sqlite3.connect('users.db')
        cur = conn.cursor()
        users = 0
        try:
            cur.execute('SELECT * FROM unfollow')
            users = cur.fetchall()
        except Exception as e:
            print(e)

        finally:
            conn.close()
            return users
