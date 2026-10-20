import os
from pathlib import Path

from PyQt6.QtWidgets import QMainWindow, QApplication
from PyQt6.uic import loadUi

from Act_3_1.MSC26_3_1_GARCIA_ALBERTO.ui.create_employee_dialog import CreateEmployeeDialog


class Main(QMainWindow):
    def __init__(self, parent=None):
        super(Main, self).__init__(parent)
        main_window_path = os.path.join(os.path.dirname(__file__), 'main_window.ui')
        loadUi(main_window_path, self)
        self.load_styles()
        self.create_employee_dialog = CreateEmployeeDialog()
        self.events()


    def load_styles(self):
        # Cargar y aplicar la hoja de estilo
        qss_path = Path(__file__).parent / 'styles.qss'
        if qss_path.exists():
            with open(qss_path, 'r', encoding='utf-8') as f:
                QApplication.instance().setStyleSheet(f.read())

    def events(self):
        self.btn_add_employee.clicked.connect(self.open_create_employee_window)

    def open_create_employee_window(self):
        if self.create_employee_dialog is None:
            self.create_employee_dialog = CreateEmployeeDialog()

        self.create_employee_dialog.show()