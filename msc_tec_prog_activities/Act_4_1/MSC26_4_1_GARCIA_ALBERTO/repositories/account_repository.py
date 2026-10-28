from db.Connection import Connection


class AccountRepository:
    def __init__(self, connection = None):
        self.__connection = connection or Connection()

    def create(self, account):
        sql = """
            INSERT INTO account (account_number, idClient, balance, created_at, updated_at)
        """

        with self.__connection.cursor() as cur:
            cur.execute(sql, (
                account.getNumberAccount(),
                account.getIdClient(),
            ))
        account.setNumberAccount(cur.lastrowid)
        return account

    def create_credit_account(self, credit_account):
        sql = """
            INSERT INTO credit_account (account_number, idClient, balance, created_at, updated_at)
        """