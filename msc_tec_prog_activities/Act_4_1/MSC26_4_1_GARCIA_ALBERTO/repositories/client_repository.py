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
    # CREAR CLIENTE (solo junto con su cuenta, ver AccountRepository.create_with_client)
    #---------------------------------------------------------------------------------

    @staticmethod
    def insert(cur, client):
        #Ejecuta el INSERT con un cursor recibido, así otro repositorio puede registrar
        #el cliente dentro de su misma transacción (p. ej. cliente + cuenta)
        sql = """
            INSERT INTO client (paternal_surname, maternal_surname, name)
            VALUES (%s, %s, %s)
        """
        cur.execute(sql, (
            client.get_paternal_surname(),
            client.get_maternal_surname(),
            client.get_name()
        )) #Ejecuta la consulta
        client.set_id(cur.lastrowid) #Asignamos el id creado al modelo Client

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
    # ACTUALIZAR CLIENTE
    #---------------------------------------------------------------------------------

    def update(self, client):
        with self.__connection.cursor() as cur:
            updated = self.update_row(cur, client)

        return updated

    @staticmethod
    def update_row(cur, client):
        #Igual que insert: recibe el cursor para poder ir en la transacción de otro repositorio
        sql = """
            UPDATE client
            SET paternal_surname = %s, maternal_surname = %s, name = %s
            WHERE id = %s
        """
        cur.execute(sql, (
            client.get_paternal_surname(),
            client.get_maternal_surname(),
            client.get_name(),
            client.get_id()
        )) #Ejecuta la consulta
        return cur.rowcount > 0

    #---------------------------------------------------------------------------------
    # ELIMINAR CLIENTE
    #---------------------------------------------------------------------------------

    def delete(self, client_id):
        #Consulta SQL, por el ON DELETE CASCADE también se borra su cuenta
        sql = "DELETE FROM client WHERE id = %s"
        with self.__connection.cursor() as cur:
            cur.execute(sql, (client_id,)) #Ejecuta la consulta
            deleted = cur.rowcount > 0 #True si se borró algún registro

        return deleted


