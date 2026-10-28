from db.Connection import Connection
from domain.client import Client


class ClientRepository:
    def __init__(self, connection = None):
        self.__connection = connection or Connection()

    @staticmethod
    def _to_client(row):
        return Client(
            row['id'],
            row['paternalSurname'],
            row['maternalSurname'],
            row['name']
        )

    #---------------------------------------------------------------------------------
    # CREAR USUARIO
    #---------------------------------------------------------------------------------

    def create(self, client):
        #Consulta SQL
        sql = """
            INSERT INTO client (paternalSurname, maternalSurname, name) 
            VALUES (%s, %s, %s)
        """
        with self.__connection.cursor() as cur: #Se usa el cursor de la conexión
            cur.execute(sql, (
                client.getPaternalSurname(),
                client.getMaternalSurname(),
                client.getName()
            )) #Ejecuta la consulta
            client.setId(cur.lastrowid) #Asignamos el id creado al modelo Client

        return client

    #---------------------------------------------------------------------------------
    # CONSULTA POR ID
    #---------------------------------------------------------------------------------

    def get_by_id(self, id):
        #Consulta SQL
        sql = """
            SELECT id, paternalSurname, maternalSurname, name
            FROM client WHERE id = %s
        """
        #Obtiene el cursor de la conexión y regresa la fila como diccionario
        with self.__connection.cursor(dictionary=True) as cur:
            cur.execute(sql, (id,)) #Ejecuta la consulta
            row = cur.fetchone() #Asigna a row un resultado

        #Si hubo resultado, se convierte a Client y se retorna, si no, regresa None
        return self._to_client(row) if row else None

    #---------------------------------------------------------------------------------
    # CONSULTA POR NOMBRE
    #---------------------------------------------------------------------------------

    def get_by_name(self, name):
        #Consulta SQL, busca coincidencias parciales en nombre y apellidos
        sql = """
            SELECT id, paternalSurname, maternalSurname, name
            FROM client
            WHERE CONCAT_WS(' ', name, paternalSurname, maternalSurname) LIKE %s
            ORDER BY paternalSurname, maternalSurname, name
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
            SELECT id, paternalSurname, maternalSurname, name
            FROM client
            ORDER BY paternalSurname, maternalSurname, name
        """
        with self.__connection.cursor(dictionary=True) as cur:
            cur.execute(sql) #Ejecuta la consulta
            rows = cur.fetchall() #Asigna a rows todos los resultados

        return [self._to_client(row) for row in rows]

    #---------------------------------------------------------------------------------
    # ACTUALIZAR USUARIO
    #---------------------------------------------------------------------------------

    def update(self, client):
        #Consulta SQL
        sql = """
            UPDATE client
            SET paternalSurname = %s, maternalSurname = %s, name = %s
            WHERE id = %s
        """
        with self.__connection.cursor() as cur:
            cur.execute(sql, (
                client.getPaternalSurname(),
                client.getMaternalSurname(),
                client.getName(),
                client.getId()
            )) #Ejecuta la consulta
            updated = cur.rowcount > 0 #True si se encontró el cliente

        return updated

    #---------------------------------------------------------------------------------
    # ELIMINAR USUARIO
    #---------------------------------------------------------------------------------

    def delete(self, id):
        #Consulta SQL, por el ON DELETE CASCADE también se borran sus cuentas
        sql = "DELETE FROM client WHERE id = %s"
        with self.__connection.cursor() as cur:
            cur.execute(sql, (id,)) #Ejecuta la consulta
            deleted = cur.rowcount > 0 #True si se borró algún registro

        return deleted


