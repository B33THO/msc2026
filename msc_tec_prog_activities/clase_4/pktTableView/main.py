import csv

from PyQt6.QtWidgets import QApplication, QMessageBox, QMainWindow, QFileDialog
from PyQt6.uic import loadUi
from PyQt6.QtGui import QStandardItemModel,QStandardItem
from PyQt6 import QtCore, QtWidgets
from PyQt6.QtCore import Qt, QModelIndex

import sys,os

from pktTableView.connection import Connection


class Main(QMainWindow):
    #Constructor
    def __init__(self,parent=None):
        try:
            self.__db = Connection('localhost', 'tdpdb', 'postgres', '31416nche')


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
            #Evento del menu y toolbox

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
            self.tbvDatos.clicked.connect(self.seleccionarRegistro)

            self.actionGuardar.triggered.connect(self.export_data_as_csv)
            self.actionAbrir.triggered.connect(self.open_csv_file)
        except Exception as e:
            QMessageBox.critical(self, 'Error', str(e))

    def configurarTabla(self):
        try:
            # Defino modelo de la tabla
            self.modelo = QStandardItemModel()
            #Crea una lista del encabezado de la tabla
            encabezado=['Clave','Nombre','Carrera','Municipio','Edad']
            #Envio la lista al modelo
            self.modelo.setHorizontalHeaderLabels(encabezado)
            self.tbvDatos.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
            #Envio el modelo al TableView
            conn = self.__db.consultar(self.modelo)
            self.tbvDatos.setModel(self.modelo)
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
            #Obtengo el modelo de la tabla
            self.modelo=self.tbvDatos.model()
            cve=self.lneClave.text()
            nom=self.lneNombre.text()
            carr = self.cmbCarrera.currentText()
            mun = self.cmbMunicipio.currentText()
            edad=str(self.spbEdad.value())
            if cve=='' or nom=='':
                QMessageBox.information(self,'Informacion',
                                        'Faltan datos para ingresar')
            else:
                self.modelo.appendRow([QStandardItem(cve),
                                       QStandardItem(nom),
                                       QStandardItem(carr),
                                       QStandardItem(mun),
                                       QStandardItem(edad)
                                    ])
            self.limpiar() #Limpia componentes
        except Exception as e:
            QMessageBox.critical(self, 'Error', str(e))


    def limpiar(self):
        #Borrar contenido de componentes
        self.lneClave.clear()
        self.lneNombre.clear()
        self.cmbCarrera.setCurrentIndex(0)
        self.cmbMunicipio.setCurrentIndex(0)
        #inicializa SpinBox
        self.spbEdad.setValue(18)
        self.lneBuscar.clear()
        #Posiciona el cursor en LineEdit Clave
        self.lneClave.setFocus()

    def buscar(self,textoBuscar):
        try:
            encuentra=False
            if textoBuscar.isdigit():
                columnaBuscar = 0  # Columna "Clave"
            else:
                columnaBuscar = 1  # Columna "Nombre"
            # Crear un índice de inicio para la búsqueda (Fila 0, Columna 0)
            indiceInicio = self.modelo.index(0, columnaBuscar)
            # Ejecutar la búsqueda utilizando el método match()
            indicesEncontrados = self.modelo.match(
                indiceInicio,
                Qt.ItemDataRole.DisplayRole,
                textoBuscar,
                hits=1,  # Detenerse tras encontrar la primera coincidencia
                flags=Qt.MatchFlag.MatchExactly  # Buscar coincidencia exacta del texto
            )
            if indicesEncontrados:
                # Obtener el primer índice que coincide
                indiceCelda: QModelIndex = indicesEncontrados[0]
                encuentra = True
                self.posicion = indiceCelda.row()  # Fila encontrada

            return encuentra
        except Exception as e:
            QMessageBox.critical(self, 'Error', str(e))

    def busqueda(self):
        try:
            if self.buscar(self.lneBuscar.text()):
                QMessageBox.information(self, 'Busqueda',
                                        f'Registro encontrado en la posicion {self.posicion + 1}')
            else:
                QMessageBox.information(self, 'Busqueda',
                                        'Clave o nombre no encontrado')
            self.lneNombre.clear()
        except Exception as e:
            QMessageBox.critical(self, 'Error', str(e))

    def eliminar(self):
        try:
            # Obtener índices seleccionados
            indicesSeleccionados = self.tbvDatos.selectionModel().selectedIndexes()

            # Extraer filas únicas
            filas = set(index.row() for index in indicesSeleccionados)

            # Eliminar en orden inverso
            for fila in sorted(filas, reverse=True):
                self.modelo.removeRow(fila)
            self.limpiar()

        except Exception as e:
            QMessageBox.critical(self, 'Error', str(e))

    def seleccionarRegistro(self):
        try:
            indices=self.tbvDatos.selectionModel().selectedIndexes()
            for indice in sorted(indices):
                ind=indice.row()
                self.lneClave.setText(self.modelo.data(
                    self.modelo.index(ind, 0)))
                self.lneNombre.setText(self.modelo.data(
                    self.modelo.index(ind, 1)))
                self.cmbCarrera.setCurrentText(self.modelo.data(
                    self.modelo.index(ind, 2)))
                self.cmbMunicipio.setCurrentText(self.modelo.data(
                    self.modelo.index(ind, 3)))
                self.spbEdad.setValue(int(self.modelo.data(
                    self.modelo.index(ind, 4))))
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
            if self.buscar(clave):
                # Actualiza la fila seleccionada
                self.modelo.setData(self.modelo.index(self.posicion, 0), clave)
                self.modelo.setData(self.modelo.index(self.posicion, 1), nombre)
                self.modelo.setData(self.modelo.index(self.posicion, 2), carr)
                self.modelo.setData(self.modelo.index(self.posicion, 3), mun)
                self.modelo.setData(self.modelo.index(self.posicion, 4), edad)


        except Exception as e:
            QMessageBox.critical(self, 'Error', str(e))



    def salir(self):
        try:
            resultado=QMessageBox.question(self,'Salir','Esta seguro de salir?',
                                           QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)
            if resultado==QMessageBox.StandardButton.Yes:
                sys.exit(app.exec())
        except Exception as e:
            QMessageBox.critical(self, 'Error', str(e))

    def export_data_as_csv(self):
        try:
            if self.modelo.rowCount() == 0:
                QMessageBox.information(self, 'Información', 'Tabla vacia')
                return

            #abiri ventana de dialogo para seleccionar la ruta
            nombre_archivo, _= QFileDialog.getSaveFileName(None, 'Guardar archivo', '', filter='Archivos CSV (*.csv)')
            if nombre_archivo:
                with open(nombre_archivo, mode='w', newline='', encoding='utf-8') as archivo:
                    writer = csv.writer(archivo)
                    encabezado = []
                    for columnas in range(self.modelo.columnCount()):
                        nombre_columnas = self.modelo.horizontalHeaderItem(columnas)
                        encabezado.append(nombre_columnas.text() if nombre_columnas.text() else f'Col_{columnas}')
                    writer.writerow(encabezado)

                    #Guardar las filas de datos
                    for ren in range(self.modelo.rowCount()):
                        datoRenglon=[]
                        for col in range(self.modelo.columnCount()):
                            celda = self.modelo.item(ren, col)
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
                    listaDatos = list(reader)

                    #limpiar datos antes de cargar
                    self.modelo.clear()

                    #encabezados
                    encabezados = listaDatos[0]
                    self.modelo.setHorizontalHeaderLabels(encabezados)

                    #agregar los datos

                    for num_fila, fila_datos in enumerate(listaDatos[1:]):
                        fila = [QStandardItem(str(reng)) for reng in fila_datos]
                        self.modelo.appendRow(fila)

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

