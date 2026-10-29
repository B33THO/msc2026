import os
import mysql.connector

from contextlib import contextmanager

class Connection:
    def __init__(self):
        #Los datos de conexión se leen del .env (cargado en main.py)
        self.config = {
            'host':os.getenv("DB_HOST"),
            'user':os.getenv("DB_USER"),
            'password':os.getenv("DB_PASSWORD"),
            'database':os.getenv("DB_DATABASE"),
            'port': 3306
        }

    @contextmanager
    def cursor(self, dictionary = False):
        #Se abre una conexión nueva por cada bloque with; dictionary=True regresa
        #cada fila como diccionario {columna: valor}
        conn = mysql.connector.connect(**self.config)
        cur = conn.cursor(dictionary=dictionary)
        try:
            # yield pausa la función y entrega un valor a quien la llamó,
            # en este caso un cursor
            yield cur
            conn.commit() #Si el bloque with terminó sin errores se guardan los cambios
        except Exception:
            conn.rollback() #Si hubo error se deshacen y se relanza la excepción
            raise
        finally: #Siempre se cierran cursor y conexión
            cur.close()
            conn.close()