from pathlib import Path

from PyQt6 import uic
from PyQt6.QtWidgets import QMainWindow

UI_FILE = Path(__file__).parent / "Main_Window.ui"

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi(UI_FILE, self) #Carga la ventana diseñada en Qt Designer
