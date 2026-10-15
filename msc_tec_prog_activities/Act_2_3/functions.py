from decimal import Decimal

from Act_2_3.account import Account, InsufficientFundsError
from Act_2_3.colors import Color
from Act_2_3.credit_account import CreditAccount
from Act_2_3.menuBuilder import MenuBuilder
from Act_2_3.validators import Validator


class AccountFunctions:
    def __init__(self):
        self.__accounts = [
            Account(1234, 'Alan Brito Delgado'),
            CreditAccount(1236, 'Esteban Quito Madera'),
        ]

    def create_account(self):
        return self.__create(Account, 'Cuenta creada correctamente')

    def create_credit_account(self):
        return self.__create(CreditAccount, 'Cuenta de crédito creada correctamente')

    def get_accounts(self):
        if not self.__accounts:
            print(f'{Color.RED}No hay cuentas{Color.RESET}')
            return
        for idx, acc in enumerate(self.__accounts, start=1):
            print(f'{Color.YELLOW}{idx} - {acc}{Color.RESET}')

    def find_account(self):
        acc = self.select_account()
        if acc is not None:
            print(f'{Color.YELLOW}{acc}{Color.RESET}')

    def select_account(self):
        """Pide un número de cuenta y devuelve la cuenta, o None si no hay cuentas, no existe o se cancela."""
        if not self.__accounts:
            print(f'{Color.RED}No hay cuentas{Color.RESET}')
            return None

        acc_num = self.__ask_account_number()
        if acc_num is None:
            return None

        acc = self.__find_by_number(acc_num)
        if acc is None:
            print(f'{Color.RED}No existe una cuenta con ese número{Color.RESET}')
        return acc

    def delete_account(self):
        acc = self.select_account()
        if acc is None:
            return

        print(f'{Color.YELLOW}{acc}{Color.RESET}')
        question = '¿Desea eliminar esta cuenta?'
        if isinstance(acc, CreditAccount) and acc.get_credit_used() > 0:
            print(f'{Color.RED}La cuenta tiene una deuda de crédito de {acc.get_credit_used():.2f}{Color.RESET}')
            question = '¿Eliminarla de todos modos?'
        if not self.__ask_yes_no(question):
            print(f'{Color.YELLOW}Eliminación cancelada{Color.RESET}')
            return

        self.__accounts.remove(acc)
        print(f'{Color.GREEN}Cuenta eliminada{Color.RESET}')

    def transaction(self):
        if self.__accounts:
            self.__display_accounts()
        acc = self.select_account()
        if acc is None:
            return

        print(f'{Color.YELLOW}Cuenta seleccionada: {Color.RESET}{Color.GREEN}{acc}{Color.RESET}')
        operations = [
            ('Depositar', lambda: self.__deposit(acc)),
            ('Retirar', lambda: self.__withdraw(acc)),
        ]
        if isinstance(acc, CreditAccount):
            operations.append(('Modificar crédito', lambda: self.__modify_credit(acc)))
        operations.append(('Regresar', MenuBuilder.back))
        MenuBuilder(operations, 'Operaciones').show()

    def __create(self, account_class, success_message):
        acc_num = self.__ask_account_number()
        while acc_num is not None and self.__find_by_number(acc_num) is not None:
            print(f'{Color.RED}Ya existe una cuenta con el número {acc_num}{Color.RESET}')
            acc_num = self.__ask_account_number()
        if acc_num is None:
            return None

        while True:
            acc_name = input('Ingrese el nombre del cliente (Enter para cancelar): ').strip()
            if not acc_name:
                print(f'{Color.YELLOW}Operación cancelada{Color.RESET}')
                return None
            if Validator.is_name(acc_name):
                break

        acc = account_class(acc_num, acc_name)
        self.__accounts.append(acc)
        print(f'{Color.GREEN}{success_message}{Color.RESET}')
        print(f'{Color.YELLOW}{acc}{Color.RESET}')
        return acc

    @staticmethod
    def __deposit(acc):
        dep_amount = AccountFunctions.__ask_amount('Ingrese el monto a depositar')
        if dep_amount is None:
            return
        if acc.balance_after_deposit(dep_amount) > Validator.MAX_AMOUNT:
            print(f'{Color.RED}El saldo no puede ser mayor que {Validator.MAX_AMOUNT:,.2f}{Color.RESET}')
            return
        acc.deposit(dep_amount)
        print(f'{Color.GREEN}Depósito realizado{Color.RESET}')
        print(f'{Color.YELLOW}{acc}{Color.RESET}')

    @staticmethod
    def __withdraw(acc):
        wd_amount = AccountFunctions.__ask_amount('Ingrese el monto a retirar')
        if wd_amount is None:
            return
        try:
            acc.withdraw(wd_amount)
        except InsufficientFundsError as error:
            print(f'{Color.RED}{error}{Color.RESET}')
        else:
            print(f'{Color.GREEN}Retiro realizado{Color.RESET}')
        print(f'{Color.YELLOW}{acc}{Color.RESET}')

    @staticmethod
    def __modify_credit(acc):
        new_limit = AccountFunctions.__ask_amount('Ingrese el nuevo límite de crédito')
        if new_limit is None:
            return
        try:
            acc.set_credit_limit(new_limit)
        except ValueError as error:
            print(f'{Color.RED}{error}{Color.RESET}')
            return
        print(f'{Color.GREEN}Nuevo límite de crédito asignado: {acc.get_credit_limit():.2f}{Color.RESET}')
        print(f'{Color.YELLOW}{acc}{Color.RESET}')

    def __find_by_number(self, acc_num):
        for acc in self.__accounts:
            if acc.get_acc_num() == acc_num:
                return acc
        return None

    @staticmethod
    def __ask_account_number():
        """Pide un número de cuenta válido; devuelve None si el usuario deja la entrada vacía para cancelar."""
        while True:
            acc_num = input('Ingrese el número de cuenta (Enter para cancelar): ').strip()
            if not acc_num:
                print(f'{Color.YELLOW}Operación cancelada{Color.RESET}')
                return None
            if Validator.is_account_number(acc_num):
                return int(acc_num)

    @staticmethod
    def __ask_amount(prompt):
        """Pide un monto válido; devuelve None si el usuario deja la entrada vacía para cancelar."""
        while True:
            amount = input(f'{prompt} (Enter para cancelar): ').strip()
            if not amount:
                print(f'{Color.YELLOW}Operación cancelada{Color.RESET}')
                return None
            if Validator.is_amount(amount):
                return Decimal(amount)

    @staticmethod
    def __ask_yes_no(prompt):
        """Pide una respuesta s/n hasta que sea válida; devuelve True para 's' y False para 'n'."""
        while True:
            answer = input(f'{prompt} (s/n): ').strip().lower()
            if answer in ('s', 'n'):
                return answer == 's'
            print(f'{Color.RED}Responda "s" o "n"{Color.RESET}')

    def __display_accounts(self):
        print(f'{Color.YELLOW}{"-" * 40} Cuentas {"-" * 40}{Color.RESET}')
        self.get_accounts()
        print(f'{Color.YELLOW}{"-" * 89}{Color.RESET}')
