from domain.account import Account
from repositories.account_repository import AccountRepository
from repositories.client_repository import ClientRepository


class AccountService:
    def __init__(self, repository = None, client_repository = None):
        self.__repository = repository or AccountRepository()
        self.__client_repository = client_repository or ClientRepository()

    def create_account(self, id_client, balance, created_at):

        client = self.__client_repository.get_by_id(id_client)
        if not client:
            raise ValueError('Cliente no encontrado')

        if balance > 0:
            raise ValueError('El monto inicial debe ser  mayor a 0')

        account = Account(None, client.get_id(), balance, created_at)
        return self.__repository.create(account)
