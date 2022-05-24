from database import db
import sqlite3


class FollowBackDB(db.Database):
    def save_in_db(self, follow_obj):
        try:
            conn = sqlite3.connect(self.database_name)
            cur = conn.cursor()
            cur.execute("""INSERT INTO follow_back (used_id, account, follow_back, date) VALUES(?,?,?,?)""",
                        (follow_obj.used_id, follow_obj.account, follow_obj.follow_back, follow_obj.date))
            conn.commit()
        except Exception as e:
            print('save_in_db_follow_back: ', e)
        finally:
            conn.close()

    def get_follow_back_data(self):
        data = 0
        conn = sqlite3.connect(self.database_name)
        cur = conn.cursor()
        try:
            data = cur.execute(" SELECT * FROM follow_back ").fetchall()
        except Exception as e:
            print('get follow_back data: ', e)
        finally:
            conn.close()
            return data

    def get_account_data(self, account_name):
        data = 0
        conn = sqlite3.connect(self.database_name)
        cur = conn.cursor()
        try:
            data = cur.execute(" SELECT * FROM follow_followers WHERE account= '{}' ".format(account_name)).fetchall()
        except Exception as e:
            print('follow_followers: get account data: ', e)
        finally:
            conn.close()
            return data
