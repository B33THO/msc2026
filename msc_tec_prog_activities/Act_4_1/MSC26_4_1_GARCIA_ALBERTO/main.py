import sys
from pathlib import Path

from dotenv import load_dotenv
from PyQt6.QtWidgets import QApplication

# Se cargan las variables del .env antes de crear cualquier Connection
load_dotenv(Path(__file__).parent / ".env")

from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
