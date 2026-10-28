class Account:
    def __init__(self, id_client, account_number, balance, created_at):
        self.__id_client = id_client
        self.__account_number = account_number
        self.__balance = balance
        self.__created_at = created_at

    def get_id_client(self):
        return self.__id_client

    def get_account_number(self):
        return self.__account_number

    def get_balance(self):
        return self.__balance

    def get_created_at(self):
        return self.__created_at

    def set_created_at(self, created_at):
        self.__created_at = created_at

    def set_balance(self, balance):
        self.__balance = balance

    def set_id_client(self, id_client):
        self.__id_client = id_client

    def set_account_number(self, account_number):
        self.__account_number = account_number