import datetime


class Employee:
    def __init__(self, nss: int, first_name: str, last_name:str, name:str, position: str, born_date: str, hometown:str):
        self.__nss = nss
        self.__first_name = first_name
        self.__last_name = last_name
        self.__name = name
        self.__position = position
        self.__born_date = born_date
        self.__hometown = hometown
        self.__salary = 1

    def get_salary(self) -> float:
        return self.__salary

    def get_nss(self) -> int:
        return self.__nss

    def get_first_name(self) -> str:
        return self.__first_name

    def get_last_name(self) -> str:
        return self.__last_name

    def get_name(self) -> str:
        return self.__name

    def get_position(self) -> str:
        return self.__position

    def get_born_date(self) -> str:
        return self.__born_date

    def get_hometown(self) -> str:
        return self.__hometown

    def set_salary(self, salary: float):
        self.__salary = salary

    def __str__(self):
        return f'NSS: {self.__nss} -- Nombre: {self.__name} -- Salario: {self.__salary:,.2f} -- Puesto: {self.__position}'