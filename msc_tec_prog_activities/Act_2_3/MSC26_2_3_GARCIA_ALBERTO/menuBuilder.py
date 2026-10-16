from MSC26_2_3_GARCIA_ALBERTO.colors import Color

class MenuBuilder:

    BACK = 'back'
    EXIT = 'exit'

    def __init__(self, items, label, *submenus):
        self.__label = label
        self.__items = list(items)
        self.__submenus = {}

        for sub in submenus:
            option, sub_items, *nested = sub

            # Validate that option is in range
            if not 1 <= option <= len(self.__items):
                raise ValueError(f'La opción {option} no existe en "{label}"')

            sub_label = self.__items[option - 1][0]
            self.__submenus[option] = MenuBuilder(sub_items, sub_label, *nested)

        for i, (text, func) in enumerate(self.__items, start=1):
            if i not in self.__submenus and not callable(func):
                raise ValueError(f'La opción "{text}" no tiene una función asignada')

    @staticmethod
    def back():
        """Función lista para usar en una opción: regresa al menú anterior."""
        return MenuBuilder.BACK

    @staticmethod
    def exit():
        """Función lista para usar en una opción: termina el menú completo."""
        return MenuBuilder.EXIT

    def show(self):
        """Muestra el menú de forma interactiva hasta que una opción devuelve BACK o EXIT.

        Devuelve EXIT si hay que cerrar todos los menús, None si solo se regresó.
        """
        while True:
            print(f'{Color.CYAN}{self.__label}{Color.RESET}')
            for i, (text, _) in enumerate(self.__items, start=1):
                arrow = f' {Color.YELLOW}>{Color.RESET}' if i in self.__submenus else ''
                print(f'  {i}. {text}{arrow}')

            choice = input('Selecciona una opción: ').strip()
            # isascii() evita que int() falle con dígitos como '²', que isdigit() acepta
            if not (choice.isascii() and choice.isdigit()) or not 1 <= int(choice) <= len(self.__items):
                print(f'{Color.RED}Opción inválida{Color.RESET}')
                continue

            option = int(choice)
            if option in self.__submenus:
                result = self.__submenus[option].show()
            else:
                result = self.__items[option - 1][1]()

            if result == MenuBuilder.EXIT:
                return MenuBuilder.EXIT
            if result == MenuBuilder.BACK:
                return None
