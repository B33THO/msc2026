from MSC26_2_4_GARCIA_ALBERTO.employee import Employee
from MSC26_2_4_GARCIA_ALBERTO.hiring import Hiring


class FeeEmployee(Employee, Hiring):
    def __init__(self, nss: int, name:str, position:str, hiring_type: str, time: int,  hours: int, hour_cost: float):
        super().__init__(nss, name, position)
        Hiring.__init__(self, hiring_type, time)
        self.__hours = hours
        self.__hour_cost = hour_cost

    def get_salary(self) -> float:
        # Las primeras 40 horas se pagan normal; las extra con el precio por hora +2%
        if self.__hours <= 40:
            salary = self.__hours * self.__hour_cost
        else:
            extra_hours = self.__hours - 40
            salary = 40 * self.__hour_cost + extra_hours * self.__hour_cost * 1.02
        self.set_salary(salary)
        return super().get_salary()

    def __str__(self):
        return super().__str__() + ' -- ' + Hiring.__str__(self) + f' -- Horas: {self.__hours} -- Costo hora: {self.__hour_cost}'