from Act_2_3.account import Account

class CreditAccount(Account):
    def __init__(self, credit_amount, acc_num, account_name, balance):
        super().__init__(acc_num, account_name, balance)
        self.__credit_amount = credit_amount

