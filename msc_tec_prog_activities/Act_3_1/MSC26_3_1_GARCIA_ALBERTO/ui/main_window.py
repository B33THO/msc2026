import os
from pathlib import Path

from PyQt6.QtWidgets import QMainWindow, QApplication
from PyQt6.uic import loadUi


class Main(QMainWindow):
    def __init__(self, parent=None):
        super(Main, self).__init__(parent)
        main_window_path = os.path.join(os.path.dirname(__file__), 'main_window.ui')
        loadUi(main_window_path, self)

        # Cargar y aplicar la hoja de estilo
        # css_path = Path(__file__).parent / 'ui' / 'styles.css'
        # if css_path.exists():
        #     with open(css_path, 'r', encoding='utf-8') as f:
        #         app.setStyleSheet(f.read())