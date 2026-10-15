from MSC26_2_4_GARCIA_ALBERTO.base_employee import BaseEmployee
from MSC26_2_4_GARCIA_ALBERTO.colors import Color
from MSC26_2_4_GARCIA_ALBERTO.fee_employee import FeeEmployee
from MSC26_2_4_GARCIA_ALBERTO.validators import Validator


class EmployeesActions:
    MAX_HOURS = 168  # horas que tiene una semana
    MAX_HIRING_TIME = 10_000

    def __init__(self):
        self.__employees = [
            BaseEmployee(12345, 'Alan Brito Delgado', 'Cajero', 150),
            FeeEmployee(23456, 'Esteban Quito Madera', 'Consultor', 'Temporal', 200, 45, 100),
            BaseEmployee(34567, 'Benito Camelo', 'Vendedor', 120),
            BaseEmployee(45678, 'Elba Lazo', 'Recepcionista', 110),
            FeeEmployee(56789, 'Aitor Tilla', 'Cocinero', 'Por proyecto', 160, 30, 90),
            FeeEmployee(67890, 'Susana Oria', 'Diseñadora', 'Temporal', 320, 50, 130),
        ]
        # Se calcula el salario para que __str__ no imprima el valor inicial de 1
        for employee in self.__employees:
            employee.get_salary()

    #-----------------------------------------------
    # Create section
    #-----------------------------------------------
    def create_fee_employee(self):
        data = self.__ask_employee_data()
        if data is None:
            return None
        nss, name, position = data

        hiring_type = self.__ask_name('Ingrese el tipo de contratación')
        if hiring_type is None:
            return None
        time = self.__ask_int('Ingrese el tiempo de contratación (horas)', self.MAX_HIRING_TIME)
        if time is None:
            return None
        hours = self.__ask_int('Ingrese las horas trabajadas', self.MAX_HOURS)
        if hours is None:
            return None
        hour_cost = self.__ask_amount('Ingrese el precio por hora')
        if hour_cost is None:
            return None

        employee = FeeEmployee(nss, name, position, hiring_type, time, hours, hour_cost)
        return self.__add(employee, 'Empleado por honorarios agregado correctamente')

    def create_base_employee(self):
        data = self.__ask_employee_data()
        if data is None:
            return None
        nss, name, position = data

        base_salary = self.__ask_amount('Ingrese el sueldo base (por hora)')
        if base_salary is None:
            return None

        employee = BaseEmployee(nss, name, position, base_salary)
        return self.__add(employee, 'Empleado base agregado correctamente')

    #-----------------------------------------------
    # Show section
    #-----------------------------------------------
    def show_fee_employees_info(self):
        fee_emps = [emp for emp in self.__employees if isinstance(emp, FeeEmployee)]
        if len(fee_emps) == 0:
            print(f'{Color.YELLOW}No hay empleados por honorarios.{Color.RESET}')
            return

        print(f'{Color.YELLOW}{"-" * 70}EMPLEADOS HONORARIOS{"-" * 70}')
        for employee in fee_emps:
                print(employee)
        print(f'{"-" * 150}{Color.RESET}')

    def show_base_employees_info(self):
        base_employees = [emp for emp in self.__employees if isinstance(emp, BaseEmployee)]
        if len(base_employees) == 0:
            print(f'{Color.YELLOW}No hay empleados base.{Color.RESET}')
            return

        print(f'{Color.YELLOW}{"-" * 70}EMPLEADOS BASE{"-" * 70}')
        for employee in base_employees:
                print(employee)
        print(f'{"-" * 150}{Color.RESET}')

    def show_all_employees_info(self):
        if len(self.__employees) == 0:
            print(f'{Color.YELLOW}No hay empleados.{Color.RESET}')
            return

        print(f'{Color.YELLOW}{"-"*70}EMPLEADOS{"-"*70}')
        for employee in self.__employees:
            print(employee)

        print(f'{"-"*150}{Color.RESET}')

    def show_salaries_info(self):
        pass

    def show_salary_info(self):
        pass

    def delete_employee(self):
        pass

    #-----------------------------------------------
    # Helpers
    #-----------------------------------------------
    def __add(self, employee, success_message):
        # Se calcula el salario antes de mostrarlo para que __str__ no imprima el valor inicial de 1
        employee.get_salary()
        self.__employees.append(employee)
        print(f'{Color.GREEN}{success_message}{Color.RESET}')
        print(f'{Color.YELLOW}{employee}{Color.RESET}')
        return employee

    def __ask_employee_data(self):
        """Pide NSS, nombre y puesto; devuelve la tupla o None si el usuario cancela."""
        nss = self.__ask_nss()
        while nss is not None and self.__find_by_nss(nss) is not None:
            print(f'{Color.RED}Ya existe un empleado con el NSS {nss}{Color.RESET}')
            nss = self.__ask_nss()
        if nss is None:
            return None

        name = self.__ask_name('Ingrese el nombre del empleado')
        if name is None:
            return None
        position = self.__ask_name('Ingrese el puesto')
        if position is None:
            return None
        return nss, name, position

    def __find_by_nss(self, nss):
        for employee in self.__employees:
            if employee.get_nss() == nss:
                return employee
        return None

    @staticmethod
    def __ask_nss():
        """Pide un NSS válido; devuelve None si el usuario deja la entrada vacía para cancelar."""
        while True:
            nss = input('Ingrese el NSS (Enter para cancelar): ').strip()
            if not nss:
                print(f'{Color.YELLOW}Operación cancelada{Color.RESET}')
                return None
            if Validator.is_nss_number(nss):
                return int(nss)

    @staticmethod
    def __ask_name(prompt):
        """Pide un texto válido (nombre, puesto, tipo de contratación); devuelve None si el usuario deja la entrada vacía para cancelar."""
        while True:
            name = input(f'{prompt} (Enter para cancelar): ').strip()
            if not name:
                print(f'{Color.YELLOW}Operación cancelada{Color.RESET}')
                return None
            if Validator.is_name(name):
                return name

    @staticmethod
    def __ask_int(prompt, max_value):
        """Pide un entero positivo; devuelve None si el usuario deja la entrada vacía para cancelar."""
        while True:
            number = input(f'{prompt} (Enter para cancelar): ').strip()
            if not number:
                print(f'{Color.YELLOW}Operación cancelada{Color.RESET}')
                return None
            if Validator.is_positive_int(number, max_value):
                return int(number)

    @staticmethod
    def __ask_amount(prompt):
        """Pide un monto válido; devuelve None si el usuario deja la entrada vacía para cancelar."""
        while True:
            amount = input(f'{prompt} (Enter para cancelar): ').strip()
            if not amount:
                print(f'{Color.YELLOW}Operación cancelada{Color.RESET}')
                return None
            if Validator.is_amount(amount):
                return float(amount)
