from MSC26_2_4_GARCIA_ALBERTO.employees_actions import EmployeesActions
from MSC26_2_4_GARCIA_ALBERTO.menuBuilder import MenuBuilder

employee_actions = EmployeesActions()

options = [
    ('Agregar Empleado', None),
    ('Ver Info de empleados', None),
    ('Ver Salarios', None),
    ('Eliminar empleado', employee_actions.delete_employee),
    ('Salir', MenuBuilder.exit)
]

add_options = [
    ('Empleado Base', employee_actions.create_base_employee),
    ('Empleado Honorarios', employee_actions.create_fee_employee),
    ('Regresar', MenuBuilder.back),
]

show_employee_options = [
    ('Ver Empleados Base', employee_actions.show_base_employees_info),
    ('Ver Empleados por honorario', employee_actions.show_fee_employees_info),
    ('Ver todos los empleados', employee_actions.show_all_employees_info),
    ('Regresar', MenuBuilder.back),
]

show_salary_options = [
    ('Ver uno', employee_actions.show_salary_info),
    ('Ver todos', employee_actions.show_salaries_info),
    ('Regresar', MenuBuilder.back),
]

actions = MenuBuilder(
    options, 'Acciones',
    (1, add_options),
    (2, show_employee_options),
    (3, show_salary_options),
)

if __name__ == '__main__':

    actions.show()