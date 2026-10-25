from database import db
import sqlite3
from utils.log import get_logger

log = get_logger(__name__)


class FollowBackDB(db.Database):
    def save_in_db(self, follow_obj):
        try:
            conn = sqlite3.connect(self.database_name)
            cur = conn.cursor()
            cur.execute("""INSERT INTO follow_back (used_id, account, follow_back, date) VALUES(?,?,?,?)""",
                        (follow_obj.used_id, follow_obj.account, follow_obj.follow_back, follow_obj.date))
            conn.commit()
        except Exception:
            log.exception("Database: could not save the follow-back stats")
        finally:
            conn.close()

    def get_follow_back_data(self):
        data = 0
        conn = sqlite3.connect(self.database_name)
        cur = conn.cursor()
        try:
            data = cur.execute(" SELECT * FROM follow_back ").fetchall()
        except Exception:
            log.exception("Database: could not read the follow-back stats")
        finally:
            conn.close()
            return data

    def get_account_data(self, account_name):
        data = 0
        conn = sqlite3.connect(self.database_name)
        cur = conn.cursor()
        try:
            data = cur.execute(" SELECT * FROM follow_followers WHERE account = ? ", (account_name,)).fetchall()
        except Exception:
            log.exception("Database: could not read the follow-back stats of %s", account_name)
        finally:
            conn.close()
            return data
