import re


class Validator:
    MAX_AMOUNT = 1_000_000_000
    MAX_NAME_LENGTH = 100

    __NSS_NUMBER_PATTERN = re.compile(r'[1-9][0-9]{4}')
    __AMOUNT_PATTERN = re.compile(r'[0-9]+(\.[0-9]{1,2})?')
    __INTEGER_PATTERN = re.compile(r'[0-9]+')
    __DATE_DDMMYY_PATTERN = re.compile(r'(\d{4}-\d{2}-\d{2})')

    @staticmethod
    def __error(message):
        return message

    @staticmethod
    def __preview(value):
        """Acorta el valor para que un texto muy largo no llene la consola en los mensajes de error."""
        text = str(value)
        return text if len(text) <= 20 else text[:20] + '...'

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
    def is_name(value):
        if not Validator.is_not_empty_string(value):
            return False
        value = value.strip()
        if len(value) > Validator.MAX_NAME_LENGTH:
            Validator.__error(f'El nombre no puede tener más de {Validator.MAX_NAME_LENGTH} caracteres.')
            return False
        if not value.isprintable():
            Validator.__error('El nombre contiene caracteres no válidos.')
            return False
        if not any(char.isalpha() for char in value):
            Validator.__error('El nombre debe contener al menos una letra.')
            return False
        return True

    @staticmethod
    def is_nss_number(value):
        if isinstance(value, str) and Validator.__NSS_NUMBER_PATTERN.fullmatch(value.strip()):
            return True
        Validator.__error(f"'{Validator.__preview(value)}' no es un NSS válido. "
                          f"Debe tener 5 dígitos y no empezar con 0, por ejemplo 12345")
        return False

    @staticmethod
    def is_amount(value):
        """Monto de dinero: positivo, con máximo 2 decimales y sin pasar de MAX_AMOUNT."""
        if not isinstance(value, str) or not Validator.__AMOUNT_PATTERN.fullmatch(value.strip()):
            Validator.__error(f"'{Validator.__preview(value)}' no es un monto válido. "
                              f"Use números con máximo 2 decimales, por ejemplo 150.50")
            return False
        amount = float(value)
        if amount <= 0:
            Validator.__error('El monto debe ser mayor que 0.')
            return False
        if amount > Validator.MAX_AMOUNT:
            Validator.__error(f'El monto no puede ser mayor que {Validator.MAX_AMOUNT:,.2f}.')
            return False
        return True

    @staticmethod
    def is_positive_int(value, max_value):
        """Número entero mayor que 0 y sin pasar de max_value (horas, tiempo de contratación)."""
        if not isinstance(value, str) or not Validator.__INTEGER_PATTERN.fullmatch(value.strip()):
            Validator.__error(f"'{Validator.__preview(value)}' no es un número entero válido. "
                              f"Use solo dígitos, por ejemplo 40")
            return False
        number = int(value)
        if number <= 0:
            Validator.__error('El número debe ser mayor que 0.')
            return False
        if number > max_value:
            Validator.__error(f'El número no puede ser mayor que {max_value:,}.')
            return False
        return True

