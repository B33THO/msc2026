from Act_3_1.MSC26_3_1_GARCIA_ALBERTO.classes.employee import Employee
from Act_3_1.MSC26_3_1_GARCIA_ALBERTO.utilities.validators import Validator


class EmployeeActions:

    @staticmethod
    def create_employee(self, nss: int, first_name: str, last_name: str, name: str, position:str, born_date: str, hometown: str):
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
