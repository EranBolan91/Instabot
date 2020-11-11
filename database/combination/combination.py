from database import db
import sqlite3


class CombinationDM(db.Database):
    def save_in_db(self, combo_obj):
        try:
            conn = sqlite3.connect(self.database_name)
            cur = conn.cursor()
            cur.execute("""INSERT INTO combination (account, url, hashtag, num_likes, num_failed_likes, num_followers, 
                num_failed_followers, schedule, distribution, group_name, date) VALUES(?,?,?,?,?,?,?,
                ?,?,?,?)""",
                        (combo_obj.account, combo_obj.url, combo_obj.hashtag, combo_obj.num_likes,
                         combo_obj.num_failed_likes, combo_obj.num_followers, combo_obj.num_failed_followers,
                         combo_obj.schedule, combo_obj.distribution, combo_obj.group_name, combo_obj.date))
            conn.commit()
        except Exception as e:
            print('save_in_db_combination: ', e)
        finally:
            conn.close()

    def get_combination_data(self):
        data = 0
        conn = sqlite3.connect(self.database_name)
        cur = conn.cursor()
        try:
            data = cur.execute(" SELECT * FROM combination ").fetchall()
        except Exception as e:
            print('get combination data: ', e)
        finally:
            conn.close()
            return data
