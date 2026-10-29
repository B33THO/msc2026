class Client:
    def __init__(self, id, paternal_surname, maternal_surname, name):
        self.__id = id
        self.__paternal_surname = paternal_surname
        self.__maternal_surname = maternal_surname
        self.__name = name

    def get_id(self):
        return self.__id

    def get_paternal_surname(self):
        return self.__paternal_surname

    def get_maternal_surname(self):
        return self.__maternal_surname

    def get_name(self):
        return self.__name

    def set_id(self, id):
        self.__id = id

    def set_paternal_surname(self, paternal_surname):
        self.__paternal_surname = paternal_surname

    def set_maternal_surname(self, maternal_surname):
        self.__maternal_surname = maternal_surname

    def set_name(self, name):
        self.__name = name

    def __str__(self):
        return f'{self.__paternal_surname} {self.__maternal_surname} {self.__name}'