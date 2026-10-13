from Act_2_3.colors import Color


class MenuBuilder:

    def __init__(self, items, label, *submenus):
        self.__label = label
        self.__items = list(items)
        self.__submenus = {} #
        for sub in submenus:
            option, sub_items, *nested = sub
            if not 1 <= option <= len(self.__items):
                raise ValueError(f'La opción {option} no existe en "{label}"')
            sub_label = self.__items[option - 1][0]
            self.__submenus[option] = MenuBuilder(sub_items, sub_label, *nested)

        for i, (text, func) in enumerate(self.__items, start=1):
            if i not in self.__submenus and not callable(func):
                raise ValueError(f'La opción "{text}" no tiene una función asignada')

    def show(self, is_root=True):
        """Muestra el menú de forma interactiva hasta que el usuario sale o regresa."""
        while True:
            print(f'{Color.CYAN}{self.__label}{Color.RESET}')
            for i, (text, _) in enumerate(self.__items, start=1):
                arrow = f' {Color.YELLOW}>{Color.RESET}' if i in self.__submenus else ''
                print(f'  {i}. {text}{arrow}')
            print(f'  0. {"Salir" if is_root else "Regresar"}')

            choice = input('Selecciona una opción: ').strip()
            if not choice.isdigit() or int(choice) > len(self.__items):
                print(f'{Color.RED}Opción inválida{Color.RESET}')
                continue

            option = int(choice)
            if option == 0:
                return
            if option in self.__submenus:
                self.__submenus[option].show(is_root=False)
            else:
                self.__items[option - 1][1]()
