import math


class Validator:
    @staticmethod
    def is_int(value):
        try:
            int(value)
            return True
        except Exception as e:
            print(e)
            return False

    @staticmethod
    def is_float(value):
        try:
            return math.isfinite(float(value))
        except Exception as e:
            print(e)
            return False

    @staticmethod
    def is_not_empty_string(value):
        try:
            value = value.strip()
            if len(value) > 0:
                return True
            else:
                return False
        except Exception as e:
            print(e)
            return False

    @staticmethod
    def is_positive_integer(value):
        try:
            if Validator.is_int(value) and int(value) > 0:
                return True
            else:
                return False
        except Exception as e:
            print(e)
            return False

    @staticmethod
    def is_positive_float(value):
        try:
            if Validator.is_float(value) and float(value) > 0:
                return True
            else:
                return False
        except Exception as e:
            print(e)
            return False