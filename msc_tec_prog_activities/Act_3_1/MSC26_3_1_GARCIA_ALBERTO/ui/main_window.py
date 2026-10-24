import datetime
import os
from pathlib import Path

from PyQt6.QtCore import Qt, QDir
from PyQt6.QtWidgets import QMainWindow, QApplication, QHeaderView, QTableWidgetItem, QMessageBox, QAbstractItemView
from PyQt6.uic import loadUi

from classes.base_employee import BaseEmployee
from classes.fee_employee import FeeEmployee
from ui.create_employee_dialog import CreateEmployeeDialog
from ui.emp_details_window import EmpDetailsWindow
from ui.help_texts import HelpTexts
from utilities.formatters import Formatter


class Main(QMainWindow):
    def __init__(self, parent=None):
        super(Main, self).__init__(parent)
        main_window_path = os.path.join(os.path.dirname(__file__), 'main_window.ui')
        loadUi(main_window_path, self)
        self.setWindowTitle('Empleados')
        self.employees_list = []
        self.create_employee_dialog = CreateEmployeeDialog(self.employees_list)
        self.emp_details_window = EmpDetailsWindow()
        self.employee_selected = None
        # Empleados en el orden en que se muestran en la tabla (cambia al filtrar con la búsqueda)
        self.shown_employees = self.employees_list
        self.load_styles()
        self.configure_table()
        self.load_default_employees()
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
        self.update_employee_table()


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
        # actionAgregar_Empleado está en el menú y en el toolbar, por eso se conecta una sola vez (más abajo)
        self.actionEditar_Empleado.triggered.connect(lambda: self.open_employee_window(True, self.employee_selected))
        self.actionEliminar_Empleado.triggered.connect(self.delete_selected_employee)
        self.actionVer_Detalle.triggered.connect(lambda: self.open_details_window(self.employee_selected))
        # Doble clic en cualquier celda abre el detalle del empleado de esa fila
        self.tw_employees_table.cellDoubleClicked.connect(
            lambda row, _: self.open_details_window(self.shown_employees[row]))
        # Las señales mandan el empleado, pero aquí solo se necesita refrescar la tabla
        self.create_employee_dialog.employee_created_signal.connect(lambda _: self.update_employee_table())
        # Al editar se reaplica la búsqueda, igual que al eliminar, para no perder el filtro
        self.create_employee_dialog.employee_updated_signal.connect(lambda _: self.search_employee())
        self.le_search.textEdited.connect(self.search_employee)
        self.tw_employees_table.itemSelectionChanged.connect(self.select_employee)
        self.actionSalir.triggered.connect(self.close)
        self.actionAgregar_Empleado.triggered.connect(lambda: self.open_employee_window(False))
        self.actionComo_usar.triggered.connect(lambda: self.show_help('Cómo usar', HelpTexts.how_to_use()))
        self.actionFormulas.triggered.connect(
            lambda: self.show_help('Fórmulas de salario', HelpTexts.salary_formulas()))
        self.actionAcerca_de.triggered.connect(
            lambda: QMessageBox.about(self, 'Acerca de', HelpTexts.about()))
    #-----------------------------------------------------------------------------------------------------------------
    #
    #-----------------------------------------------------------------------------------------------------------------

    def open_employee_window(self, edit_mode:bool=False, employee = None):
        try:
            self.create_employee_dialog.clear_fields()
            self.create_employee_dialog.set_employee(employee)
            self.create_employee_dialog.is_edit_mode(edit_mode)
            self.create_employee_dialog.show()
        except Exception as e:
            QMessageBox.critical(self, 'Error al abrir el empleado', str(e))

    def show_help(self, title: str, html: str):
        # QMessageBox con texto enriquecido para poder usar listas y tablas en la ayuda
        message = QMessageBox(self)
        message.setWindowTitle(title)
        message.setIcon(QMessageBox.Icon.Information)
        message.setTextFormat(Qt.TextFormat.RichText)
        message.setText(html)
        message.exec()

    def open_details_window(self, employee):
        try:
            self.emp_details_window.show_employee(employee)
        except Exception as e:
            QMessageBox.critical(self, 'Error al mostrar el detalle', str(e))

    def select_employee(self):
        try:
            indexes_selected = sorted(
                list(
                    set(index.row() for index in self.tw_employees_table.selectedIndexes()))
            )

            is_one_selected = len(indexes_selected) == 1
            # Sin una sola fila seleccionada no queda guardado el empleado anterior
            self.employee_selected = self.shown_employees[indexes_selected[0]] if is_one_selected else None
            # Las acciones que necesitan un empleado solo se habilitan con una fila seleccionada
            self.actionEditar_Empleado.setEnabled(is_one_selected)
            self.actionEliminar_Empleado.setEnabled(is_one_selected)
            self.actionVer_Detalle.setEnabled(is_one_selected)

        except Exception as e:
            QMessageBox.critical(self, 'Error al seleccionar el empleado', str(e))

    def update_employee_table(self):
        # Al crear se quita el filtro para que se vea el nuevo empleado entre todos los demás
        self.le_search.clear()
        self.fill_table(self.employees_list)

    def fill_table(self, employees):
        # Lo usan tanto la lista completa como la búsqueda, para que la tabla se vea igual en ambos casos
        try:
            self.shown_employees = employees
            self.tw_employees_table.setRowCount(0)
            self.tw_employees_table.setRowCount(len(employees))
            for row, employee in enumerate(employees):
                self.tw_employees_table.setItem(row, self.NSS, QTableWidgetItem(str(employee.get_nss())))
                self.tw_employees_table.setItem(row, self.FIRST_NAME, QTableWidgetItem(employee.get_first_name()))
                self.tw_employees_table.setItem(row, self.LAST_NAME, QTableWidgetItem(employee.get_last_name()))
                self.tw_employees_table.setItem(row, self.NAME, QTableWidgetItem(employee.get_name()))
                self.tw_employees_table.setItem(row, self.POSITION, QTableWidgetItem(employee.get_position()))
                self.tw_employees_table.setItem(row, self.BORN_DATE, QTableWidgetItem(employee.get_born_date()))
                self.tw_employees_table.setItem(row, self.HOMETOWN, QTableWidgetItem(employee.get_hometown()))
                self.tw_employees_table.setItem(row, self.TYPE, QTableWidgetItem(employee.get_type()))
                self.tw_employees_table.setItem(row, self.HOUR_SALARY, self.money_item(employee.get_hourly_salary()))
                self.tw_employees_table.setItem(row, self.SALARY, self.money_item(employee.get_salary()))
            # Al quitar filas la tabla no avisa el cambio de selección: se limpia el empleado y se deshabilitan acciones
            self.select_employee()
        except Exception as e:
            QMessageBox.critical(self, 'Error al actualizar la tabla', str(e))

    @staticmethod
    def money_item(amount: float) -> QTableWidgetItem:
        # Montos alineados a la derecha para que los decimales queden en columna
        item = QTableWidgetItem(Formatter.money(amount))
        item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        return item

    def configure_table(self):
        headers = ['NSS', 'Apellido paterno', 'Apellido Materno', 'Nombre', 'Puesto', 'Fecha de nacimiento',
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
        val = self.le_search.text().strip().lower()

        result = [
            e for e in self.employees_list
                if val in f'{e.get_first_name()} {e.get_last_name()} {e.get_name()} {e.get_nss()}'.lower()
        ]
        self.fill_table(result)

    def delete_selected_employee(self):
        try:
            employee = self.employee_selected
            # NSS y nombre completo para distinguir a empleados con el mismo nombre
            full_name = f'{employee.get_name()} {employee.get_first_name()} {employee.get_last_name()}'
            result = QMessageBox.question(self, 'Eliminar empleado',
                                          f'¿Seguro que desea eliminar al empleado {employee.get_nss()} - {full_name}?',
                                          QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
            if result == QMessageBox.StandardButton.Ok:
                self.employees_list.remove(employee)
                # Se reaplica la búsqueda para no perder el filtro (con el campo vacío muestra a todos)
                self.search_employee()

        except Exception as e:
            QMessageBox.critical(self, 'Error al eliminar el empleado', str(e))

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

