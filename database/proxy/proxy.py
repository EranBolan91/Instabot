from database import db
import sqlite3


class Proxy(db.Database):
    def save_in_db(self, proxy_obj):
        is_saved = False
        try:
            conn = sqlite3.connect(self.database_name)
            cur = conn.cursor()
            cur.execute("""INSERT INTO proxy (host, username, password, port) VALUES(?,?,?,?)""",
                        (proxy_obj.host, proxy_obj.username, proxy_obj.password, proxy_obj.port))
            conn.commit()
            is_saved = True
        except Exception as e:
            print('save_in_db_proxy: ', e)
        finally:
            conn.close()
            return is_saved

    def remove_from_db(self, proxy_id):
        is_removed = False
        try:
            conn = sqlite3.connect(self.database_name)
            cur = conn.cursor()
            cur.execute("DELETE FROM proxy WHERE id='{}' ".format(proxy_id))
            conn.commit()
            is_removed = True
        except Exception as e:
            print('save_in_db_proxy: ', e)
        finally:
            conn.close()
            return is_removed
