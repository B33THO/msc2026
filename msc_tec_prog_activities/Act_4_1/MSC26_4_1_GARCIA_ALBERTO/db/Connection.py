import os
import mysql.connector

from contextlib import contextmanager

class Connection:
    def __init__(self):
        self.config = {
            'host':os.getenv("DB_HOST"),
            'user':os.getenv("DB_USER"),
            'password':os.getenv("DB_PASSWORD"),
            'database':os.getenv("DB_DATABASE"),
            'port': 3306
        }

    @contextmanager
    def cursor(self, dictionary = False):
        conn = mysql.connector.connect(**self.config)
        cur = conn.cursor(dictionary=dictionary)
        try:
            # yield pausa la función y entrega un valor a quien la llamó,
            # en este caso un cursor
            yield cur
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()