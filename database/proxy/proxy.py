from database import db
import sqlite3


class Proxy(db.Database):
    def save_in_db(self, proxy_obj):
        try:
            conn = sqlite3.connect(self.database_name)
            cur = conn.cursor()
            cur.execute("""INSERT INTO proxy (host, username, password, port) VALUES(?,?,?,?)""",
                        (proxy_obj.host, proxy_obj.username, proxy_obj.password, proxy_obj.port))
            conn.commit()
        except Exception as e:
            print('save_in_db_proxy: ', e)
        finally:
            conn.close()

    def get_proxy_data(self):
        data = 0
        conn = sqlite3.connect(self.database_name)
        cur = conn.cursor()
        try:
            data = cur.execute(" SELECT * FROM proxy ").fetchall()
        except Exception as e:
            print('get proxy data: ', e)
        finally:
            conn.close()
            return data
