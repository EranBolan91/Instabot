from database import db
import sqlite3


class DMDB(db.Database):
    def save_in_db(self, dm_obj):
        try:
            conn = sqlite3.connect(self.database_name)
            cur = conn.cursor()
            cur.execute("""INSERT INTO dm (account, message, group, num_members, num_failed_members, 
            schedule, date) VALUES(?,?,?,?,?,?,?,?)""",
                        (dm_obj.account, dm_obj.message, dm_obj.group,
                         dm_obj.num_members, dm_obj.num_failed_members, dm_obj.schedule, dm_obj.date))
            conn.commit()
        except Exception as e:
            print('save_in_db_dm: ', e)
        finally:
            conn.close()

    def get_dm_data(self):
        data = 0
        try:
            data = self.cur.execute(" SELECT * FROM dm ").fetchall()
        except Exception as e:
            print('get_dm_data: ', e)
        finally:
            return data
