from flask_login import UserMixin
from ..db import get_db_connection

class User(UserMixin):
    def __init__(self, id, user_name, is_admin):
        self.id = id
        self.user_name = user_name
        self.is_admin = is_admin

    @staticmethod
    def get(user_id):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT user_id, user_name, is_admin
            FROM login_data WHERE user_id=%s
        """, (user_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()

        return User(*row) if row else None
