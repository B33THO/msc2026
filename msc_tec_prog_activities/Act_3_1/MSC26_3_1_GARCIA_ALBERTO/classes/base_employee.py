from MSC26_2_4_GARCIA_ALBERTO.employee import Employee


class BaseEmployee(Employee):
    def __init__(self, nss: int, name: str, position: str, base_salary: float):
        super().__init__(nss, name, position)
        self.__base_salary = base_salary

    def get_salary(self) -> float:
        self.set_salary(self.__base_salary * 40)
        return super().get_salary()

    def __str__(self):
        return super().__str__() + f' -- Sueldo base: {self.__base_salary}'
