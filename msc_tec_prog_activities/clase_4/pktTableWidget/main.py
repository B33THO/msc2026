import csv
import sys,os

from PyQt6.QtWidgets import QApplication, QMessageBox, QMainWindow, QFileDialog
from PyQt6.uic import loadUi
from PyQt6 import QtWidgets
from PyQt6.QtCore import Qt

class Main(QMainWindow):
    #Constructor
    def __init__(self,parent=None):
        try:
            super(Main,self).__init__(parent)
            #enviar la ventana
            ui_path = os.path.join(os.path.dirname(__file__), 'mwVentana.ui')
            loadUi(ui_path, self)

            #Define la estructura de la tabla
            self.configurarTabla()
            self.configurarCombos()
            #mando llamar evento
            self.eventos()


        except Exception as e:
            QMessageBox.critical(self,'Error',str(e))

    def eventos(self):
        try:

            self.btnAgregar.clicked.connect(self.agregar)
            self.actionLimpiar.triggered.connect(self.limpiar)
            self.actionLimpiar_2.triggered.connect(self.limpiar)
            self.btnBuscar.clicked.connect(self.busqueda)
            self.btnActualizar.clicked.connect(self.actualizar)
            self.btnEliminar.clicked.connect(self.eliminar)

            #Menu Salir
            self.actionSalir.triggered.connect(self.salir)
            self.actionSalir_2.triggered.connect(self.salir)

            #Evento LineEdit
            self.lneNombre.textChanged.connect(self.convertirMayusculas)
            #Evento TableView
            self.tbwDatos.clicked.connect(self.seleccionarRegistro)

            self.actionGuardar.triggered.connect(self.export_data_as_csv)
            self.actionAbrir.triggered.connect(self.open_csv_file)

        except Exception as e:
            QMessageBox.critical(self, 'Error', str(e))

    def configurarTabla(self):
        try:           
            self.tbwDatos.setColumnCount(5)
            #Crea una lista del encabezado de la tabla
            encabezado=['Clave','Nombre','Carrera','Municipio','Edad']
            self.tbwDatos.setHorizontalHeaderLabels(encabezado)
            self.tbwDatos.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)            
        except Exception as e:
            QMessageBox.critical(self, 'Error', str(e))

    def configurarCombos(self):
        try:
            self.carreras = ['ING. SISTEMAS', 'ING. EN TECNOLOGIAS', 'ING. ELECTRONICA', 'ING. INDUSTRIAL']
            self.cmbCarrera.addItems(self.carreras)
            self.municipios = ['ZAMORA', 'TANGANCICUARO', 'IXTLAN', 'CHAVINDA', 'CHILCHOTA']
            self.cmbMunicipio.addItems(self.municipios)

        except Exception as ex:
            QMessageBox.critical(self, 'Error', str(ex))
    def convertirMayusculas(self,texto):
        try:
            self.lneNombre.setText(texto.upper())
        except Exception as e:
            QMessageBox.critical(self, 'Error', str(e))



    def agregar(self):
        try:           
            clave=self.lneClave.text()
            nombre=self.lneNombre.text()
            carr = self.cmbCarrera.currentText()
            mun = self.cmbMunicipio.currentText()
            edad=str(self.spbEdad.value())

            if not clave.isdigit():
                QMessageBox.information(self,'Información','La clave debe ser numérico.')
                self.lneClave.setFocus()
                return
            if clave=='' or nombre=='':
                QMessageBox.information(self,'Información',
                                        'Faltan datos para ingresar')
                return
            else:
                renglon = self.tbwDatos.rowCount()
                self.tbwDatos.insertRow(renglon)
                self.tbwDatos.setItem(renglon, 0, QtWidgets.QTableWidgetItem(clave))
                self.tbwDatos.setItem(renglon, 1, QtWidgets.QTableWidgetItem(nombre))
                self.tbwDatos.setItem(renglon, 2, QtWidgets.QTableWidgetItem(carr))
                self.tbwDatos.setItem(renglon, 3, QtWidgets.QTableWidgetItem(mun))
                self.tbwDatos.setItem(renglon, 4, QtWidgets.QTableWidgetItem(str(edad)))
            self.limpiar() #Limpia componentes
        except Exception as e:
            QMessageBox.critical(self, 'Error', str(e))

    def limpiar(self):
        # Borrar contenido de componentes
        self.lneClave.clear()
        self.lneNombre.clear()
        self.lneBuscar.clear()
        self.cmbCarrera.setCurrentIndex(0)
        self.cmbMunicipio.setCurrentIndex(0)
        # inicializa SpinBox
        self.spbEdad.setValue(18)
        # Posiciona el cursor en LineEdit Clave
        self.lneClave.setFocus()

    def buscar(self,texto):
        try:
            encuentra = False
            #texto=self.lneBuscar.text()
            items=self.tbwDatos.findItems(texto, Qt.MatchFlag.MatchContains)
            for item in items:
                fila=item.row()
                encuentra=True
                self.posicion = fila
                break
            return encuentra
        except Exception as e:
            QMessageBox.critical(self, 'Error', str(e))

    def busqueda(self):
        try:
            if self.buscar(self.lneBuscar.text()):
                QMessageBox.information(self, 'Búsqueda',
                                        f'Registro encontrado en la posición {self.posicion + 1}')
            else:
                QMessageBox.information(self, 'Búsqueda',
                                        'Clave o nombre no encontrado')
            self.lneBuscar.clear()
        except Exception as e:
            QMessageBox.critical(self, 'Error', str(e))

    def eliminar(self):
        try:
            renglon=self.tbwDatos.selectionModel().selectedRows()
            for index in sorted(renglon, reverse=True):
                self.tbwDatos.removeRow(index.row())


        except Exception as e:
            QMessageBox.critical(self, 'Error', str(e))

    def seleccionarRegistro(self):
        try:
            fila = self.tbwDatos.currentRow()
            self.lneClave.setText(self.tbwDatos.item(fila, 0).text())
            self.lneNombre.setText(self.tbwDatos.item(fila, 1).text())
            self.cmbCarrera.setCurrentText(str(self.tbwDatos.item(fila, 2).text()))
            self.cmbMunicipio.setCurrentText((self.tbwDatos.item(fila, 3).text()))
            self.spbEdad.setValue(int(self.tbwDatos.item(fila, 4).text()))

        except Exception as e:
            QMessageBox.critical(self, 'Error', str(e))

    def actualizar(self):
        try:
            clave = self.lneClave.text()
            nombre = self.lneNombre.text()
            carr = self.cmbCarrera.currentText()
            mun = self.cmbMunicipio.currentText()
            edad = str(self.spbEdad.value())

            if not clave.isdigit():
                QMessageBox.information(self, 'Información', 'La clave debe ser numérica.')
                self.lneClave.setFocus()
                return
            if clave == '' or nombre == '':
                QMessageBox.information(self, 'Información',
                                        'Faltan datos para ingresar')
                return
            if self.buscar(self.lneClave.text()):
                renglon = self.posicion
                self.tbwDatos.setItem(renglon, 0, QtWidgets.QTableWidgetItem(clave))
                self.tbwDatos.setItem(renglon, 1, QtWidgets.QTableWidgetItem(nombre))
                self.tbwDatos.setItem(renglon, 2, QtWidgets.QTableWidgetItem(carr))
                self.tbwDatos.setItem(renglon, 3, QtWidgets.QTableWidgetItem(mun))
                self.tbwDatos.setItem(renglon, 4, QtWidgets.QTableWidgetItem(str(edad)))


        except Exception as e:
            QMessageBox.critical(self, 'Error', str(e))

    def salir(self):
        try:
            resultado=QMessageBox.question(self,'Salir','Está seguro de salir?',
                                           QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)
            if resultado==QMessageBox.StandardButton.Yes:
                sys.exit(app.exec())
        except Exception as e:
            QMessageBox.critical(self, 'Error', str(e))

    def export_data_as_csv(self):
        try:
            if self.tbwDatos.rowCount() == 0:
                QMessageBox.information(self, 'Información', 'Tabla vacia')
                return

            #abiri ventana de dialogo para seleccionar la ruta
            nombre_archivo, _= QFileDialog.getSaveFileName(None, 'Guardar archivo', '', filter='Archivos CSV (*.csv)')
            if nombre_archivo:
                with open(nombre_archivo, mode='w', newline='', encoding='utf-8') as archivo:
                    writer = csv.writer(archivo)
                    encabezado = []
                    for columnas in range(self.tbwDatos.columnCount()):
                        elementoHorizontal = self.tbwDatos.horizontalHeaderItem(columnas)
                        encabezado.append(elementoHorizontal.text() if elementoHorizontal.text() else f'Col_{columnas}')
                    writer.writerow(encabezado)

                    #Guardar las filas de datos
                    for ren in range(self.tbwDatos.rowCount()):
                        datoRenglon=[]
                        for col in range(self.tbwDatos.columnCount()):
                            celda = self.tbwDatos.item(ren, col)
                            datoRenglon.append(celda.text() if celda is not None else '')
                        writer.writerow(datoRenglon)
                    QMessageBox.information(self, 'Correcto', 'Datos exportados')

        except Exception as e:
            QMessageBox.critical(self, 'Error al exportat', str(e))

    def open_csv_file(self):
        try:
            nombre_archivo, _ = QFileDialog.getOpenFileName(None, 'Guardar archivo', '', filter='CSV (*.csv)')

            if nombre_archivo:
                with open(nombre_archivo, mode='r', encoding = 'utf-8') as archivo:
                    reader = csv.reader(archivo)
                    if not reader:
                        QMessageBox(self, 'Info', 'El archivo no tiene datos')
                        return
                    self.tbwDatos.setRowCount(0)
                    self.tbwDatos.setColumnCount(0)

                    for num_fila, fila_datos in enumerate(reader):
                        if num_fila == 0:
                            self.tbwDatos.setColumnCount(len(fila_datos))
                            self.tbwDatos.setHorizontalHeaderLabels(fila_datos)
                            continue

                        self.tbwDatos.insertRow(self.tbwDatos.rowCount())
                        fila_actual = self.tbwDatos.rowCount() - 1
                        for num_columna, dato in enumerate(fila_datos):
                            self.tbwDatos.setItem(fila_actual, num_columna, QtWidgets.QTableWidgetItem(dato))
                    QMessageBox.information(self, 'Correcto', f'Datos exportados desde {nombre_archivo}')

        except Exception as e:
            print(e.with_traceback(None))
            QMessageBox.critical(self, 'Error al importar', str(e))


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    app=QApplication(sys.argv)
    objVentana=Main()
    objVentana.show()
    app.exec()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
