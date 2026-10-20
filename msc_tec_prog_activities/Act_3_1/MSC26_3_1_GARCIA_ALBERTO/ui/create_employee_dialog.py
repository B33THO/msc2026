import os

from PyQt6.QtWidgets import QWidget
from PyQt6.uic import loadUi


class CreateEmployeeDialog(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Crear Empleado")
        path = os.path.join(os.path.dirname(__file__), "create_employee_dialog.ui")
        loadUi(path, self)
        self.events()

    def events(self):
        self.btn_save_employee.clicked.connect(self.save_employee)


    def save_employee(self):
        print('Creando Empleado')

