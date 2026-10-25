from database import db
import sqlite3
from utils.log import get_logger

log = get_logger(__name__)


class FollowersDB(db.Database):
    def save_in_db(self, followers_obj):
        try:
            conn = sqlite3.connect(self.database_name)
            cur = conn.cursor()
            cur.execute("""INSERT INTO follow_back (user_id, account, follow_back, date) VALUES(?,?,?,?)""",
                        (followers_obj.user_id, followers_obj.account, followers_obj.follow_back, followers_obj.date))
            conn.commit()
        except Exception:
            log.exception("Database: could not save the followers stats")
        finally:
            conn.close()