from Act_2_3.menuBuilder import MenuBuilder


def first_option():
    print('Ejecutando First option')


def sub_second_option():
    print('Ejecutando Sub Second option')


def sub_third_option():
    print('Ejecutando Sub Third option')


def sub_sub_x():
    print('Ejecutando Sub Sub X')


def sub_sub_y():
    print('Ejecutando Sub Sub Y')


def sub_a():
    print('Ejecutando Sub A')


def sub_b():
    print('Ejecutando Sub B')


# (texto, función). Las opciones que abren un submenú pueden llevar None
menuTest = [('First option', first_option), ('Second option', None), ('Third option', None)]
submenuTest = [('Sub First option', None), ('Sub Second option', sub_second_option),
               ('Sub Third option', sub_third_option)]
submenuTest2 = [('Sub A', sub_a), ('Sub B', sub_b)]
subSubmenuTest = [('Sub Sub X', sub_sub_x), ('Sub Sub Y', sub_sub_y)]

# (opción del padre, items del submenú, *submenús anidados)
menuBuilder = MenuBuilder(
    menuTest, 'Menú Principal',
    (2, submenuTest, (1, subSubmenuTest)),
    (3, submenuTest2))

if __name__ == '__main__':
    menuBuilder.show()
