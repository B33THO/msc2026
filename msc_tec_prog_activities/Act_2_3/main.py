from Act_2_3.menuBuilder import MenuBuilder
from Act_2_3.functions import AccountFunctions

funcs = AccountFunctions()

main_menu = [
    ('Crear cuenta', None),  # 1
    ('Imprimir cuentas', funcs.get_accounts),  # 2
    ('Realizar transacción', funcs.transaction),  # 3
    ('Buscar una cuenta', funcs.find_account),  # 4
    ('Eliminar cuenta', funcs.delete_account),  # 5
    ('Salir', MenuBuilder.exit)  # 6
]
create_menu = [
    ('Cuenta normal', funcs.create_account),
    ('Cuenta crédito', funcs.create_credit_account),
    ('Regresar', MenuBuilder.back)
]

menu = MenuBuilder(
    main_menu, 'Principal',
    (1, create_menu),
)

if __name__ == '__main__':
    try:
        menu.show()
    except (KeyboardInterrupt, EOFError):
        print('\nPrograma terminado')