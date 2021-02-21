from database import db
import sqlite3


class FollowersDB(db.Database):
    def save_in_db(self, followers_obj):
        try:
            conn = sqlite3.connect(self.database_name)
            cur = conn.cursor()
            cur.execute("""INSERT INTO follow_back (user_id, account, follow_back, date) VALUES(?,?,?,?)""",
                        (followers_obj.user_id, followers_obj.account, followers_obj.follow_back, followers_obj.date))
            conn.commit()
        except Exception as e:
            print('save_in_db_followers: ', e)
        finally:
            conn.close()