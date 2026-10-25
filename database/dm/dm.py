from database import db
import sqlite3
from utils.log import get_logger

log = get_logger(__name__)


class DMDB(db.Database):
    def save_in_db(self, dm_obj):
        conn = sqlite3.connect(self.database_name)
        try:
            cur = conn.cursor()
            cur.execute("""INSERT INTO dm (account, message, group_name, num_members, num_failed_members, 
            schedule, date) VALUES(?,?,?,?,?,?,?)""",
                        (dm_obj.account, dm_obj.message, dm_obj.group,
                         dm_obj.num_members, dm_obj.num_failed_members, dm_obj.schedule, dm_obj.date))
            conn.commit()
        except Exception:
            log.exception("Database: could not save the DM stats")
        finally:
            conn.close()

    def get_dm_data(self):
        data = 0
        conn = sqlite3.connect(self.database_name)
        cur = conn.cursor()
        try:
            data = cur.execute(" SELECT * FROM dm ").fetchall()
        except Exception:
            log.exception("Database: could not read the DM stats")
        finally:
            conn.close()
            return data

    def remove_dm_user_from_list(self, username, group_id):
        conn = sqlite3.connect(self.database_name)
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM dm_users WHERE username = ? AND group_id = ?", (username, group_id))
            conn.commit()
        except Exception:
            log.exception("Database: could not remove %s from DM group %s", username, group_id)
        finally:
            conn.close()