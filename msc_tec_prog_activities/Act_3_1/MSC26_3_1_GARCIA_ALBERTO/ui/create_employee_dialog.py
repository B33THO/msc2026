import os

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget, QMessageBox
from PyQt6.uic import loadUi

from Act_3_1.MSC26_3_1_GARCIA_ALBERTO.classes.employee import Employee
from Act_3_1.MSC26_3_1_GARCIA_ALBERTO.utilities.employee_actions import EmployeeActions
from Act_3_1.MSC26_3_1_GARCIA_ALBERTO.utilities.validators import Validator


class CreateEmployeeDialog(QWidget):
    employee_created = pyqtSignal(Employee)
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Crear Empleado")
        path = os.path.join(os.path.dirname(__file__), "create_employee_dialog.ui")
        loadUi(path, self)
        self.events()
        self.load_positions()
        self.emp_actions = EmployeeActions()

    def events(self):
        self.btn_save_employee.clicked.connect(self.save_employee)


    def save_employee(self):
        try:

            nss = self.le_nss.text()
            if not Validator.is_nss_number(nss):
                QMessageBox.critical(self, 'NSS invalido', 'El NSS debe contener 5 números')

            first_name = self.le_first_name.text()
            last_name = self.le_last_name.text()
            name = self.le_name.text()
            born_date = self.de_born_date.text()
            position = self.cb_positions.currentText()
            hometown = self.le_hometown.text()
            new_employee = Employee(nss, first_name, last_name, name, born_date, position, hometown)
            self.employee_created.emit(new_employee)
            QMessageBox.information(self, 'El employee creado', 'El employee creado')
            self.close()
        except Exception as e:
            print(e)

    def load_positions(self):
        positions = ['Programador', 'Analista', 'Soporte Técnico']
        self.cb_positions.addItems(positions)


