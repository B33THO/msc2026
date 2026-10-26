class Account:
    def __init__(self, idClient ,number_account, balance, createdAt):
        self.__idClient = idClient
        self.__number_account = number_account
        self.__balance = balance
        self.__createdAt = createdAt

    def getIdClient(self):
        return self.__idClient

    def getNumberAccount(self):
        return self.__number_account

    def getBalance(self):
        return self.__balance

    def getCreatedAt(self):
        return self.__createdAt

    def setCreatedAt(self, createdAt):
        self.__createdAt = createdAt

    def setBalance(self, balance):
        self.__balance = balance

    def setIdClient(self, idClient):
        self.__idClient = idClient

    def setNumberAccount(self, number_account):
        self.__number_account = number_account