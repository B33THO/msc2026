class Account:
    def __init__(self, acc_num, account_name, balance):
        self.__acc_num = acc_num
        self.__account_name = account_name
        self.__balance = balance

    def deposit(self, amount):
        self.__balance += amount

    def withdraw(self, amount):
        self.__balance -= amount

    def set_balance(self, balance):
        self.__balance = balance

    def get_balance(self):
        return self.__balance