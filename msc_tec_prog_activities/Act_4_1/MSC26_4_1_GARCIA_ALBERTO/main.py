import sys
from pathlib import Path

from dotenv import load_dotenv
from PyQt6.QtCore import QDir
from PyQt6.QtWidgets import QApplication

# Se cargan las variables del .env antes de crear cualquier Connection
load_dotenv(Path(__file__).parent / ".env")

from ui.main_window import MainWindow

BASE_DIR = Path(__file__).parent
STYLE_FILE = BASE_DIR / "ui" / "styles.qss"


def load_style():
    #El QSS usa url(icons:archivo.svg); el prefijo "icons:" se resuelve a la carpeta icons
    #del proyecto sin importar desde dónde se ejecute el programa ni si la ruta tiene espacios
    QDir.addSearchPath("icons", str(BASE_DIR / "icons"))
    return STYLE_FILE.read_text(encoding="utf-8")


def main():
    app = QApplication(sys.argv)
    #Fusion se ve igual en todos los sistemas y respeta mejor la hoja de estilos
    app.setStyle("Fusion")
    app.setStyleSheet(load_style())
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
