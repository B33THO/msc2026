from datetime import date
from pathlib import Path

from PyQt6 import uic
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import (QAbstractItemView, QFileDialog, QHeaderView, QInputDialog, QMainWindow, QMenu,
                             QMessageBox)

from domain.credit_account import CreditAccount
from services.account_service import AccountExistsError, AccountService, MAX_AMOUNT
from ui.account_form import AccountForm
from utilities.file_handler import read_file, write_file

UI_FILE = Path(__file__).parent / "Main_Window.ui"
#Carpeta donde se abren por defecto los diálogos de exportar / importar
DATA_DIR = Path(__file__).parent.parent / "data"
FILE_FILTER = "CSV (*.csv);;Excel (*.xlsx)"
#Columnas de los archivos; exportar e importar usan el mismo orden para que un
#archivo exportado se pueda volver a importar. El número de cuenta evita duplicados:
#si ya existe en la BD la fila se omite; si viene vacío se genera uno nuevo.
file_headers = [
    "No. Cuenta",
    "Apellido paterno",
    "Apellido materno",
    "Nombre",
    "Tipo",
    "Saldo",
    "Límite de crédito",
    "Adeudo",
    "Fecha de apertura"
]
TYPE_SAVINGS = "AHORRO"
TYPE_CREDIT = "CREDITO"
MAX_ERRORS_SHOWN = 10 #Máximo de errores que se listan en el resumen de importación
table_headers = [
    "No. Cuenta",
    "Nombre del Cliente",
    "Fecha de apertura",
    "Saldo",
    "Límite de crédito",
    "Crédito utilizado",
    "Crédito disponible"
]
#Opciones del comboBox de filtro
FILTER_ALL = "Todas las cuentas"
FILTER_SAVINGS = "Cuentas de ahorro"
FILTER_CREDIT = "Cuentas de crédito"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi(UI_FILE, self) #Carga la ventana diseñada en Qt Designer

        self.__account_service = AccountService()
        #Pares (Client, cuenta) que se muestran en la tabla, en el mismo orden que las filas
        self.__rows = []

        self.config_table()
        self.config_controls()
        self.connect_signals()
        self.load_accounts()

    def config_table(self):
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(table_headers)
        self.tv_clients_table.setModel(self.model)
        self.tv_clients_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        #Tabla de solo lectura y se selecciona la fila completa
        self.tv_clients_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tv_clients_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tv_clients_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        #Habilita el menú propio con clic derecho (show_context_menu)
        self.tv_clients_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

    def config_controls(self):
        self.comboBox.addItems([FILTER_ALL, FILTER_SAVINGS, FILTER_CREDIT])
        self.le_search.setPlaceholderText(" Buscar por número de cuenta (Enter)")
        self.le_search.setClearButtonEnabled(True)
        self.lineEdit.setPlaceholderText(" Cantidad")

    def connect_signals(self):
        self.btn_create_account.clicked.connect(self.open_create_form)
        self.actionCrear_Cuenta.triggered.connect(self.open_create_form)
        self.btn_edit_account.clicked.connect(self.open_edit_form)
        self.btn_delete_account.clicked.connect(self.delete_account)
        self.btn_exit.clicked.connect(self.close)
        self.actionSalir.triggered.connect(self.close)
        self.btn_export.clicked.connect(self.export_file)
        self.actionExportar_Datos.triggered.connect(self.export_file)
        self.btn_import.clicked.connect(self.import_file)
        self.actionImportar_datos.triggered.connect(self.import_file)

        self.comboBox.currentTextChanged.connect(self.load_accounts)
        self.le_search.returnPressed.connect(self.search_by_account_number)
        #Al borrar el texto de búsqueda se vuelve a mostrar el filtro
        self.le_search.textChanged.connect(lambda text: self.load_accounts() if not text else None)
        self.btn_search_amount.clicked.connect(self.search_by_max_balance)
        self.lineEdit.returnPressed.connect(self.search_by_max_balance)

        self.tv_clients_table.customContextMenuRequested.connect(self.show_context_menu)
        self.tv_clients_table.doubleClicked.connect(self.open_edit_form)

    #--------------------------------------------------------------------------
    # TABLA
    #--------------------------------------------------------------------------
    def fill_table(self, client_accounts):
        self.__rows = client_accounts
        self.model.removeRows(0, self.model.rowCount()) #Vacía la tabla antes de llenarla

        for client, account in client_accounts:
            row = [
                str(account.get_account_number()),
                str(client),
                account.get_created_at().strftime("%d/%m/%Y"),
                self.money(account.get_balance())
            ]
            if isinstance(account, CreditAccount):
                row += [
                    self.money(account.get_credit_limit()),
                    self.money(account.get_debt()),
                    self.money(account.get_credit_limit() - account.get_debt())
                ]
            else:
                row += ["", "", ""] #Las de ahorro no tienen datos de crédito

            items = [QStandardItem(value) for value in row]
            #La fecha y los números se alinean a la derecha
            for item in items[2:]:
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.model.appendRow(items)

        self.statusbar.showMessage(f"{len(client_accounts)} cuenta(s)")

    @staticmethod
    def money(value):
        #Formato moneda con separador de miles y 2 decimales, p. ej. $ 1,250.00
        return f"$ {value:,.2f}"

    def selected_client_account(self):
        indexes = self.tv_clients_table.selectionModel().selectedRows()
        if not indexes:
            QMessageBox.information(self, "Selecciona una cuenta", "Primero selecciona una cuenta de la tabla.")
            return None
        #El número de fila de la tabla es el mismo índice en __rows
        return self.__rows[indexes[0].row()]

    #--------------------------------------------------------------------------
    # CONSULTAS
    #--------------------------------------------------------------------------
    def load_accounts(self):
        #Recarga la tabla según el filtro del comboBox
        option = self.comboBox.currentText()
        try:
            if option == FILTER_SAVINGS:
                results = self.__account_service.get_savings_accounts()
            elif option == FILTER_CREDIT:
                results = self.__account_service.get_credit_accounts()
            else:
                results = self.__account_service.get_all()
            self.fill_table(results)
        except Exception as e:
            self.show_error(e)

    def search_by_account_number(self):
        text = self.le_search.text().strip()
        if not text:
            self.load_accounts()
            return

        if not text.isdigit():
            QMessageBox.warning(self, "Datos inválidos", "El número de cuenta debe ser numérico.")
            return

        try:
            #Se pasa como lista porque fill_table espera varios pares
            self.fill_table([self.__account_service.get_by_account_number(int(text))])
        except Exception as e:
            self.show_error(e)

    def search_by_max_balance(self):
        #El servicio valida que la cantidad sea un número no negativo
        try:
            self.fill_table(self.__account_service.get_by_max_balance(self.lineEdit.text().strip()))
        except Exception as e:
            self.show_error(e)

    #--------------------------------------------------------------------------
    # CREAR / EDITAR / ELIMINAR
    #--------------------------------------------------------------------------
    def open_create_form(self):
        form = AccountForm(self)
        form.saved.connect(self.load_accounts) #Recarga la tabla cada vez que se guarda
        form.exec() #exec() abre el diálogo de forma modal

    def open_edit_form(self):
        client_account = self.selected_client_account()
        if not client_account:
            return

        form = AccountForm(self, client_account)
        form.saved.connect(self.load_accounts)
        form.exec()

    def delete_account(self):
        client_account = self.selected_client_account()
        if not client_account:
            return

        client, account = client_account
        answer = QMessageBox.question(
            self, "Eliminar cuenta",
            f"¿Eliminar la cuenta {account.get_account_number()} de {client}?"
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            self.__account_service.delete(account.get_account_number())
            self.load_accounts()
        except Exception as e:
            self.show_error(e)

    #--------------------------------------------------------------------------
    # DEPOSITAR / RETIRAR (clic derecho sobre la tabla)
    #--------------------------------------------------------------------------
    def show_context_menu(self, position):
        #Solo se muestra si el clic fue sobre una fila
        if not self.tv_clients_table.indexAt(position).isValid():
            return

        menu = QMenu(self)
        menu.addAction("Depositar", self.deposit)
        menu.addAction("Retirar", self.withdraw)
        menu.addSeparator()
        menu.addAction("Editar", self.open_edit_form)
        menu.addAction("Eliminar", self.delete_account)
        #La posición llega relativa a la tabla y el menú necesita coordenadas de pantalla
        menu.exec(self.tv_clients_table.viewport().mapToGlobal(position))

    def ask_amount(self, title):
        #Diálogo con valor inicial 0, rango de 0 a MAX_AMOUNT y 2 decimales; None si se cancela
        amount, ok = QInputDialog.getDouble(self, title, "Cantidad:", 0, 0, float(MAX_AMOUNT), 2)
        return amount if ok else None

    def deposit(self):
        self.move_money("Depositar", self.__account_service.deposit)

    def withdraw(self):
        self.move_money("Retirar", self.__account_service.withdraw)

    def move_money(self, title, operation):
        #Depositar y retirar solo cambian en la operación del servicio que se llama
        client_account = self.selected_client_account()
        if not client_account:
            return

        amount = self.ask_amount(title)
        if amount is None:
            return

        try:
            operation(client_account[1].get_account_number(), amount)
            self.load_accounts()
        except Exception as e:
            self.show_error(e)

    #--------------------------------------------------------------------------
    # EXPORTAR (guardar la tabla en CSV / XLSX)
    #--------------------------------------------------------------------------
    def export_file(self):
        #Se exporta lo que se ve en la tabla, es decir, respeta el filtro o la búsqueda activa
        if not self.__rows:
            QMessageBox.information(self, "Exportar", "No hay cuentas en la tabla para exportar.")
            return

        #Regresa la ruta elegida y el filtro; la ruta viene vacía si el usuario cancela
        path, _ = QFileDialog.getSaveFileName(self, "Exportar cuentas", str(DATA_DIR / "cuentas.csv"), FILE_FILTER)
        if not path:
            return

        rows = [self.to_file_row(client, account) for client, account in self.__rows]
        try:
            write_file(path, file_headers, rows)
            self.statusbar.showMessage(f"Se exportaron {len(rows)} cuenta(s) a {Path(path).name}")
        except Exception as e:
            self.show_error(e)

    @staticmethod
    def to_file_row(client, account):
        #Se guardan los valores sin formato de moneda ("$ 1,250.00" no se podría volver a leer);
        #se convierten a float porque openpyxl no acepta Decimal
        row = [
            account.get_account_number(),
            client.get_paternal_surname(),
            client.get_maternal_surname(),
            client.get_name()
        ]
        if isinstance(account, CreditAccount):
            row += [TYPE_CREDIT, float(account.get_balance()),
                    float(account.get_credit_limit()), float(account.get_debt())]
        else:
            #Las de ahorro no tienen datos de crédito
            row += [TYPE_SAVINGS, float(account.get_balance()), "", ""]
        #Se guarda como date: en CSV queda como AAAA-MM-DD y en XLSX como celda de fecha
        row.append(account.get_created_at())
        return row

    #--------------------------------------------------------------------------
    # IMPORTAR (cargar cuentas desde CSV / XLSX)
    #--------------------------------------------------------------------------
    def import_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Importar cuentas", str(DATA_DIR), FILE_FILTER)
        if not path:
            return

        try:
            rows = read_file(path)
        except Exception as e:
            self.show_error(e)
            return

        imported = 0
        skipped = 0 #Filas cuyo número de cuenta ya existe en la BD
        without_date = 0 #Filas importadas que no traían fecha de apertura
        errors = []
        #start=2 para que el número coincida con la fila del archivo (la 1 es el encabezado)
        for row_number, row in enumerate(rows, start=2):
            #Se ignoran las filas vacías (comunes al final de los archivos de Excel)
            if not any(self.cell(row, i) for i in range(len(file_headers))):
                continue
            try:
                if not self.import_row(row):
                    without_date += 1
                imported += 1
            except AccountExistsError:
                #La cuenta ya está registrada (p. ej. se importa de nuevo un archivo exportado)
                skipped += 1
            except Exception as e:
                #Una fila con error no detiene la importación, se registra y se sigue con la siguiente
                errors.append(f"Fila {row_number}: {e}")

        #Las cuentas se guardaron en la BD, así que se recarga la tabla desde ahí
        self.load_accounts()
        self.show_import_summary(imported, skipped, without_date, errors)

    @staticmethod
    def cell(row, index):
        #Regresa el valor de la columna como texto limpio; "" si la fila es más corta o la celda
        #está vacía (en XLSX llega como None y str(None) sería "None")
        if index >= len(row) or row[index] is None:
            return ""
        return str(row[index]).strip()

    def import_row(self, row):
        account_type = self.cell(row, 4).upper().replace("É", "E") #Acepta CREDITO y CRÉDITO
        if account_type not in (TYPE_SAVINGS, TYPE_CREDIT):
            raise ValueError(f"Tipo de cuenta '{self.cell(row, 4)}' inválido, usa {TYPE_SAVINGS} o {TYPE_CREDIT}")

        #Sin número de cuenta (archivo hecho a mano) se genera uno nuevo al guardar
        account_number = self.cell(row, 0) or None

        #Se pasa el valor original (no self.cell) porque en XLSX la fecha llega como datetime o número;
        #si el archivo no trae fecha se toma hoy y se avisa
        has_date = bool(self.cell(row, 8))
        created_at = row[8] if has_date else date.today()

        #Si es de ahorro no se pasa límite (None) ni adeudo; si la de crédito no trae adeudo se toma como 0
        credit_limit = None
        debt = 0
        if account_type == TYPE_CREDIT:
            credit_limit = self.cell(row, 6)
            debt = self.cell(row, 7) or 0

        #Cliente y cuenta se guardan en una sola transacción, si algo falla no queda ninguno.
        #Si el número de cuenta ya existe se lanza AccountExistsError y la fila se omite
        self.__account_service.create_client_with_account(
            self.cell(row, 1), self.cell(row, 2), self.cell(row, 3),
            self.cell(row, 5), created_at, credit_limit, debt, account_number
        )

        return has_date

    def show_import_summary(self, imported, skipped, without_date, errors):
        message = f"Se importaron {imported} cuenta(s)."
        if skipped:
            message += f"\nSe omitieron {skipped} cuenta(s) que ya existían."
        if without_date:
            message += (f"\n{without_date} cuenta(s) no traían fecha de apertura "
                        f"y se registraron con la fecha de hoy.")
        if not errors:
            QMessageBox.information(self, "Importar", message)
            return

        #Si hay muchos errores solo se listan los primeros para que el mensaje quepa en pantalla
        message += f"\n\n{len(errors)} fila(s) con error:\n" + "\n".join(errors[:MAX_ERRORS_SHOWN])
        if len(errors) > MAX_ERRORS_SHOWN:
            message += f"\n... y {len(errors) - MAX_ERRORS_SHOWN} más"
        QMessageBox.warning(self, "Importar", message)

    #--------------------------------------------------------------------------
    # ERRORES
    #--------------------------------------------------------------------------
    def show_error(self, error):
        #Los ValueError son reglas de negocio del servicio, lo demás es error de BD
        if isinstance(error, ValueError):
            QMessageBox.warning(self, "Aviso", str(error))
        else:
            QMessageBox.critical(self, "Error", f"Ocurrió un error con la base de datos:\n{error}")
