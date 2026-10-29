from domain.client import Client
from repositories.client_repository import ClientRepository
from utilities.validators import validate_required_text


class ClientService:
    def __init__(self, repository = None):
        self.__repository = repository or ClientRepository()

    def _clean_names(self, paternal_surname, maternal_surname, name):
        #Valida que los tres campos tengan texto y los guarda en mayúsculas
        paternal_surname = validate_required_text(paternal_surname, 'Apellido paterno').upper()
        maternal_surname = validate_required_text(maternal_surname, 'Apellido materno').upper()
        name = validate_required_text(name, 'Nombre').upper()
        return paternal_surname, maternal_surname, name

    #--------------------------------------------------------------------------
    # CREAR CLIENTE
    #--------------------------------------------------------------------------
    def create(self, paternal_surname, maternal_surname, name):

        paternal_surname, maternal_surname, name = self._clean_names(paternal_surname, maternal_surname, name)
        client = Client(None, paternal_surname, maternal_surname, name)
        return self.__repository.create(client)

    #--------------------------------------------------------------------------
    # ACTUALIZAR CLIENTE
    #--------------------------------------------------------------------------
    def update(self, client_id, paternal_surname, maternal_surname, name):

        paternal_surname, maternal_surname, name = self._clean_names(paternal_surname, maternal_surname, name)

        #Se verifica que el cliente exista antes de actualizarlo
        client_to_update = self.__repository.get_by_id(client_id)
        if not client_to_update:
            raise ValueError('Cliente no encontrado.')
        client_to_update = Client(client_id, paternal_surname, maternal_surname, name)

        self.__repository.update(client_to_update)

        return client_to_update

    #--------------------------------------------------------------------------
    # ELIMINAR CLIENTE
    #--------------------------------------------------------------------------
    def delete(self, client_id):

         client_to_delete = self.__repository.get_by_id(client_id)

         if not client_to_delete:
            raise ValueError('Cliente no encontrado.')

         self.__repository.delete(client_to_delete.get_id())

         return client_to_delete