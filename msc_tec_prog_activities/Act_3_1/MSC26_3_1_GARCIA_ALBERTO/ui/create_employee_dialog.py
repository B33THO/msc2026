import datetime
import os

from PyQt6.QtCore import pyqtSignal, Qt, QDate
from PyQt6.QtWidgets import QWidget, QMessageBox
from PyQt6.uic import loadUi

from classes.base_employee import BaseEmployee
from classes.employee import Employee
from classes.fee_employee import FeeEmployee
from utilities.dates import Dates
from utilities.formatters import Formatter
from utilities.validators import Validator


class CreateEmployeeDialog(QWidget):
    employee_created_signal = pyqtSignal(Employee)
    # Señal aparte para que la ventana principal pueda conservar el filtro de búsqueda al editar
    employee_updated_signal = pyqtSignal(Employee)
    def __init__(self, employees):
        super().__init__()
        self.setWindowTitle("Crear Empleado")
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        path = os.path.join(os.path.dirname(__file__), "create_employee_dialog.ui")
        loadUi(path, self)
        self.load_positions()
        self.configure_dates()

        #Empleado seleccionado para editar
        self.employee_selected = None
        self.__is_edit = False
        self.__employees = employees
        self.rb_base_employee.setChecked(True)
        self.events()
        # setChecked se llama antes de conectar las señales, así que el panel se ajusta a mano la primera vez
        self.show_panel()

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
    #-----------------------------------------------------------------------------------------------------------------
    def set_employee(self, employee):
        self.employee_selected = employee

    def is_edit_mode(self, is_edit):
        self.__is_edit = is_edit
        title = "Editar Empleado" if self.__is_edit else "Crear Empleado"
        self.setWindowTitle(title)
        self.lbl_title.setText(title)

        # NSS, tipo, puesto y fecha de ingreso no se actualizan según los requerimientos
        self.btn_clear.setEnabled(not is_edit)
        self.le_nss.setEnabled(not is_edit)
        self.rb_base_employee.setEnabled(not is_edit)
        self.rb_fee_employee.setEnabled(not is_edit)
        self.cb_positions.setEnabled(not is_edit)
        self.de_hire_date.setEnabled(not is_edit)

        # Al crear el sueldo es el fijo del puesto (solo se muestra); al editar se puede actualizar
        self.lbl_salary_title.setText('Sueldo por hora' if is_edit else 'Sueldo Inicial')
        self.lb_base_salary.setVisible(not is_edit)
        self.le_hourly_salary.setVisible(is_edit)

        if not is_edit:
            # clear_fields() no dispara las señales si el combo y el radio ya estaban en su valor inicial
            self.update_initial_salary()
            return

        employee = self.employee_selected
        if isinstance(employee, BaseEmployee):
            self.rb_base_employee.setChecked(True)
            self.de_hire_date.setDate(employee.get_hire_date())
        else:
            self.rb_fee_employee.setChecked(True)
            self.le_hours.setText(str(employee.get_hours()))

        self.cb_positions.setCurrentText(employee.get_position())

        self.le_nss.setText(str(employee.get_nss()))
        self.le_first_name.setText(employee.get_first_name())
        self.le_last_name.setText(employee.get_last_name())
        self.le_name.setText(employee.get_name())
        self.de_born_date.setDate(QDate.fromString(employee.get_born_date(), 'yyyy-MM-dd'))
        self.le_hometown.setText(employee.get_hometown())

        self.le_hourly_salary.setText(f'{employee.get_hourly_salary():.2f}')

    def save_employee(self):
        try:
            if self.__is_edit:
                self.edit_employee()
                return

            # Cada validador ya mostró su mensaje si regresa None
            form_values = self.get_form_values()
            if form_values is None:
                return
            detail_values = self.get_detail_values()
            if detail_values is None:
                return

            in_nss, in_first_name, in_last_name, in_name = form_values
            born_date_text, hometown, type_value = detail_values
            position = self.cb_positions.currentText()

            if self.rb_base_employee.isChecked():
                new_employee = BaseEmployee(in_nss, in_first_name, in_last_name, in_name, position, born_date_text,
                                            hometown, type_value)
            else:
                new_employee = FeeEmployee(in_nss, in_first_name, in_last_name, in_name, position, born_date_text,
                                           hometown, type_value)

            self.__employees.append(new_employee)
            self.employee_created_signal.emit(new_employee)
            QMessageBox.information(self, 'Correcto', 'Empleado creado correctamente')
            self.close()
        except Exception as e:
            QMessageBox.critical(self, 'Error inesperado', str(e))

    def edit_employee(self):
        # Los errores inesperados los atrapa save_employee, que es quien llama a este método
        form_values = self.get_form_values()
        if form_values is None:
            return
        detail_values = self.get_detail_values()
        if detail_values is None:
            return

        # El NSS no se edita, por eso se ignora
        _, in_first_name, in_last_name, in_name = form_values
        born_date_text, hometown, type_value = detail_values

        in_hourly_salary = self.le_hourly_salary.text().strip()
        if not Validator.is_amount(in_hourly_salary):
            QMessageBox.critical(self, 'Error', f'El sueldo por hora debe ser un monto mayor que 0 y hasta '
                                                f'{Formatter.money(Validator.MAX_AMOUNT)}, con máximo 2 '
                                                f'decimales, por ejemplo 150.50')
            return

        employee = self.employee_selected
        employee.set_first_name(in_first_name)
        employee.set_last_name(in_last_name)
        employee.set_name(in_name)
        employee.set_born_date(born_date_text)
        employee.set_hometown(hometown)
        employee.set_hourly_salary(float(in_hourly_salary))
        if isinstance(employee, FeeEmployee):
            employee.set_hours(type_value)

        self.employee_updated_signal.emit(employee)
        QMessageBox.information(self, 'Correcto', 'Empleado actualizado correctamente')
        self.close()

    def get_detail_values(self):
        """Valida fecha de nacimiento, procedencia y el dato según el tipo (fecha de ingreso u horas)."""
        #------------------------------------Fecha de nacimiento-----------------------------------------------------
        born_date = self.de_born_date.date().toPyDate()
        if Dates.full_years(born_date, datetime.date.today()) < Employee.MIN_AGE:
            QMessageBox.critical(self, 'Error', f'El empleado debe tener al menos {Employee.MIN_AGE} años')
            return

        hometown = self.le_hometown.text().strip()
        if not Validator.is_name(hometown):
            QMessageBox.critical(self,'Error', 'Ingrese un lugar de procedencia válido')
            return

        #------------------------------------Datos según el tipo de empleado-----------------------------------------
        # Se guarda la fecha como texto ISO (aaaa-mm-dd) para no depender del formato regional
        born_date_text = born_date.isoformat()
        if self.rb_base_employee.isChecked():
            if self.__is_edit:
                # La fecha de ingreso no se edita: se valida contra la guardada y no contra el campo deshabilitado
                hire_date = self.employee_selected.get_hire_date()
                if Dates.full_years(born_date, hire_date) < Employee.MIN_AGE:
                    QMessageBox.critical(self, 'Error', f'A su fecha de ingreso ({hire_date:%d/%m/%Y}), que no se '
                                                        f'puede modificar, el empleado debía tener al menos '
                                                        f'{Employee.MIN_AGE} años. Revise la fecha de nacimiento')
                    return
                return born_date_text, hometown, hire_date

            hire_date = self.de_hire_date.date().toPyDate()
            if hire_date > datetime.date.today():
                QMessageBox.critical(self, 'Error', 'La fecha de ingreso no puede ser futura')
                return
            if Dates.full_years(born_date, hire_date) < Employee.MIN_AGE:
                QMessageBox.critical(self, 'Error', f'A la fecha de ingreso el empleado debía tener al menos '
                                                    f'{Employee.MIN_AGE} años')
                return
            return born_date_text, hometown, hire_date

        in_hours = self.le_hours.text().strip()
        if not Validator.is_positive_int(in_hours, FeeEmployee.MAX_HOURS):
            QMessageBox.critical(self, 'Error', f'Las horas trabajadas deben ser un número entero '
                                                f'entre 1 y {FeeEmployee.MAX_HOURS}')
            return
        return born_date_text, hometown, int(in_hours)

    def get_form_values(self):
        in_nss = self.le_nss.text().strip()
        if not Validator.is_nss_number(in_nss):
            QMessageBox.critical(self, 'NSS inválido', 'El NSS debe tener 5 dígitos y no empezar con 0')
            return
        if not self.__is_edit:
            for em in self.__employees:
                if em.get_nss() == in_nss:
                    QMessageBox.warning(self, 'NSS duplicado', 'Ya existe un empleado con ese NSS')
                    return

        in_first_name = self.le_first_name.text().strip()
        if not Validator.is_name(in_first_name):
            QMessageBox.critical(self, 'Error', 'Ingrese un apellido paterno válido')
            return

        in_last_name = self.le_last_name.text().strip()
        if not Validator.is_name(in_last_name):
            QMessageBox.critical(self, 'Error', 'Ingrese un apellido materno válido')
            return

        in_name = self.le_name.text().strip()
        if not Validator.is_name(in_name):
            QMessageBox.critical(self, 'Error', 'Ingrese un nombre válido')
            return
        return in_nss, in_first_name, in_last_name, in_name

    def clear_fields(self):
        self.le_nss.clear()
        self.le_first_name.clear()
        self.le_last_name.clear()
        self.le_name.clear()
        self.le_hometown.clear()
        self.le_hours.clear()
        self.le_hourly_salary.clear()
        self.cb_positions.setCurrentIndex(0)
        self.de_born_date.setDate(QDate(2000, 1, 1))
        # Se actualiza el máximo de las fechas por si la aplicación sigue abierta de un día a otro
        self.configure_dates()
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
        self.lb_base_salary.setText(f'{Formatter.money(hourly_salary)} / hora')
