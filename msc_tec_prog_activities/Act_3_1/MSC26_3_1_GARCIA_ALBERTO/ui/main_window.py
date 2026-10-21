import datetime
import os
from pathlib import Path

from PyQt6.QtCore import Qt, QDir
from PyQt6.QtWidgets import QMainWindow, QApplication, QHeaderView, QTableWidgetItem, QMessageBox, QAbstractItemView
from PyQt6.uic import loadUi

from Act_3_1.MSC26_3_1_GARCIA_ALBERTO.classes.base_employee import BaseEmployee
from Act_3_1.MSC26_3_1_GARCIA_ALBERTO.classes.fee_employee import FeeEmployee
from Act_3_1.MSC26_3_1_GARCIA_ALBERTO.ui.create_employee_dialog import CreateEmployeeDialog

class Main(QMainWindow):
    def __init__(self, parent=None):
        super(Main, self).__init__(parent)
        main_window_path = os.path.join(os.path.dirname(__file__), 'main_window.ui')
        loadUi(main_window_path, self)
        self.setWindowTitle('Empleados')
        self.employees_list = []
        self.load_styles()
        self.configure_table()
        self.load_default_employees()
        self.create_employee_dialog = CreateEmployeeDialog(self.employees_list)
        self.events()

    def load_default_employees(self):
        # Empleados de prueba para no capturar datos cada vez que se abre la aplicación
        self.employees_list.extend([
            BaseEmployee('10001', 'Brito', 'Delgado', 'Alan', 'Programador', '1990-03-15', 'Monterrey',
                         datetime.date(2015, 6, 1)),
            BaseEmployee('10002', 'Quito', 'Madera', 'Esteban', 'Analista', '1985-11-02', 'Guadalajara',
                         datetime.date(2010, 1, 15)),
            BaseEmployee('10003', 'Vaca', 'del Corral', 'Zoila', 'Soporte Técnico', '1995-07-20', 'Saltillo',
                         datetime.date(2020, 9, 1)),
            BaseEmployee('10004', 'Galindo', 'Según', 'Mónica', 'Administrador de BD', '1988-01-30', 'Puebla',
                         datetime.date(2012, 3, 10)),
            BaseEmployee('10005', 'Tilla', 'de Patata', 'Aitor', 'Líder de Proyecto', '1980-05-05', 'Querétaro',
                         datetime.date(2005, 8, 22)),
            FeeEmployee('20001', 'Bronca', 'Segura', 'Armando', 'Programador', '1992-09-12', 'Mérida', 40),
            FeeEmployee('20002', 'Mento', 'Mucho', 'Lola', 'Analista', '1998-12-24', 'Toluca', 35),
            FeeEmployee('20003', 'Oria', 'Buena', 'Susana', 'Soporte Técnico', '1993-04-18', 'León', 45),
            FeeEmployee('20004', 'Pato', 'Rojo', 'Elsa', 'Administrador de BD', '1987-10-08', 'Morelia', 52),
            FeeEmployee('20005', 'Lisa', 'Cruz', 'Ana', 'Líder de Proyecto', '1991-02-14', 'Oaxaca', 60),
        ])
        self.update_employee_table(None)


    def load_styles(self):
        # Prefijo "icons:" para usar url(icons:archivo.svg) en el qss sin depender de la carpeta de ejecución
        QDir.addSearchPath('icons', str(Path(__file__).parent.parent / 'icons'))
        # Cargar y aplicar la hoja de estilo
        qss_path = Path(__file__).parent / 'styles.qss'
        if qss_path.exists():
            with open(qss_path, 'r', encoding='utf-8') as f:
                QApplication.instance().setStyleSheet(f.read())
    #-----------------------------------------------------------------------------------------------------------------
    # EVENTS
    #-----------------------------------------------------------------------------------------------------------------
    def events(self):
        self.btn_add_employee.clicked.connect(self.open_create_employee_window)
        self.create_employee_dialog.employee_created.connect(self.update_employee_table)
        self.le_search.textEdited.connect(self.search_employee)

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

    def search_employee(self):
        try:
            val = self.le_search.text().strip().lower()

            result = [
                e for e in self.employees_list
                    if val in f'{e.get_first_name()} {e.get_last_name()} {e.get_nss()}'.lower()
            ]
            self.tw_employees_table.setRowCount(0)
            self.tw_employees_table.setRowCount(len(result))
            for line, employee in enumerate(result):
                print(employee)
                self.tw_employees_table.setItem(line, self.NSS, QTableWidgetItem(employee.get_nss()))
                self.tw_employees_table.setItem(line, self.FIRST_NAME, QTableWidgetItem(employee.get_first_name()))
                self.tw_employees_table.setItem(line, self.LAST_NAME, QTableWidgetItem(employee.get_last_name()))
                self.tw_employees_table.setItem(line, self.NAME, QTableWidgetItem(employee.get_name()))
                self.tw_employees_table.setItem(line, self.POSITION, QTableWidgetItem(employee.get_position()))
                self.tw_employees_table.setItem(line, self.POSITION, QTableWidgetItem(employee.get_position()))
                self.tw_employees_table.setItem(line, self.BORN_DATE, QTableWidgetItem(employee.get_born_date()))
                self.tw_employees_table.setItem(line, self.HOMETOWN, QTableWidgetItem(employee.get_hometown()))
                current_type = employee.get_type()
                print(current_type)
                self.tw_employees_table.setItem(line, self.TYPE, QTableWidgetItem(current_type))

                if current_type == 'Honorarios':
                    self.tw_employees_table.setItem(line, self.HOUR_SALARY, QTableWidgetItem(f'{employee.get_hourly_salary():.2f}'))

                if current_type == 'Base':
                    self.tw_employees_table.setItem(line, self.HOUR_SALARY, QTableWidgetItem(f'{employee.get_hourly_salary():.2f}'))

                self.tw_employees_table.setItem(line, self.SALARY, QTableWidgetItem(f'{employee.get_salary():.2f}'))
        except Exception as e:
            print(e)


    NSS = 0
    FIRST_NAME = 1
    LAST_NAME = 2
    NAME = 3
    POSITION = 4
    BORN_DATE = 5
    HOMETOWN = 6
    TYPE = 7
    HOUR_SALARY = 8
    SALARY = 9

