from classes.employee import Employee


class FeeEmployee(Employee):
    # Sueldo por hora inicial fijo para todos los empleados de honorarios
    HOURLY_SALARY = 180.0
    NORMAL_HOURS = 40
    MAX_HOURS = 60
    EXTRA_HOUR_RATE = 0.002

    def __init__(self, nss: str, first_name: str, last_name: str, name: str, position: str, born_date: str,
                 hometown: str, hours: int):
        super().__init__(nss, first_name, last_name, name, position, born_date, hometown)
        self.__hours = hours
        self.__hourly_salary = FeeEmployee.HOURLY_SALARY

    def get_type(self) -> str:
        return 'Honorarios'

    def get_hours(self) -> int:
        return self.__hours

    def set_hours(self, hours: int):
        self.__hours = hours

    def get_hourly_salary(self) -> float:
        return self.__hourly_salary

    def set_hourly_salary(self, hourly_salary: float):
        self.__hourly_salary = hourly_salary

    def get_extra_hours(self) -> int:
        return max(0, self.__hours - FeeEmployee.NORMAL_HOURS)

    def get_subtotal(self) -> float:
        # Pago de todas las horas sin el bono por horas extra
        return self.__hours * self.__hourly_salary

    def get_extra_rate(self) -> float:
        # 0.2% por cada hora extra
        return FeeEmployee.EXTRA_HOUR_RATE * self.get_extra_hours()

    def get_salary(self) -> float:
        # horas * sueldo_hora, +0.2% por cada hora extra arriba de 40
        return self.get_subtotal() * (1 + self.get_extra_rate())

    def __str__(self):
        return super().__str__() + f' -- Salario: {self.get_salary():,.2f} -- Horas: {self.__hours} -- Sueldo hora: {self.__hourly_salary}'
