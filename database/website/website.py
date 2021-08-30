from database import db
import sqlite3


class Website(db.Database):
    def save_in_db(self, website_obj):
        is_saved = False
        try:
            conn = sqlite3.connect(self.database_name)
            cur = conn.cursor()
            cur.execute("""INSERT INTO website (website, modify) VALUES(?,?)""",
                        (website_obj.website, website_obj.modify))
            conn.commit()
            is_saved = True
        except Exception as e:
            print('save_in_db_website: ', e)
        finally:
            conn.close()
            return is_saved

    def remove_from_db(self, website_id):
        is_removed = False
        try:
            conn = sqlite3.connect(self.database_name)
            cur = conn.cursor()
            cur.execute("DELETE FROM website WHERE id='{}' ".format(website_id))
            conn.commit()
            is_removed = True
        except Exception as e:
            print('save_in_db_website: ', e)
        finally:
            conn.close()
            return is_removed


