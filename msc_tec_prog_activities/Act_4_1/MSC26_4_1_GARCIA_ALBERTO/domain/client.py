class Client:
    def __init__(self, id, paternalSurname, maternalSurname, name):
        self.__id = id
        self.__paternalSurname = paternalSurname
        self.__maternalSurname = maternalSurname
        self.__name = name

    def getId(self):
        return self.__id

    def getPaternalSurname(self):
        return self.__paternalSurname

    def getMaternalSurname(self):
        return self.__maternalSurname

    def getName(self):
        return self.__name

    def setId(self, id):
        self.__id = id

    def setPaternalSurname(self, paternalSurname):
        self.__paternalSurname = paternalSurname

    def setMaternalSurname(self, maternalSurname):
        self.__maternalSurname = maternalSurname

    def setName(self, name):
        self.__name = name