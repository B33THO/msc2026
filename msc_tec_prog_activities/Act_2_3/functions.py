from Act_2_3.account import Account
from Act_2_3.colors import Color
from Act_2_3.credit_account import CreditAccount
from Act_2_3.validators import Validator


class AccountFunctions:
    def __init__(self):
        self.__accounts = [
            Account(1234, 'Alan Brito', 1000),
            CreditAccount(500,1236,'Esteban Quito', 1000),
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
                    credit_amount = int(credit_amount)
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
        for acc in self.__accounts:
            print(f'{Color.YELLOW}{acc}{Color.RESET}')
