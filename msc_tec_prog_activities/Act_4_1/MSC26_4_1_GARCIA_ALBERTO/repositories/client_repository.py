from db.connection import Connection
from domain.client import Client


class ClientRepository:
    def __init__(self, connection = None):
        self.__connection = connection or Connection()

    @staticmethod
    def _to_client(row):
        return Client(
            row['id'],
            row['paternal_surname'],
            row['maternal_surname'],
            row['name']
        )

    #---------------------------------------------------------------------------------
    # CREAR CLIENTE
    #---------------------------------------------------------------------------------

    def create(self, client):
        #Consulta SQL
        sql = """
            INSERT INTO client (paternal_surname, maternal_surname, name) 
            VALUES (%s, %s, %s)
        """
        with self.__connection.cursor() as cur: #Se usa el cursor de la conexión
            cur.execute(sql, (
                client.get_paternal_surname(),
                client.get_maternal_surname(),
                client.get_name()
            )) #Ejecuta la consulta
            client.set_id(cur.lastrowid) #Asignamos el id creado al modelo Client

        return client

    #---------------------------------------------------------------------------------
    # CONSULTA POR ID
    #---------------------------------------------------------------------------------

    def get_by_id(self, client_id):
        #Consulta SQL
        sql = """
            SELECT id, paternal_surname, maternal_surname, name
            FROM client WHERE id = %s
        """
        #Obtiene el cursor de la conexión y regresa la fila como diccionario
        with self.__connection.cursor(dictionary=True) as cur:
            cur.execute(sql, (client_id,)) #Ejecuta la consulta
            row = cur.fetchone() #Asigna a row un resultado

        #Si hubo resultado, se convierte a Client y se retorna, si no, regresa None
        return self._to_client(row) if row else None

    #---------------------------------------------------------------------------------
    # CONSULTA POR NOMBRE
    #---------------------------------------------------------------------------------

    def get_by_name(self, name):
        #Consulta SQL, busca coincidencias parciales en nombre y apellidos
        sql = """
            SELECT id, paternal_surname, maternal_surname, name
            FROM client
            WHERE CONCAT_WS(' ', name, paternal_surname, maternal_surname) LIKE %s
            ORDER BY paternal_surname, maternal_surname, name
        """
        with self.__connection.cursor(dictionary=True) as cur:
            cur.execute(sql, (f"%{name}%",)) #El % permite buscar texto contenido
            rows = cur.fetchall() #Asigna a rows todos los resultados

        #Convierte cada fila a Client, si no hubo resultados regresa una lista vacía
        return [self._to_client(row) for row in rows]

    #---------------------------------------------------------------------------------
    # CONSULTAR TODOS
    #---------------------------------------------------------------------------------

    def get_all(self):
        #Consulta SQL
        sql = """
            SELECT id, paternal_surname, maternal_surname, name
            FROM client
            ORDER BY paternal_surname, maternal_surname, name
        """
        with self.__connection.cursor(dictionary=True) as cur:
            cur.execute(sql) #Ejecuta la consulta
            rows = cur.fetchall() #Asigna a rows todos los resultados

        return [self._to_client(row) for row in rows]

    #---------------------------------------------------------------------------------
    # ACTUALIZAR CLIENTE
    #---------------------------------------------------------------------------------

    def update(self, client):
        #Consulta SQL
        sql = """
            UPDATE client
            SET paternal_surname = %s, maternal_surname = %s, name = %s
            WHERE id = %s
        """
        with self.__connection.cursor() as cur:
            cur.execute(sql, (
                client.get_paternal_surname(),
                client.get_maternal_surname(),
                client.get_name(),
                client.get_id()
            )) #Ejecuta la consulta
            updated = cur.rowcount > 0

        return updated

    #---------------------------------------------------------------------------------
    # ELIMINAR CLIENTE
    #---------------------------------------------------------------------------------

    def delete(self, client_id):
        #Consulta SQL, por el ON DELETE CASCADE también se borran sus cuentas
        sql = "DELETE FROM client WHERE id = %s"
        with self.__connection.cursor() as cur:
            cur.execute(sql, (client_id,)) #Ejecuta la consulta
            deleted = cur.rowcount > 0 #True si se borró algún registro

        return deleted


