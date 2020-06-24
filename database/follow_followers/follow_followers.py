from database import db
import sqlite3


class FollowFollowersDB(db.Database):
    def save_in_db(self, follow_obj):
        try:
            conn = sqlite3.connect(self.database_name)
            cur = conn.cursor()
            cur.execute("""INSERT INTO follow_followers (account, url, num_follow, num_failed_follow, distribution, 
            schedule, date) VALUES(?,?,?,?,?,?,?)""",
                        (follow_obj.account, follow_obj.url, follow_obj.num_follow,
                         follow_obj.num_failed_follow,
                         follow_obj.distribution, follow_obj.schedule, follow_obj.date))
            conn.commit()
        except Exception as e:
            print('save_in_db_follow_followers: ', e)
        finally:
            conn.close()

    def get_follow_followers_data(self):
        data = 0
        try:
            data = self.cur.execute(" SELECT * FROM follow_followers ").fetchall()
        except Exception as e:
            print('get follow_followers data: ', e)
        finally:
            return data
