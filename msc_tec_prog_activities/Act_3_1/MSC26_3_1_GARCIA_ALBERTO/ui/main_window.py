import os
from pathlib import Path

from PyQt6.QtCore import Qt, QDir
from PyQt6.QtWidgets import QMainWindow, QApplication, QHeaderView, QTableWidgetItem, QMessageBox, QAbstractItemView
from PyQt6.uic import loadUi

from ui.create_employee_dialog import CreateEmployeeDialog


class Main(QMainWindow):
    def __init__(self, parent=None):
        super(Main, self).__init__(parent)
        main_window_path = os.path.join(os.path.dirname(__file__), 'main_window.ui')
        loadUi(main_window_path, self)
        self.setWindowTitle('Empleados')
        self.employees_list = []
        self.load_styles()
        self.configure_table()
        self.create_employee_dialog = CreateEmployeeDialog(self.employees_list)
        self.events()


    def load_styles(self):
        # Prefijo "icons:" para usar url(icons:archivo.svg) en el qss sin depender de la carpeta de ejecución
        QDir.addSearchPath('icons', str(Path(__file__).parent.parent / 'icons'))
        # Cargar y aplicar la hoja de estilo
        qss_path = Path(__file__).parent / 'styles.qss'
        if qss_path.exists():
            with open(qss_path, 'r', encoding='utf-8') as f:
                QApplication.instance().setStyleSheet(f.read())

    def events(self):
        self.btn_add_employee.clicked.connect(self.open_create_employee_window)
        self.create_employee_dialog.employee_created.connect(self.update_employee_table)

    def open_create_employee_window(self):
        self.create_employee_dialog.clear_fields()
        self.create_employee_dialog.show()

    def update_employee_table(self, new_employee):
        try:
            self.tw_employees_table.setRowCount(len(self.employees_list))
            for row, employee in enumerate(self.employees_list):
                nss = str(employee.get_nss())
                first_name = employee.get_first_name()
                last_name = employee.get_last_name()
                name = employee.get_name()
                born_date = employee.get_born_date()
                position = employee.get_position()
                hometown = employee.get_hometown()
                employee_type = employee.get_type()
                hourly_salary = employee.get_hourly_salary()
                salary = employee.get_salary()

                self.tw_employees_table.setItem(row, 0, QTableWidgetItem(str(nss)))
                self.tw_employees_table.setItem(row, 1, QTableWidgetItem(str(first_name)))
                self.tw_employees_table.setItem(row, 2, QTableWidgetItem(str(last_name)))
                self.tw_employees_table.setItem(row, 3, QTableWidgetItem(str(name)))
                self.tw_employees_table.setItem(row, 4, QTableWidgetItem(str(position)))
                self.tw_employees_table.setItem(row, 5, QTableWidgetItem(str(born_date)))
                self.tw_employees_table.setItem(row, 6, QTableWidgetItem(str(hometown)))
                self.tw_employees_table.setItem(row, 7, QTableWidgetItem(employee_type))
                self.tw_employees_table.setItem(row, 8, self.money_item(hourly_salary))
                self.tw_employees_table.setItem(row, 9, self.money_item(salary))
        except Exception as e:
            QMessageBox.critical(self, 'Error al actualizar la tabla', str(e))

    @staticmethod
    def money_item(amount: float) -> QTableWidgetItem:
        # Montos alineados a la derecha para que los decimales queden en columna
        item = QTableWidgetItem(f'$ {amount:,.2f}')
        item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        return item

    def configure_table(self):
        headers = ['NSS', 'Apellido paterno', 'Apellido Materno', 'Nombre', 'Posición', 'Fecha de nacimiento',
                   'Lugar de procedencia', 'Tipo', 'Sueldo / hora', 'Salario']
        self.tw_employees_table.setColumnCount(len(headers))
        self.tw_employees_table.setHorizontalHeaderLabels(headers)
        self.tw_employees_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        # Apariencia: filas alternadas (colores en styles.qss), selección por fila y sin edición directa
        self.tw_employees_table.setAlternatingRowColors(True)
        self.tw_employees_table.setShowGrid(False)
        self.tw_employees_table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.tw_employees_table.verticalHeader().setVisible(False)
        self.tw_employees_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tw_employees_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)