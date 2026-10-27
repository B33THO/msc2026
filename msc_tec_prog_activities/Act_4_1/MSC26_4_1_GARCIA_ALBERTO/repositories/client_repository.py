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


