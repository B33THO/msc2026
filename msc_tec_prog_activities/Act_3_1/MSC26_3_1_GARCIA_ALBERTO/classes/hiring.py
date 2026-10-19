#Contratacion
class Hiring:
    def __init__(self, hiring_type: str, time: int):
        self.__hiring_type = hiring_type
        self.__time = time #tiempo de contratación (horas)

    def __str__(self):
        return f'Tipo: {self.__hiring_type}, Tiempo: {self.__time}'