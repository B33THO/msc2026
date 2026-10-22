import re


class Validator:
    MAX_AMOUNT = 5_000
    MAX_NAME_LENGTH = 100

    __NSS_NUMBER_PATTERN = re.compile(r'[1-9][0-9]{4}')
    __AMOUNT_PATTERN = re.compile(r'[0-9]+(\.[0-9]{1,2})?')
    __INTEGER_PATTERN = re.compile(r'[0-9]+')

    @staticmethod
    def is_not_empty_string(value):
        return isinstance(value, str) and len(value.strip()) > 0

    @staticmethod
    def is_name(value):
        if not Validator.is_not_empty_string(value):
            return False
        value = value.strip()
        if len(value) > Validator.MAX_NAME_LENGTH:
            return False
        if not value.isprintable():
            return False
        # Debe contener al menos una letra
        return any(char.isalpha() for char in value)

    @staticmethod
    def is_nss_number(value):
        """NSS de 5 dígitos que no empieza con 0, por ejemplo 12345."""
        return isinstance(value, str) and Validator.__NSS_NUMBER_PATTERN.fullmatch(value.strip()) is not None

    @staticmethod
    def is_amount(value):
        """Monto de dinero: positivo, con máximo 2 decimales y sin pasar de MAX_AMOUNT."""
        if not isinstance(value, str) or not Validator.__AMOUNT_PATTERN.fullmatch(value.strip()):
            return False
        amount = float(value)
        return 0 < amount <= Validator.MAX_AMOUNT

    @staticmethod
    def is_positive_int(value, max_value):
        """Número entero mayor que 0 y sin pasar de max_value (horas trabajadas)."""
        if not isinstance(value, str) or not Validator.__INTEGER_PATTERN.fullmatch(value.strip()):
            return False
        number = int(value)
        return 0 < number <= max_value
