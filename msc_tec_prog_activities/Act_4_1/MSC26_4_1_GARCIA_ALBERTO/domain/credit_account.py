from domain.account import Account


#Cuenta de crédito: hereda los datos de Account y agrega el límite y el adeudo
#(tabla credit_account)
class CreditAccount(Account):

    def __init__(self, account_number, id_client, balance, created_at, credit_limit, debt):
        super().__init__(account_number, id_client, balance, created_at)
        self.__credit_limit = credit_limit
        self.__debt = debt

    def get_credit_limit(self):
        return self.__credit_limit

    def get_debt(self):
        return self.__debt

    def set_credit_limit(self, credit_limit):
        self.__credit_limit = credit_limit

    def set_debt(self, debt):
        self.__debt = debt
