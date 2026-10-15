from decimal import Decimal


class InsufficientFundsError(Exception):
    """Se lanza cuando un retiro supera los fondos disponibles de la cuenta."""


class Account:
    # Los montos se guardan como Decimal para evitar errores de redondeo de float
    def __init__(self, acc_num, account_name, balance=Decimal('1000')):
        self.__acc_num = acc_num
        self.__account_name = account_name
        self.__balance = Decimal(balance)

    @staticmethod
    def _check_amount(amount):
        if amount <= 0:
            raise ValueError('El monto debe ser mayor que 0')

    def deposit(self, amount):
        self._check_amount(amount)
        self.__balance += amount
        return self.__balance

    def withdraw(self, amount):
        self._check_amount(amount)
        if amount > self.__balance:
            raise InsufficientFundsError('Saldo insuficiente')
        self.__balance -= amount
        return self.__balance

    def balance_after_deposit(self, amount):
        """Saldo que quedaría después de depositar amount, sin modificar la cuenta."""
        return self.__balance + amount

    def get_balance(self):
        return self.__balance

    def get_acc_num(self):
        return self.__acc_num

    def set_balance(self, balance):
        self.__balance = balance

    def __str__(self):
        return f'Cuenta No: {self.__acc_num}, Cliente: {self.__account_name}, Saldo: {self.__balance:.2f}'
