from Act_3_1.MSC26_3_1_GARCIA_ALBERTO.classes.employee import Employee


class EmployeeActions:
    def create_employee(self, nss, first_name: str, last_name: str, name: str, position:str, born_date: str, hometown: str):
        new_employee = Employee(
            nss,
            first_name,
            last_name,
            name,
            position,
            born_date,
            hometown
        )