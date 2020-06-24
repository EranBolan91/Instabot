from database import db
import sqlite3


class HashtagDB(db.Database):
    def save_in_db(self, hashtag_obj):
        try:
            conn = sqlite3.connect(self.database_name)
            cur = conn.cursor()
            cur.execute("""INSERT INTO hashtag (account, hashtag, num_posts, num_failed_posts, action_like, 
            action_follow, action_comment, distribution, group_name, comment,  schedule, date) VALUES(?,?,?,?,?,?,?,
            ?,?,?,?,?)""",
                        (hashtag_obj.account, hashtag_obj.hashtag, hashtag_obj.num_posts,
                         hashtag_obj.num_failed_posts,
                         hashtag_obj.action_like, hashtag_obj.action_follow, hashtag_obj.action_comment,
                         hashtag_obj.distribution, hashtag_obj.group_name, hashtag_obj.comment,
                         hashtag_obj.schedule, hashtag_obj.date))
            conn.commit()
        except Exception as e:
            print('save_in_db_hashtag: ', e)
        finally:
            conn.close()

    def get_hashtag_data(self):
        data = 0
        try:
            data = self.cur.execute(" SELECT * FROM hashtag ").fetchall()
        except Exception as e:
            print('get hashtag data: ', e)
        finally:
            return data
