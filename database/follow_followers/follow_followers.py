from database import db
import sqlite3


class FollowFollowersDB(db.Database):
    def save_in_db(self, follow_obj):
        try:
            conn = sqlite3.connect(self.database_name)
            cur = conn.cursor()
            cur.execute("""INSERT INTO follow_followers (account, url, num_follow, num_failed_follow,
            distribution, group_name, schedule, date, skip) VALUES(?,?,?,?,?,?,?,?,?)""",
                        (follow_obj.account, follow_obj.url, follow_obj.num_follow,
                         follow_obj.num_failed_follow,
                         follow_obj.distribution, follow_obj.group_name, follow_obj.schedule, follow_obj.date, follow_obj.skip))
            conn.commit()
        except Exception as e:
            print('save_in_db_follow_followers: ', e)
        finally:
            conn.close()

    def get_follow_followers_data(self):
        data = 0
        conn = sqlite3.connect(self.database_name)
        cur = conn.cursor()
        try:
            data = cur.execute(" SELECT * FROM follow_followers ").fetchall()
        except Exception as e:
            print('get follow_followers data: ', e)
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
