from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation

from domain.account import Account
from domain.credit_account import CreditAccount
from repositories.account_repository import AccountRepository
from repositories.client_repository import ClientRepository
from services.client_service import ClientService

#Fecha de apertura más antigua aceptada (MySQL DATE además no acepta años menores a 1000)
MIN_DATE = date(1900, 1, 1)
EXCEL_EPOCH = date(1899, 12, 30) #Día 0 de los números de serie de fecha de Excel
#Formatos de texto aceptados; los que traen hora son los que genera Excel al guardar CSV
DATE_FORMATS = ('%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S',
                '%d/%m/%Y', '%d/%m/%Y %H:%M', '%d/%m/%Y %H:%M:%S')
MAX_AMOUNT = Decimal('99999999.99') #Máximo que cabe en DECIMAL(10,2)


class AccountExistsError(ValueError):
    #Se lanza al crear una cuenta con un número que ya está registrado
    #(al importar permite omitir las cuentas que ya existen en lugar de duplicarlas)
    pass


class AccountService:
    def __init__(self, repository = None, client_repository = None, client_service = None):
        #Se pueden recibir repositorios externos (p. ej. para pruebas), si no, se crean
        self.__repository = repository or AccountRepository()
        self.__client_repository = client_repository or ClientRepository()
        self.__client_service = client_service or ClientService(self.__client_repository)

    @staticmethod
    def _to_amount(value, field_name):
        #MySQL regresa los DECIMAL como Decimal, y Decimal no se puede sumar con float,
        #por eso todas las cantidades se convierten a Decimal
        try:
            amount = Decimal(str(value))
        except InvalidOperation:
            raise ValueError(f'El campo {field_name} debe ser un número')

        #Decimal acepta 'NaN' e 'Infinity', que no son cantidades válidas
        if not amount.is_finite():
            raise ValueError(f'El campo {field_name} debe ser un número')
        if amount < 0:
            raise ValueError(f'El campo {field_name} no puede ser negativo')
        if amount > MAX_AMOUNT:
            raise ValueError(f'El campo {field_name} no puede ser mayor a {MAX_AMOUNT:,}')

        return amount

    @staticmethod
    def _to_account_number(value):
        #Número de cuenta escrito en un archivo: entero positivo (en XLSX puede llegar como int)
        text = str(value).strip()
        if not text.isdigit() or int(text) == 0:
            raise ValueError(f"El número de cuenta '{text}' es inválido")
        return int(text)

    @staticmethod
    def _to_positive_amount(value, field_name):
        #Igual que _to_amount pero no acepta 0 (depósitos y retiros)
        amount = AccountService._to_amount(value, field_name)
        if amount == 0:
            raise ValueError(f'El campo {field_name} debe ser mayor a 0')
        return amount

    @staticmethod
    def _to_date(value):
        #Acepta date, datetime (así llegan las fechas de un .xlsx), un número de serie de Excel
        #(celda de fecha con formato General) o texto AAAA-MM-DD / DD/MM/AAAA, con o sin hora
        if isinstance(value, datetime):
            created_at = value.date()
        elif isinstance(value, date):
            created_at = value
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            #Excel cuenta los días desde el 30/12/1899; la parte decimal es la hora
            try:
                created_at = EXCEL_EPOCH + timedelta(days=int(value))
            except OverflowError:
                raise ValueError(f"La fecha de apertura '{value}' es inválida")
        else:
            text = str(value).strip()
            for date_format in DATE_FORMATS:
                try:
                    created_at = datetime.strptime(text, date_format).date()
                    break
                except ValueError:
                    continue
            else:
                raise ValueError(f"La fecha de apertura '{text}' es inválida, usa AAAA-MM-DD o DD/MM/AAAA")

        #Una cuenta no se puede abrir en el futuro ni antes de MIN_DATE
        if created_at > date.today():
            raise ValueError('La fecha de apertura no puede ser posterior a hoy')
        if created_at < MIN_DATE:
            raise ValueError(f"La fecha de apertura no puede ser anterior a {MIN_DATE.strftime('%d/%m/%Y')}")

        return created_at

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
        account = self._build_account(client.get_id(), balance, created_at)
        return self.__repository.create(account)

    #--------------------------------------------------------------------------
    # CREAR CUENTA DE CRÉDITO
    #--------------------------------------------------------------------------
    def create_credit_account(self, id_client, balance, created_at, credit_limit, debt = 0):

        client = self._get_client(id_client)
        credit_account = self._build_account(client.get_id(), balance, created_at, credit_limit, debt)
        return self.__repository.create_credit_account(credit_account)

    #--------------------------------------------------------------------------
    # CREAR CLIENTE NUEVO CON SU CUENTA
    #--------------------------------------------------------------------------
    def create_client_with_account(self, paternal_surname, maternal_surname, name,
                                   balance, created_at, credit_limit = None, debt = 0,
                                   account_number = None):
        #Se valida todo antes de tocar la BD; credit_limit en None indica cuenta de ahorro
        client = self.__client_service.build_client(paternal_surname, maternal_surname, name)
        account = self._build_account(None, balance, created_at, credit_limit, debt)

        #Sin número de cuenta se genera uno nuevo; con número (al importar) se conserva,
        #así un archivo exportado se puede volver a importar sin duplicar cuentas
        if account_number is not None:
            account_number = self._to_account_number(account_number)
            if self.__repository.get_by_account_number(account_number):
                raise AccountExistsError(f'La cuenta {account_number} ya existe')
            account.set_account_number(account_number)

        #Cliente y cuenta se guardan en una sola transacción, regresa el par (Client, cuenta)
        return self.__repository.create_with_client(client, account)

    def _build_account(self, id_client, balance, created_at, credit_limit = None, debt = 0):
        #Valida los datos y regresa la cuenta sin número, todavía sin guardar en la BD
        balance = self._to_amount(balance, 'Saldo inicial')
        created_at = self._to_date(created_at)

        if credit_limit is None:
            return Account(None, id_client, balance, created_at)

        credit_limit = self._to_amount(credit_limit, 'Monto de crédito')
        #Una cuenta nueva no tiene adeudo, solo al importar desde archivo puede traer uno
        debt = self._to_amount(debt, 'Adeudo')

        if debt > credit_limit:
            raise ValueError('El adeudo no puede ser mayor al monto de crédito')

        return CreditAccount(None, id_client, balance, created_at, credit_limit, debt)

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

        if account.get_balance() + amount > MAX_AMOUNT:
            raise ValueError(f'El saldo de la cuenta no puede ser mayor a {MAX_AMOUNT:,}')

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

        account = self._get_account(account_number)
        self._apply_credit_limit(account, credit_limit)
        self.__repository.update(account)

        return account

    def _apply_credit_limit(self, account, credit_limit):
        #Valida el nuevo límite y lo asigna a la cuenta, todavía sin guardar en la BD
        credit_limit = self._to_amount(credit_limit, 'Monto de crédito')

        if not isinstance(account, CreditAccount):
            raise ValueError('La cuenta no es de crédito')

        #Si el límite quedara debajo del adeudo, el crédito disponible sería negativo
        if credit_limit < account.get_debt():
            raise ValueError('El monto de crédito no puede ser menor al adeudo')

        account.set_credit_limit(credit_limit)

    #--------------------------------------------------------------------------
    # ACTUALIZAR CLIENTE Y LÍMITE DE CRÉDITO (formulario de edición)
    #--------------------------------------------------------------------------
    def update_client_and_account(self, account_number, paternal_surname, maternal_surname, name,
                                  credit_limit = None):
        #Se valida todo antes de tocar la BD; credit_limit en None indica que no se cambia
        client, account = self.get_by_account_number(account_number)
        updated_client = self.__client_service.build_client(paternal_surname, maternal_surname, name)
        updated_client.set_id(client.get_id())

        if credit_limit is not None:
            self._apply_credit_limit(account, credit_limit)

        #Cliente y cuenta se guardan en una sola transacción: si falla una no cambia ninguna
        self.__repository.update_with_client(updated_client, account)

        return updated_client, account

    #--------------------------------------------------------------------------
    # ELIMINAR CUENTA
    #--------------------------------------------------------------------------
    def delete(self, account_number):

        #get_by_account_number lanza ValueError si la cuenta no existe
        client, account_to_delete = self.get_by_account_number(account_number)
        self.__repository.delete(account_to_delete.get_account_number())

        return account_to_delete
