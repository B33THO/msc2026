import datetime

from classes.employee import Employee


class BaseEmployee(Employee):

    HOURLY_SALARIES = {
        'Programador': 250.0,
        'Analista': 220.0,
        'Soporte Técnico': 150.0,
        'Administrador de BD': 270.0,
        'Líder de Proyecto': 320.0,
    }

    def __init__(self, nss: str, first_name: str, last_name: str, name: str, position: str, born_date: str,
                 hometown: str, hire_date: datetime.date):
        super().__init__(nss, first_name, last_name, name, position, born_date, hometown)
        self.__hire_date = hire_date
        self.__hourly_salary = BaseEmployee.HOURLY_SALARIES[position]

    def get_type(self) -> str:
        return 'Base'

    def get_hire_date(self) -> datetime.date:
        return self.__hire_date

    def get_hourly_salary(self) -> float:
        return self.__hourly_salary

    def set_hourly_salary(self, hourly_salary: float):
        self.__hourly_salary = hourly_salary

    def get_years_of_service(self) -> int:
        # Años completos desde la fecha de ingreso
        today = datetime.date.today()
        years = today.year - self.__hire_date.year
        if (today.month, today.day) < (self.__hire_date.month, self.__hire_date.day):
            years -= 1
        return max(0, years)

    def get_salary(self) -> float:
        # sueldo_hora * 40 * (1 + 1% por cada año de servicio)
        self.set_salary(self.__hourly_salary * 40 * (1 + 0.01 * self.get_years_of_service()))
        return super().get_salary()

    def __str__(self):
        return super().__str__() + f' -- Sueldo hora: {self.__hourly_salary} -- Años de servicio: {self.get_years_of_service()}'
