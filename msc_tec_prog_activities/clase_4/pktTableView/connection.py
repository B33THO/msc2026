import psycopg2
from PyQt6.QtGui import QStandardItem
from PyQt6.QtWidgets import QMessageBox
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

class Connection:
    def __init__(self, host="localhost", database="mi_base_datos", user="postgres", password="tu_contraseña",
                 port=5432):
        """Inicializa los parámetros de configuración de la base de datos."""
        self.config = {
            "host": host,
            "database": database,
            "user": user,
            "password": password,
            "port": port
        }

    @staticmethod
    def __obtener_conexion(self):
        try:
            conexion = psycopg2.connect(**self.config)
            if conexion:
                print("Conectado")
                return conexion

        except Exception as e:
            QMessageBox.critical(None, "Error", f"{e}")

    def consultar(self, modelo):
        try:
            conn = self.__obtener_conexion(self)
            cursor = conn.cursor()
            sql = 'SELECT clave, nombre, carrera, municipio, edad FROM datos;'
            cursor.execute(sql)
            rows = cursor.fetchall()
            for row in rows:
                row=[QStandardItem(str(i)) for i in row]
                modelo.appendRow(row)
            return modelo
        except Exception as e:
            print(e)
        finally:
            cursor.close()
            conn.close()
