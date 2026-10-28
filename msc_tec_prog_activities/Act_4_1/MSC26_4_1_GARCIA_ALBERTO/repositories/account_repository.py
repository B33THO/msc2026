from db.connection import Connection
from domain.account import Account
from domain.credit_account import CreditAccount


class AccountRepository:
    def __init__(self, connection = None):
        self.__connection = connection or Connection()

    @staticmethod
    def _to_account(row):
        return Account(
            row['id_client'],
            row['account_number'],
            row['balance'],
            row['created_at']
        )

    # ---------------------------------------------------------------------------------
    # CREAR CUENTA NORMAL
    # ---------------------------------------------------------------------------------
    def create(self, account):

        with self.__connection.cursor() as cur:
            cur.execute(self.SQL_CREATE_ACCOUNT, (
                account.get_id_client(),
                account.get_balance(),
                account.get_created_at()
            ))
            account.set_account_number(cur.lastrowid)

        return account

    # ---------------------------------------------------------------------------------
    # CREAR CUENTA CRÉDITO
    # ---------------------------------------------------------------------------------
    def create_credit_account(self, credit_account: CreditAccount):

        with self.__connection.cursor() as cur:
            cur.execute(self.SQL_CREATE_ACCOUNT, (
                credit_account.get_id_client(),
                credit_account.get_balance(),
                credit_account.get_created_at()
            ))
            credit_account.set_account_number(cur.lastrowid)

            cur.execute(self.SQL_CREATE_CREDIT_ACCOUNT, (
                credit_account.get_account_number(),
                credit_account.get_credit_limit(),
                credit_account.get_debt()
            ))

        return credit_account


    # ---------------------------------------------------------------------------------
    # CONSULTAS SQL
    # ---------------------------------------------------------------------------------
    SQL_CREATE_ACCOUNT = """
            INSERT INTO account (id_client, balance, created_at)
            VALUES (%s, %s, %s)
        """

    SQL_CREATE_CREDIT_ACCOUNT = """
            INSERT INTO credit_account (account_number, credit_limit, debt)
            VALUES (%s, %s, %s)
        """