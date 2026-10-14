from Act_2_3.account import Account
from Act_2_3.credit_account import CreditAccount
from Act_2_3.validators import Validator


class AccountFunctions:
    def __init__(self, account):
        self.__account = account

    def create_account(self):
        try:
            while True:
                acc_num = input('Ingrese el número de cuenta: ')
                if Validator.is_positive_integer(acc_num):
                    acc_num = int(acc_num)
                else:
                    print('Ingrese un numero valido')
                    continue

                acc_name = input('Ingrese el nombre de cuenta: ')
                if Validator.is_not_empty_string(acc_name):
                    acc = Account(acc_num, acc_name, 1000)
                    return acc

        except Exception as e:
            print(e)

    def create_credit_account(self):
        try:
            while True:
                credit_amount = Validator.is_positive_float(input('Ingrese el monto de crédito: '))
                acc_num = Validator.is_positive_integer(input('Ingrese el numero de cuenta: '))
                acc_name = Validator.is_not_empty_string(input('Ingrese el nombre de cuenta: '))
                return CreditAccount(credit_amount,acc_num, acc_name, 1000 )
        except Exception as e:
            print(e)

