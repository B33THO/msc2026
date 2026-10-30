from db.connection import Connection
from domain.account import Account
from domain.client import Client
from domain.credit_account import CreditAccount
from repositories.client_repository import ClientRepository


class AccountRepository:
    def __init__(self, connection = None):
        self.__connection = connection or Connection()

    #Los métodos _to_* convierten una fila (diccionario) en el objeto del dominio
    @staticmethod
    def _to_account(row):
        return Account(
            row['account_number'],
            row['id_client'],
            row['balance'],
            row['created_at']
        )

    @staticmethod
    def _to_credit_account(row):
        return CreditAccount(
            row['account_number'],
            row['id_client'],
            row['balance'],
            row['created_at'],
            row['credit_limit'],
            row['debt']
        )

    @staticmethod
    def _to_client(row):
        return Client(
            row['id_client'],
            row['paternal_surname'],
            row['maternal_surname'],
            row['name']
        )

    @classmethod
    def _to_client_account(cls, row):
        #Por el LEFT JOIN, las cuentas de ahorro traen credit_limit en None
        if row['credit_limit'] is not None:
            account = cls._to_credit_account(row)
        else:
            account = cls._to_account(row)

        #Regresa el par (Client, Account/CreditAccount)
        return cls._to_client(row), account

    def _fetch_all(self, where = "", params = ()):
        #Arma la consulta base con el filtro recibido y convierte cada fila
        sql = self.SQL_SELECT_ACCOUNTS.format(where = where)
        with self.__connection.cursor(dictionary=True) as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()

        return [self._to_client_account(row) for row in rows]

    # ---------------------------------------------------------------------------------
    # CREAR CUENTA NORMAL
    # ---------------------------------------------------------------------------------
    def create(self, account):

        with self.__connection.cursor() as cur:
            self._insert(cur, account)

        return account

    # ---------------------------------------------------------------------------------
    # CREAR CUENTA CRÉDITO
    # ---------------------------------------------------------------------------------
    def create_credit_account(self, credit_account: CreditAccount):

        #Ambos INSERT usan el mismo cursor, si falla uno se hace rollback de los dos
        with self.__connection.cursor() as cur:
            self._insert(cur, credit_account)

        return credit_account

    # ---------------------------------------------------------------------------------
    # CREAR CLIENTE Y SU CUENTA (ahorro o crédito)
    # ---------------------------------------------------------------------------------
    def create_with_client(self, client, account):

        #Todos los INSERT van en la misma transacción: si falla la cuenta también se
        #deshace el cliente, así nunca queda un cliente sin cuenta
        with self.__connection.cursor() as cur:
            ClientRepository.insert(cur, client)
            account.set_id_client(client.get_id())
            self._insert(cur, account)

        return client, account

    def _insert(self, cur, account):
        #INSERT en account y, si es de crédito, también en credit_account.
        #Si la cuenta no trae número se envía NULL y MySQL genera uno con el AUTO_INCREMENT;
        #si trae uno (cuenta importada) se guarda con ese mismo número
        cur.execute(self.SQL_CREATE_ACCOUNT, (
            account.get_account_number(),
            account.get_id_client(),
            account.get_balance(),
            account.get_created_at()
        ))
        if account.get_account_number() is None:
            account.set_account_number(cur.lastrowid) #Número de cuenta generado por el AUTO_INCREMENT

        if isinstance(account, CreditAccount):
            #credit_account usa el mismo número de cuenta como llave primaria y foránea
            cur.execute(self.SQL_CREATE_CREDIT_ACCOUNT, (
                account.get_account_number(),
                account.get_credit_limit(),
                account.get_debt()
            ))

    # ---------------------------------------------------------------------------------
    # CONSULTAR TODAS LAS CUENTAS
    # ---------------------------------------------------------------------------------
    def get_all(self):
        return self._fetch_all()

    # ---------------------------------------------------------------------------------
    # CONSULTA POR NÚMERO DE CUENTA
    # ---------------------------------------------------------------------------------
    def get_by_account_number(self, account_number):
        results = self._fetch_all("WHERE a.account_number = %s", (account_number,))

        #Si hubo resultado regresa el par (Client, cuenta), si no, regresa None
        return results[0] if results else None

    # ---------------------------------------------------------------------------------
    # CONSULTAR SOLO CUENTAS DE AHORRO
    # ---------------------------------------------------------------------------------
    def get_savings_accounts(self):
        return self._fetch_all("WHERE ca.account_number IS NULL")

    # ---------------------------------------------------------------------------------
    # CONSULTAR SOLO CUENTAS DE CRÉDITO
    # ---------------------------------------------------------------------------------
    def get_credit_accounts(self):
        return self._fetch_all("WHERE ca.account_number IS NOT NULL")

    # ---------------------------------------------------------------------------------
    # CONSULTAR CUENTAS CON SALDO MENOR O IGUAL A UNA CANTIDAD
    # ---------------------------------------------------------------------------------
    def get_by_max_balance(self, amount):
        return self._fetch_all("WHERE a.balance <= %s", (amount,))

    # ---------------------------------------------------------------------------------
    # ACTUALIZAR CUENTA (saldo, y límite/adeudo si es de crédito)
    # ---------------------------------------------------------------------------------
    def update(self, account):

        with self.__connection.cursor() as cur:
            updated = self._update(cur, account)

        return updated

    # ---------------------------------------------------------------------------------
    # ACTUALIZAR CLIENTE Y SU CUENTA
    # ---------------------------------------------------------------------------------
    def update_with_client(self, client, account):

        #Los UPDATE de cliente y cuenta van en la misma transacción
        with self.__connection.cursor() as cur:
            client_updated = ClientRepository.update_row(cur, client)
            account_updated = self._update(cur, account)

        return client_updated or account_updated

    def _update(self, cur, account):
        cur.execute(self.SQL_UPDATE_ACCOUNT, (
            account.get_balance(),
            account.get_account_number()
        ))
        updated = cur.rowcount > 0

        #Las de crédito también actualizan su tabla; ambos UPDATE van en la misma transacción
        if isinstance(account, CreditAccount):
            cur.execute(self.SQL_UPDATE_CREDIT_ACCOUNT, (
                account.get_credit_limit(),
                account.get_debt(),
                account.get_account_number()
            ))
            updated = updated or cur.rowcount > 0

        #True si cambió alguna de las dos tablas
        return updated

    # ---------------------------------------------------------------------------------
    # ELIMINAR CUENTA
    # ---------------------------------------------------------------------------------
    def delete(self, account_number):

        #Por el ON DELETE CASCADE también se borra su registro en credit_account
        with self.__connection.cursor() as cur:
            cur.execute(self.SQL_DELETE_ACCOUNT, (account_number,))
            deleted = cur.rowcount > 0

        return deleted


    # ---------------------------------------------------------------------------------
    # CONSULTAS SQL
    # ---------------------------------------------------------------------------------
    SQL_CREATE_ACCOUNT = """
            INSERT INTO account (account_number, id_client, balance, created_at)
            VALUES (%s, %s, %s, %s)
        """

    SQL_CREATE_CREDIT_ACCOUNT = """
            INSERT INTO credit_account (account_number, credit_limit, debt)
            VALUES (%s, %s, %s)
        """

    #{where} se reemplaza por el filtro de cada consulta; los valores van como %s
    SQL_SELECT_ACCOUNTS = """
            SELECT c.paternal_surname, c.maternal_surname, c.name,
                   a.account_number, a.id_client, a.balance, a.created_at,
                   ca.credit_limit, ca.debt
            FROM account a
            INNER JOIN client c ON c.id = a.id_client
            LEFT JOIN credit_account ca ON ca.account_number = a.account_number
            {where}
            ORDER BY a.account_number
        """

    SQL_UPDATE_ACCOUNT = """
            UPDATE account
            SET balance = %s
            WHERE account_number = %s
        """

    SQL_UPDATE_CREDIT_ACCOUNT = """
            UPDATE credit_account
            SET credit_limit = %s, debt = %s
            WHERE account_number = %s
        """

    SQL_DELETE_ACCOUNT = "DELETE FROM account WHERE account_number = %s"
