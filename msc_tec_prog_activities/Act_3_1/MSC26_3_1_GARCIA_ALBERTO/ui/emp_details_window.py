import datetime
import os

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QLabel
from PyQt6.uic import loadUi

from classes.base_employee import BaseEmployee
from classes.fee_employee import FeeEmployee
from utilities.dates import Dates
from utilities.formatters import Formatter


class EmpDetailsWindow(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        path = os.path.join(os.path.dirname(__file__), "emp_details_window.ui")
        loadUi(path, self)
        self.events()

    #-----------------------------------------------------------------------------------------------------------------
    # EVENTS
    #-----------------------------------------------------------------------------------------------------------------
    def events(self):
        self.btn_close.clicked.connect(self.close)
    #-----------------------------------------------------------------------------------------------------------------

    def show_employee(self, employee):
        self.lbl_emp_fullname.setText(
            f'{employee.get_name()} {employee.get_first_name()} {employee.get_last_name()}')
        self.lbl_emp_subtitle.setText(f'Empleado {employee.get_type().lower()} · {employee.get_position()}')
        self.fill_employee_data(employee)

        # Las filas del salario cambian según el tipo, por eso se arman cada vez
        while self.fl_salary.rowCount() > 0:
            self.fl_salary.removeRow(0)
        if isinstance(employee, BaseEmployee):
            self.fill_base_salary(employee)
        else:
            self.fill_fee_salary(employee)

        self.lb_total.setText(Formatter.money(employee.get_salary()))
        self.show()

    def fill_employee_data(self, employee):
        born_date = datetime.date.fromisoformat(employee.get_born_date())
        age = Dates.full_years(born_date, datetime.date.today())
        self.lb_nss.setText(employee.get_nss())
        self.lb_type.setText(employee.get_type())
        self.lb_position.setText(employee.get_position())
        self.lb_born_date.setText(f'{born_date:%d/%m/%Y}  ({age} años)')
        self.lb_hometown.setText(employee.get_hometown())

        # Fecha de ingreso y antigüedad solo aplican a empleados base
        is_base = isinstance(employee, BaseEmployee)
        for widget in (self.lbl_hire_date_title, self.lb_hire_date, self.lbl_seniority_title, self.lb_seniority):
            widget.setVisible(is_base)
        if is_base:
            years = employee.get_years_of_service()
            self.lb_hire_date.setText(f'{employee.get_hire_date():%d/%m/%Y}')
            self.lb_seniority.setText(f'{years} año' if years == 1 else f'{years} años')

    def fill_base_salary(self, employee: BaseEmployee):
        hourly_salary = employee.get_hourly_salary()
        weekly_base = employee.get_weekly_base()
        rate = employee.get_seniority_rate()
        # La antigüedad depende de la fecha de hoy, se calcula una vez para todo el desglose
        years = employee.get_years_of_service()

        self.add_salary_row('Sueldo por hora', Formatter.money(hourly_salary))
        self.add_salary_row('Horas semanales', str(BaseEmployee.WEEKLY_HOURS))
        self.add_salary_row(f'Sueldo base ({Formatter.money(hourly_salary)} × {BaseEmployee.WEEKLY_HOURS})',
                            Formatter.money(weekly_base))
        self.add_salary_row('Años de servicio', str(years))
        self.add_salary_row(f'Bono por antigüedad ({Formatter.percent(rate)})', '+ ' + Formatter.money(weekly_base * rate))
        self.lb_formula.setText(f'Sueldo por hora × {BaseEmployee.WEEKLY_HOURS} horas × '
                                f'(1 + {Formatter.percent(BaseEmployee.SENIORITY_RATE)} por cada año de servicio)')

    def fill_fee_salary(self, employee: FeeEmployee):
        hourly_salary = employee.get_hourly_salary()
        subtotal = employee.get_subtotal()
        rate = employee.get_extra_rate()

        self.add_salary_row('Sueldo por hora', Formatter.money(hourly_salary))
        self.add_salary_row('Horas trabajadas', str(employee.get_hours()))
        self.add_salary_row('Horas normales', str(min(employee.get_hours(), FeeEmployee.NORMAL_HOURS)))
        self.add_salary_row('Horas extra', str(employee.get_extra_hours()))
        self.add_salary_row(f'Subtotal ({employee.get_hours()} × {Formatter.money(hourly_salary)})', Formatter.money(subtotal))
        self.add_salary_row(f'Bono por horas extra ({Formatter.percent(rate)})', '+ ' + Formatter.money(subtotal * rate))
        self.lb_formula.setText(f'Horas trabajadas × sueldo por hora × (1 + {Formatter.percent(FeeEmployee.EXTRA_HOUR_RATE)} '
                                f'por cada hora extra arriba de {FeeEmployee.NORMAL_HOURS})')

    def add_salary_row(self, title: str, value: str):
        lb_value = QLabel(value)
        # Misma propiedad que los valores del .ui para que tomen el estilo de styles.qss
        lb_value.setProperty('value', True)
        lb_value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.fl_salary.addRow(QLabel(title), lb_value)
