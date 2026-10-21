import datetime
import os

from PyQt6.QtCore import pyqtSignal, Qt, QDate
from PyQt6.QtWidgets import QWidget, QMessageBox
from PyQt6.uic import loadUi

from classes.base_employee import BaseEmployee
from classes.employee import Employee
from classes.fee_employee import FeeEmployee
from utilities.employee_actions import EmployeeActions
from utilities.validators import Validator


class CreateEmployeeDialog(QWidget):
    MIN_AGE = 18

    employee_created = pyqtSignal(Employee)
    def __init__(self, employees):
        super().__init__()
        self.setWindowTitle("Crear Empleado")
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        path = os.path.join(os.path.dirname(__file__), "create_employee_dialog.ui")
        loadUi(path, self)
        self.load_positions()
        self.configure_dates()
        self.events()
        self.emp_actions = EmployeeActions()
        self.__employees = employees
        self.rb_base_employee.setChecked(True)

    #-----------------------------------------------------------------------------------------------------------------
    # EVENTS
    #-----------------------------------------------------------------------------------------------------------------
    def events(self):
        self.btn_save_employee.clicked.connect(self.save_employee)
        self.btn_clear.clicked.connect(self.clear_fields)
        self.btn_cancel.clicked.connect(self.close)
        self.rb_base_employee.toggled.connect(self.show_panel)
        self.rb_fee_employee.toggled.connect(self.show_panel)
        self.cb_positions.currentTextChanged.connect(self.update_initial_salary)


    def save_employee(self):
        try:
            #------------------------------------NSS-----------------------------------------------------------------
            in_nss = self.le_nss.text().strip()
            if not Validator.is_nss_number(in_nss):
                QMessageBox.critical(self, 'NSS inválido', 'El NSS debe tener 5 dígitos y no empezar con 0')
                return

            for em in self.__employees:
                if em.get_nss() == in_nss:
                    QMessageBox.warning(self, 'NSS duplicado', 'Ya existe un empleado con ese NSS')
                    return

            in_first_name = self.le_first_name.text().strip()
            if not Validator.is_name(in_first_name):
                QMessageBox.critical(self,'Error', 'Ingrese un apellido paterno válido')
                return

            in_last_name = self.le_last_name.text().strip()
            if not Validator.is_name(in_last_name):
                QMessageBox.critical(self,'Error', 'Ingrese un apellido materno válido')
                return

            in_name = self.le_name.text().strip()
            if not Validator.is_name(in_name):
                QMessageBox.critical(self,'Error', 'Ingrese un nombre válido')
                return

            #------------------------------------Fecha de nacimiento-------------------------------------------------
            born_date = self.de_born_date.date().toPyDate()
            if self.__full_years(born_date, datetime.date.today()) < CreateEmployeeDialog.MIN_AGE:
                QMessageBox.critical(self, 'Error', f'El empleado debe tener al menos {CreateEmployeeDialog.MIN_AGE} años')
                return

            position = self.cb_positions.currentText()

            hometown = self.le_hometown.text().strip()
            if not Validator.is_name(hometown):
                QMessageBox.critical(self,'Error', 'Ingrese un lugar de procedencia válido')
                return

            #------------------------------------Datos según el tipo de empleado-------------------------------------
            # Se guarda la fecha como texto ISO (aaaa-mm-dd) para no depender del formato regional
            born_date_text = born_date.isoformat()
            if self.rb_base_employee.isChecked():
                hire_date = self.de_hire_date.date().toPyDate()
                if hire_date > datetime.date.today():
                    QMessageBox.critical(self, 'Error', 'La fecha de ingreso no puede ser futura')
                    return
                if self.__full_years(born_date, hire_date) < CreateEmployeeDialog.MIN_AGE:
                    QMessageBox.critical(self, 'Error', f'A la fecha de ingreso el empleado debía tener al menos '
                                                        f'{CreateEmployeeDialog.MIN_AGE} años')
                    return

                new_employee = BaseEmployee(in_nss, in_first_name, in_last_name, in_name, position, born_date_text,
                                            hometown, hire_date)
            else:
                in_hours = self.le_hours.text().strip()
                if not Validator.is_positive_int(in_hours, FeeEmployee.MAX_HOURS):
                    QMessageBox.critical(self, 'Error', f'Las horas trabajadas deben ser un número entero '
                                                        f'entre 1 y {FeeEmployee.MAX_HOURS}')
                    return

                new_employee = FeeEmployee(in_nss, in_first_name, in_last_name, in_name, position, born_date_text,
                                           hometown, int(in_hours))

            self.__employees.append(new_employee)
            self.employee_created.emit(new_employee)
            QMessageBox.information(self, 'Correcto', 'Empleado creado correctamente')
            self.close()
        except Exception as e:
            QMessageBox.critical(self, 'Error inesperado', str(e))

    def clear_fields(self):
        self.le_nss.clear()
        self.le_first_name.clear()
        self.le_last_name.clear()
        self.le_name.clear()
        self.le_hometown.clear()
        self.le_hours.clear()
        self.cb_positions.setCurrentIndex(0)
        self.de_born_date.setDate(QDate(2000, 1, 1))
        self.de_hire_date.setDate(QDate.currentDate())
        self.rb_base_employee.setChecked(True)

    def load_positions(self):
        # Los puestos salen de la tabla puesto → sueldo para no tener dos listas distintas
        self.cb_positions.addItems(BaseEmployee.HOURLY_SALARIES.keys())

    def configure_dates(self):
        # No se permiten fechas futuras en el calendario
        today = QDate.currentDate()
        self.de_born_date.setMaximumDate(today)
        self.de_hire_date.setMaximumDate(today)
        self.de_hire_date.setDate(today)

    def show_panel(self):
        is_base = self.rb_base_employee.isChecked()
        # El sueldo inicial se muestra para los dos tipos; la fecha de ingreso solo aplica a base
        self.lb_hire_date.setVisible(is_base)
        self.de_hire_date.setVisible(is_base)
        self.f_fee_emp.setVisible(not is_base)
        self.update_initial_salary()

    def update_initial_salary(self):
        if self.rb_base_employee.isChecked():
            hourly_salary = BaseEmployee.HOURLY_SALARIES.get(self.cb_positions.currentText(), 0.0)
        else:
            hourly_salary = FeeEmployee.HOURLY_SALARY
        self.lb_base_salary.setText(f'$ {hourly_salary:,.2f} / hora')

    @staticmethod
    def __full_years(start: datetime.date, end: datetime.date) -> int:
        """Años completos entre dos fechas (edad o antigüedad)."""
        years = end.year - start.year
        if (end.month, end.day) < (start.month, start.day):
            years -= 1
        return years
