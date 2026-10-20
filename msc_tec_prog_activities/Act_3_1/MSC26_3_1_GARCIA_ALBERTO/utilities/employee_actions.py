from Act_3_1.MSC26_3_1_GARCIA_ALBERTO.classes.employee import Employee
from Act_3_1.MSC26_3_1_GARCIA_ALBERTO.utilities.validators import Validator


class EmployeeActions:
    def create_employee(self, nss: int, first_name: str, last_name: str, name: str, position:str, born_date: str, hometown: str):

        new_employee = Employee(
            nss,
            first_name,
            last_name,
            name,
            position,
            born_date,
            hometown
        )

    @staticmethod
    def __ask_nss():
        """Pide un NSS válido; devuelve None si el usuario deja la entrada vacía para cancelar."""
        while True:
            nss = input('Ingrese el NSS de 5 dígitos (Enter para cancelar): ').strip()
            if not nss:
                return 'Error'
                return None
            if Validator.is_nss_number(nss):
                return int(nss)