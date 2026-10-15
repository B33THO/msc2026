from Act_2_3.account import Account
from Act_2_3.colors import Color
from Act_2_3.credit_account import CreditAccount
from Act_2_3.validators import Validator


class AccountFunctions:
    def __init__(self):
        self.__accounts = [
            Account(1234, 'Alan Brito Delgado', 1000),
            CreditAccount(500,1236,'Esteban Quito Madera', 1000),
        ]

    def create_account(self):
        try:
            while True:
                acc_num = input('Ingrese el número de cuenta: ')
                if Validator.is_positive_integer(acc_num):
                    acc_num = int(acc_num)
                else:
                    continue

                acc_name = input('Ingrese el nombre de cuenta: ')
                if Validator.is_not_empty_string(acc_name):
                    acc = Account(acc_num, acc_name, 1000)
                    self.__accounts.append(acc)
                    print(f'{Color.GREEN}Cuenta creada correctamente{Color.RESET}')
                    return acc

        except Exception as e:
            print(e)

    def create_credit_account(self):
        try:
            while True:
                credit_amount = input('Ingrese el monto de crédito: ')
                if Validator.is_positive_float(credit_amount):
                    credit_amount = float(credit_amount)
                else:
                    continue
                acc_num = input('Ingrese el numero de cuenta: ')
                if Validator.is_positive_integer(acc_num):
                    acc_num = int(acc_num)
                else:
                    continue
                acc_name = input('Ingrese el nombre: ')
                if Validator.is_not_empty_string(acc_name):
                    cdt_acc = CreditAccount(credit_amount,acc_num, acc_name, 1000 )
                    self.__accounts.append(cdt_acc)
                    print(f'{Color.GREEN}Cuenta de crédito creada correctamente{Color.RESET}')
                    return cdt_acc
                else:
                    continue
        except Exception as e:
            print(e)

    def get_accounts(self):
        if not self.__accounts:
            print('No hay cuentas')
            return
        for idx, acc in enumerate(self.__accounts, start=1):
            print(f'{Color.YELLOW}{idx} - {acc}{Color.RESET}')

    def find_account(self):
        try:
            acc = self.select_account()
            if acc is None:
                print(f'{Color.RED}Cuenta no encontrada{Color.RESET}')
                return

            print(f'{Color.YELLOW}{acc}{Color.RESET}')
        except Exception as e:
            print(e)

    def select_account(self):
        try:
            while True:
                acc_num = input('Ingrese el numero de cuenta: ')
                if Validator.is_positive_integer(acc_num):
                    acc_num = int(acc_num)

                    for acc in self.__accounts:
                        if acc.get_acc_num() == acc_num:
                            return acc
                        else:
                            print('La cuenta no existe')
                    return None

        except Exception as e:
            print(e)

    def delete_account(self):
        try:
            acc_to_delete = self.select_account()
            if acc_to_delete is None:
                print(f'{Color.RED}Cuenta no encontrada{Color.RESET}')
                return

            self.__accounts.remove(acc_to_delete)
            print(f'{Color.GREEN}Cuenta eliminada{Color.RESET}')
        except Exception as e:
            print(e)

    def deposit(self):
        try:
            print(f'{Color.YELLOW}{"-"*40} Cuentas {"-"*40}{Color.RESET}')
            self.get_accounts()
            print(f'{Color.YELLOW}{"-"*89}{Color.RESET}')

            acc_selected = self.select_account()
            if acc_selected is None:
                print(f'{Color.RED}No existe una cuenta con ese número{Color.RESET}')
                return
            print(f'{Color.YELLOW}Cuenta Seleccionada: {Color.RESET}{Color.GREEN}{acc_selected}{Color.RESET}')
            dep_amount = input('Ingrese el monto de deposito: ')
            if Validator.is_positive_float(dep_amount):
                dep_amount = float(dep_amount)
                acc_selected.deposit(dep_amount)
                print(f'{Color.GREEN}Operación exitosa!{Color.RESET}')
                print(f'{Color.YELLOW}{acc_selected}{Color.RESET}')
        except Exception as e:
            print(e)

    def withdraw(self):
        try:
            print(f'{Color.YELLOW}{"-" * 40} Cuentas {"-" * 40}{Color.RESET}')
            self.get_accounts()
            print(f'{Color.YELLOW}{"-" * 89}{Color.RESET}')

            acc_selc = self.select_account()
            if acc_selc is None:
                print(f'{Color.RED}No existe una cuenta con ese número{Color.RESET}')
                return
            print(f'{Color.YELLOW}Cuenta Seleccionada: {Color.RESET}{Color.GREEN}{acc_selc}{Color.RESET}')
            wd_amount = input('Ingrese el monto da retirar: ')

            if Validator.is_positive_float(wd_amount):
                wd_amount = float(wd_amount)

                available = acc_selc.get_balance()
                if isinstance(acc_selc, CreditAccount):
                    available += acc_selc.get_credit_amount()

                if wd_amount > available:
                    print(f'{Color.RED}Saldo insuficiente{Color.RESET}')
                    return

                acc_selc.withdraw(wd_amount)
                print(f'{Color.GREEN}Operación exitosa!{Color.RESET}')
                print(f'{Color.YELLOW}{acc_selc}{Color.RESET}')

        except Exception as e:
            print(e)



