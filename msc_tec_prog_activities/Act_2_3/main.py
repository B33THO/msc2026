from Act_2_3.menuBuilder import MenuBuilder
from Act_2_3.functions import AccountFunctions

funcs = AccountFunctions()

main_menu = [
    ('Crear Cuenta', None), # 1
    ('Ver Cuentas', funcs.get_accounts), #2
    ('Realizar Transacción', None ), #3
    ('Buscar cuenta', funcs.find_account), #4
    ('Eliminar cuenta', funcs.delete_account), #4
    ('Salir', MenuBuilder.exit)#6
]
create_menu = [
    ('Cuenta normal', funcs.create_account),
    ('Cuenta de crédito', funcs.create_credit_account),
    ('Regresar', MenuBuilder.back)
]

transc_menu = [
    ('Depositar', funcs.deposit),
    ('Retirar', funcs.withdraw),
    ('Modificar crédito', MenuBuilder.back),
    ('Regresar', MenuBuilder.back),
]

menu = MenuBuilder(
    main_menu, 'Principal',
    (1, create_menu),
    (3, transc_menu)
)

if __name__ == '__main__':
    menu.show()