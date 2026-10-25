from database import db
import sqlite3
from utils.log import get_logger

log = get_logger(__name__)


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
        except Exception:
            log.exception("Database: could not save the follow-followers stats")
        finally:
            conn.close()

    def get_follow_followers_data(self):
        data = 0
        conn = sqlite3.connect(self.database_name)
        cur = conn.cursor()
        try:
            data = cur.execute(" SELECT * FROM follow_followers ").fetchall()
        except Exception:
            log.exception("Database: could not read the follow-followers stats")
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
            log.exception("Database: could not read the follow-followers stats of %s", account_name)
        finally:
            conn.close()
            return data
