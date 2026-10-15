from Act_2_3.account import Account

class CreditAccount(Account):
    def __init__(self, credit_amount, acc_num, account_name, balance):
        super().__init__(acc_num, account_name, balance)
        self.__credit_amount = credit_amount

    def __str__(self):
        return super().__str__() + f', Crédito: {self.__credit_amount}'

    def get_credit_amount(self):
        return self.__credit_amount

