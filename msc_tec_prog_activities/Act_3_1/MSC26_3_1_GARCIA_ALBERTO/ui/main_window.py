import os
from pathlib import Path

from PyQt6.QtWidgets import QMainWindow, QApplication, QHeaderView, QTableWidgetItem
from PyQt6.uic import loadUi

from Act_3_1.MSC26_3_1_GARCIA_ALBERTO.ui.create_employee_dialog import CreateEmployeeDialog


class Main(QMainWindow):
    def __init__(self, parent=None):
        super(Main, self).__init__(parent)
        main_window_path = os.path.join(os.path.dirname(__file__), 'main_window.ui')
        loadUi(main_window_path, self)
        self.employees_list = []
        self.load_styles()
        self.configure_table()
        self.create_employee_dialog = CreateEmployeeDialog(self.employees_list)
        self.events()


    def load_styles(self):
        # Cargar y aplicar la hoja de estilo
        qss_path = Path(__file__).parent / 'styles.qss'
        if qss_path.exists():
            with open(qss_path, 'r', encoding='utf-8') as f:
                QApplication.instance().setStyleSheet(f.read())

    def events(self):
        self.btn_add_employee.clicked.connect(self.open_create_employee_window)
        self.create_employee_dialog.employee_created.connect(self.update_employee_table)

    def open_create_employee_window(self):
        self.create_employee_dialog.show()

    def update_employee_table(self, employee):
        try:

            self.employees_list.append(employee)
            self.tw_employees_table.setRowCount(len(self.employees_list))
            for row, employee in enumerate(self.employees_list):
                nss = str(employee.get_nss())
                first_name = employee.get_first_name()
                last_name = employee.get_last_name()
                name = employee.get_name()
                born_date = employee.get_born_date()
                position = employee.get_position()
                hometown = employee.get_hometown()

                self.tw_employees_table.setItem(row, 0, QTableWidgetItem(str(nss)))
                self.tw_employees_table.setItem(row, 1, QTableWidgetItem(str(first_name)))
                self.tw_employees_table.setItem(row, 2, QTableWidgetItem(str(last_name)))
                self.tw_employees_table.setItem(row, 3, QTableWidgetItem(str(name)))
                self.tw_employees_table.setItem(row, 4, QTableWidgetItem(str(born_date)))
                self.tw_employees_table.setItem(row, 5, QTableWidgetItem(str(position)))
                self.tw_employees_table.setItem(row, 6, QTableWidgetItem(str(hometown)))
        except Exception as e:
            print(e)

    def configure_table(self):
        headers = ['NSS', 'Apellido paterno', 'Apellido Materno', 'Nombre', 'Posición', 'Fecha de nacimiento', 'Lugar de procedencia']
        self.tw_employees_table.setColumnCount(len(headers))
        self.tw_employees_table.setHorizontalHeaderLabels(headers)
        self.tw_employees_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)