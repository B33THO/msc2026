import math

from Act_2_3.colors import Color


class Validator:
    @staticmethod
    def __error(message):
        print(f'{Color.RED}{message}{Color.RESET}')

    @staticmethod
    def is_int(value):
        try:
            int(value)
            return True
        except (ValueError, TypeError):
            Validator.__error(f"'{value}' no es un número entero válido.")
            return False

    @staticmethod
    def is_float(value):
        try:
            if math.isfinite(float(value)):
                return True
            Validator.__error(f"'{value}' no es un número finito.")
            return False
        except (ValueError, TypeError):
            Validator.__error(f"'{value}' no es un número decimal válido.")
            return False

    @staticmethod
    def is_not_empty_string(value):
        if not isinstance(value, str):
            Validator.__error('El valor debe ser un texto.')
            return False
        if len(value.strip()) > 0:
            return True
        Validator.__error('El valor no puede estar vacío.')
        return False

    @staticmethod
    def is_positive_integer(value):
        if not Validator.is_int(value):
            return False
        if int(value) > 0:
            return True
        Validator.__error(f"'{value}' debe ser un número entero mayor que 0.")
        return False

    @staticmethod
    def is_positive_float(value):
        if not Validator.is_float(value):
            return False
        if float(value) > 0:
            return True
        Validator.__error(f"'{value}' debe ser un número mayor que 0.")
        return False
