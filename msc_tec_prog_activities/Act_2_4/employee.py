class Employee:
    def __init__(self, nss: int, name: str, position: str):
        self.__nss = nss
        self.__name = name
        self.__position = position
        self.__salary = 1

    def get_salary(self) -> float:
        return self.__salary

    def __str__(self):
        return f'NSS: {self.__nss} -- Nombre: {self.__name} -- Salario: {self.__salary} -- Puesto: {self.__position}'