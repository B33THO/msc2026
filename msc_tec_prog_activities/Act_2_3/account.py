from Act_2_3.colors import Color


class Account:
    def __init__(self, acc_num, account_name, balance):
        self.__acc_num = acc_num
        self.__account_name = account_name
        self.__balance = balance

    def deposit(self, amount):
        self.__balance += amount

    def withdraw(self, amount):
        self.__balance -= amount

    def get_balance(self):
        return self.__balance

    def get_acc_num(self):
        return self.__acc_num

    def get_account_name(self):
        return self.__account_name

    def get_account_name(self):
        return self.__account_name

    def set_balance(self, balance):
        self.__balance = balance

    def set_acc_num(self, acc_num):
        self.__acc_num = acc_num

    def set_account_name(self, account_name):
        self.__account_name = account_name

    def __str__(self):
        return f'Cuenta No: {self.__acc_num} Account Name: {self.__account_name}, Balance: {self.__balance}'