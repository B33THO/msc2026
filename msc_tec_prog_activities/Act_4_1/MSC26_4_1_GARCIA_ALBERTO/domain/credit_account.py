from domain.account import Account


class CreditAccount(Account):

    def __init__(self, idClient, number_account, balance, createdAt, creditLimit, debt):
        super().__init__(idClient, number_account, balance, createdAt)
        self.__creditLimit = creditLimit
        self.__debt = debt

    def getCreditLimit(self):
        return self.__creditLimit

    def getDebt(self):
        return self.__debt

    def setCreditLimit(self, creditLimit):
        self.__creditLimit = creditLimit

    def setDebt(self, debt):
        self.__debt = debt
