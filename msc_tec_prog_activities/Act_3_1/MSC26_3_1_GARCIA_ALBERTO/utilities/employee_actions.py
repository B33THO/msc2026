from classes.employee import Employee
from utilities.validators import Validator


class EmployeeActions:

    @staticmethod
    def create_employee(nss: str, first_name: str, last_name: str, name: str, position:str, born_date: str, hometown: str):
        if not Validator.is_nss_number(nss):
            return 'Invalid Nss Number'

        if not Validator.is_name(name):
            return 'Invalid Name'

        return Employee(
            nss,
            first_name,
            last_name,
            name,
            position,
            born_date,
            hometown
        )
