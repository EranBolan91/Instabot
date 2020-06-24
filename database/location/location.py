from database import db
import sqlite3


class LocationDB(db.Database):
    def save_in_db(self, location_obj):
        try:
            conn = sqlite3.connect(self.database_name)
            cur = conn.cursor()
            cur.execute("""INSERT INTO location (account, url, num_posts, num_failed_posts, action_like, 
            action_follow, action_comment, distribution, group_name, comment,  schedule, date) VALUES(?,?,?,?,?,?,?,
            ?,?,?,?,?)""",
                        (location_obj.account, location_obj.url, location_obj.num_posts,
                         location_obj.num_failed_posts,
                         location_obj.action_like, location_obj.action_follow, location_obj.action_comment,
                         location_obj.distribution, location_obj.group_name, location_obj.comment,
                         location_obj.schedule, location_obj.date))
            conn.commit()
        except Exception as e:
            print('save_in_db_location: ', e)
        finally:
            conn.close()

    def get_location_data(self):
        data = 0
        try:
            data = self.cur.execute(" SELECT * FROM location ").fetchall()
        except Exception as e:
            print('get location data: ', e)
        finally:
            return data
