from pathlib import Path

from PyQt6 import uic
from PyQt6.QtGui import QStandardItemModel
from PyQt6.QtWidgets import QMainWindow, QHeaderView

UI_FILE = Path(__file__).parent / "Main_Window.ui"
table_headers = [
    "No. Cuenta",
    "Nombre del Cliente",
    "Saldo",
    "Límite de crédito",
    "Crédito utilizado",
    "Crédito disponible"
]

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi(UI_FILE, self) #Carga la ventana diseñada en Qt Designer
        self.config_table()

    def config_table(self):
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(table_headers)
        self.tv_clients_table.setModel(self.model)
        self.tv_clients_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)

    