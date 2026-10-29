from decimal import Decimal, InvalidOperation

from domain.account import Account
from domain.credit_account import CreditAccount
from repositories.account_repository import AccountRepository
from repositories.client_repository import ClientRepository


class AccountService:
    def __init__(self, repository = None, client_repository = None):
        #Se pueden recibir repositorios externos (p. ej. para pruebas), si no, se crean
        self.__repository = repository or AccountRepository()
        self.__client_repository = client_repository or ClientRepository()

    @staticmethod
    def _to_amount(value, field_name):
        #MySQL regresa los DECIMAL como Decimal, y Decimal no se puede sumar con float,
        #por eso todas las cantidades se convierten a Decimal
        try:
            amount = Decimal(str(value))
        except InvalidOperation:
            raise ValueError(f'El campo {field_name} debe ser un número')

        if amount < 0:
            raise ValueError(f'El campo {field_name} no puede ser negativo')

        return amount

    @staticmethod
    def _to_positive_amount(value, field_name):
        #Igual que _to_amount pero no acepta 0 (depósitos y retiros)
        amount = AccountService._to_amount(value, field_name)
        if amount == 0:
            raise ValueError(f'El campo {field_name} debe ser mayor a 0')
        return amount

    def _get_client(self, id_client):
        client = self.__client_repository.get_by_id(id_client)
        if not client:
            raise ValueError('Cliente no encontrado')
        return client

    def _get_account(self, account_number):
        #Regresa solo la cuenta del par (Client, cuenta)
        return self.get_by_account_number(account_number)[1]

    #--------------------------------------------------------------------------
    # CREAR CUENTA DE AHORRO
    #--------------------------------------------------------------------------
    def create(self, id_client, balance, created_at):

        client = self._get_client(id_client)
        balance = self._to_amount(balance, 'Saldo inicial')

        account = Account(None, client.get_id(), balance, created_at)
        return self.__repository.create(account)

    #--------------------------------------------------------------------------
    # CREAR CUENTA DE CRÉDITO
    #--------------------------------------------------------------------------
    def create_credit_account(self, id_client, balance, created_at, credit_limit, debt = 0):

        client = self._get_client(id_client)
        balance = self._to_amount(balance, 'Saldo inicial')
        credit_limit = self._to_amount(credit_limit, 'Monto de crédito')
        #Una cuenta nueva no tiene adeudo, solo al importar desde archivo puede traer uno
        debt = self._to_amount(debt, 'Adeudo')

        if debt > credit_limit:
            raise ValueError('El adeudo no puede ser mayor al monto de crédito')

        credit_account = CreditAccount(None, client.get_id(), balance, created_at, credit_limit, debt)
        return self.__repository.create_credit_account(credit_account)

    #--------------------------------------------------------------------------
    # CONSULTAS (regresan pares (Client, cuenta))
    #--------------------------------------------------------------------------
    def get_all(self):
        return self.__repository.get_all()

    def get_by_account_number(self, account_number):
        result = self.__repository.get_by_account_number(account_number)
        if not result:
            raise ValueError('Cuenta no encontrada')
        return result

    def get_savings_accounts(self):
        return self.__repository.get_savings_accounts()

    def get_credit_accounts(self):
        return self.__repository.get_credit_accounts()

    def get_by_max_balance(self, amount):
        amount = self._to_amount(amount, 'Saldo')
        return self.__repository.get_by_max_balance(amount)

    #--------------------------------------------------------------------------
    # DEPOSITAR
    #--------------------------------------------------------------------------
    def deposit(self, account_number, amount):

        amount = self._to_positive_amount(amount, 'Monto a depositar')
        account = self._get_account(account_number)

        if isinstance(account, CreditAccount):
            #Si hay adeudo, el depósito primero paga el crédito y el resto va al saldo
            payment = min(account.get_debt(), amount)
            account.set_debt(account.get_debt() - payment)
            amount -= payment

        account.set_balance(account.get_balance() + amount)
        self.__repository.update(account)

        return account

    #--------------------------------------------------------------------------
    # RETIRAR
    #--------------------------------------------------------------------------
    def withdraw(self, account_number, amount):

        amount = self._to_positive_amount(amount, 'Monto a retirar')
        account = self._get_account(account_number)

        if isinstance(account, CreditAccount):
            #Se retira primero del saldo y luego del crédito disponible
            available_credit = account.get_credit_limit() - account.get_debt()
            if amount > account.get_balance() + available_credit:
                raise ValueError('El monto a retirar excede el saldo más el crédito disponible')

            from_balance = min(account.get_balance(), amount)
            account.set_balance(account.get_balance() - from_balance)
            #Lo que no alcanzó a cubrir el saldo se suma al adeudo
            account.set_debt(account.get_debt() + amount - from_balance)
        else:
            if amount > account.get_balance():
                raise ValueError('El monto a retirar excede el saldo de la cuenta')

            account.set_balance(account.get_balance() - amount)

        self.__repository.update(account)

        return account

    #--------------------------------------------------------------------------
    # ACTUALIZAR MONTO DE CRÉDITO
    #--------------------------------------------------------------------------
    def update_credit_limit(self, account_number, credit_limit):

        credit_limit = self._to_amount(credit_limit, 'Monto de crédito')
        account = self._get_account(account_number)

        if not isinstance(account, CreditAccount):
            raise ValueError('La cuenta no es de crédito')

        #Si el límite quedara debajo del adeudo, el crédito disponible sería negativo
        if credit_limit < account.get_debt():
            raise ValueError('El monto de crédito no puede ser menor al adeudo')

        account.set_credit_limit(credit_limit)
        self.__repository.update(account)

        return account

    #--------------------------------------------------------------------------
    # ELIMINAR CUENTA
    #--------------------------------------------------------------------------
    def delete(self, account_number):

        #get_by_account_number lanza ValueError si la cuenta no existe
        client, account_to_delete = self.get_by_account_number(account_number)
        self.__repository.delete(account_to_delete.get_account_number())

        return account_to_delete
