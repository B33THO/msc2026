from Act_2_3.menuBuilder import MenuBuilder

main_menu = ['1. Crear cuenta']
sub_menu = ['1. Cuenta normal', '2. Cuenta a Crédito']

menu = MenuBuilder(main_menu, 'Principal',(1, sub_menu))
if __name__ == '__main__':
    menu.show()