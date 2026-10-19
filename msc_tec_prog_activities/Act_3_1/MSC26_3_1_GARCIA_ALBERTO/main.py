import sys

from PyQt6.QtWidgets import QApplication

from Act_3_1.MSC26_3_1_GARCIA_ALBERTO.ui.main_window import Main

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Main()
    window.show()
    app.exec()