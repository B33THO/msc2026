from decimal import Decimal

from MSC26_2_3_GARCIA_ALBERTO.account import Account, InsufficientFundsError


class CreditAccount(Account):
    def __init__(self, acc_num, account_name, balance=Decimal('1000')):
        super().__init__(acc_num, account_name, balance)
        self.__credit_limit = Decimal('500')
        self.__credit_used = Decimal('0')

    def deposit(self, amount):
        self._check_amount(amount)
        # El depósito paga primero la deuda de crédito y el resto va al saldo
        payment = min(amount, self.__credit_used)
        self.__credit_used -= payment
        remainder = amount - payment
        if remainder > 0:
            return super().deposit(remainder)
        return self.get_balance()

    def withdraw(self, amount):
        self._check_amount(amount)
        balance = self.get_balance()
        if amount <= balance:
            return super().withdraw(amount)

        if amount > balance + self.get_credit_amount():
            raise InsufficientFundsError('Saldo y crédito insuficiente')
        self.__credit_used += amount - balance
        self._set_balance(Decimal('0'))
        return self.get_balance()

    def balance_after_deposit(self, amount):
        # Solo lo que sobra después de pagar la deuda aumenta el saldo
        return self.get_balance() + max(amount - self.__credit_used, Decimal('0'))

    def __str__(self):
        return (super().__str__() + f', Límite de crédito: {self.__credit_limit:.2f}'
                f', Crédito disponible: {self.get_credit_amount():.2f}, Deuda: {self.__credit_used:.2f}')

    def get_credit_amount(self):
        return self.__credit_limit - self.__credit_used

    def get_credit_limit(self):
        return self.__credit_limit

    def set_credit_limit(self, credit_limit):
        if credit_limit < 0:
            raise ValueError('El límite de crédito no puede ser negativo')
        if credit_limit < self.__credit_used:
            raise ValueError(f'El límite de crédito no puede ser menor que la deuda actual '
                             f'({self.__credit_used:.2f})')
        self.__credit_limit = credit_limit

    def get_credit_used(self):
        return self.__credit_used
