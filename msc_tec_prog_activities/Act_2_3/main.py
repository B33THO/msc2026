from Act_2_3.menuBuilder import MenuBuilder
from Act_2_3.functions import AccountFunctions

funcs = AccountFunctions()

main_menu = [
    ('Crear Cuenta', None),
    ('Ver Cuentas', funcs.get_accounts),
    ('Salir', MenuBuilder.exit)
]
sub_menu = [
    ('Cuenta normal', funcs.create_account),
    ('Cuenta de crédito', funcs.create_credit_account),
    ('Regresar', MenuBuilder.back)
]

menu = MenuBuilder(main_menu, 'Principal',(1, sub_menu))
if __name__ == '__main__':
    menu.show()