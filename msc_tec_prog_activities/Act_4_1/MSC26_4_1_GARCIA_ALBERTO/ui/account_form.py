from pathlib import Path

from PyQt6 import uic
from PyQt6.QtCore import QDate, pyqtSignal
from PyQt6.QtWidgets import QDialog, QMessageBox

from domain.credit_account import CreditAccount
from services.account_service import AccountService, MAX_AMOUNT, MIN_DATE

UI_FILE = Path(__file__).parent / "Create_Account_Window.ui"


class AccountForm(QDialog):
    #Avisa a la ventana principal que debe recargar la tabla
    saved = pyqtSignal()

    def __init__(self, parent = None, client_account = None):
        super().__init__(parent)
        uic.loadUi(UI_FILE, self) #Carga la ventana diseñada en Qt Designer

        self.__account_service = AccountService()
        #Si recibe un par (Client, cuenta) la ventana es para editar, si no, para crear
        self.__client_account = client_account

        self.config_form()
        self.connect_signals()

        if client_account:
            self.load_account()

    def config_form(self):
        #Por defecto el QDoubleSpinBox solo llega a 99.99
        self.dsb_balance.setMaximum(float(MAX_AMOUNT))
        self.dsb_credit_limit.setMaximum(float(MAX_AMOUNT))
        #La fecha de apertura inicia en hoy y no permite fechas futuras ni anteriores a MIN_DATE
        self.de_created_at.setMinimumDate(QDate(MIN_DATE))
        self.reset_created_at()
        #Inicia como cuenta de ahorro, con el límite de crédito deshabilitado
        self.rb_debit.setChecked(True)
        self.groupBox_3.setEnabled(False)
        self.lb_title.setText("Crear cuenta")
        self.setWindowTitle("Crear cuenta")

    def connect_signals(self):
        #El límite de crédito solo se captura en cuentas de crédito
        self.rb_credit.toggled.connect(self.groupBox_3.setEnabled)
        self.btn_create.clicked.connect(self.save)
        self.btn_cancel.clicked.connect(self.reject)
        self.tbtn_clear_form.clicked.connect(self.clear_form)

    #--------------------------------------------------------------------------
    # MODO EDITAR
    #--------------------------------------------------------------------------
    def load_account(self):
        client, account = self.__client_account
        is_credit = isinstance(account, CreditAccount)

        self.lb_title.setText(f"Cuenta {account.get_account_number()}")
        self.setWindowTitle("Editar cuenta")

        self.le_paternal.setText(client.get_paternal_surname())
        self.le_maternal.setText(client.get_maternal_surname())
        self.le_name.setText(client.get_name())

        #El tipo de cuenta y el saldo no se editan aquí, el saldo cambia con depósitos y retiros
        self.rb_credit.setChecked(is_credit)
        self.rb_debit.setChecked(not is_credit)
        self.groupBox.setEnabled(False)
        self.dsb_balance.setValue(float(account.get_balance()))
        self.dsb_balance.setEnabled(False)
        #La fecha de apertura tampoco se edita
        self.de_created_at.setDate(QDate(account.get_created_at()))
        self.de_created_at.setEnabled(False)

        if is_credit:
            self.dsb_credit_limit.setValue(float(account.get_credit_limit()))

        self.tbtn_clear_form.setVisible(False)

    #--------------------------------------------------------------------------
    # GUARDAR
    #--------------------------------------------------------------------------
    def save(self):
        try:
            if self.__client_account:
                self.update_account()
            else:
                self.create_account()
        except ValueError as e: #Validaciones de los servicios
            QMessageBox.warning(self, "Datos inválidos", str(e))
        except Exception as e: #Errores de la base de datos
            QMessageBox.critical(self, "Error", f"No se pudo guardar la cuenta:\n{e}")

    def create_account(self):
        #Cliente y cuenta se guardan juntos en una transacción: si falla la cuenta
        #tampoco se registra el cliente
        credit_limit = self.dsb_credit_limit.value() if self.rb_credit.isChecked() else None

        client, account = self.__account_service.create_client_with_account(
            self.le_paternal.text(),
            self.le_maternal.text(),
            self.le_name.text(),
            self.dsb_balance.value(),
            self.de_created_at.date().toPyDate(),
            credit_limit
        )

        self.saved.emit()
        QMessageBox.information(self, "Cuenta creada", f"Se creó la cuenta {account.get_account_number()}")
        #Se limpian los controles para capturar otra cuenta
        self.clear_form()

    def update_account(self):
        _, account = self.__client_account

        #Al editar solo cambian el nombre del cliente y, si es de crédito, el límite;
        #se guardan juntos para que un límite inválido no deje el nombre ya cambiado
        credit_limit = self.dsb_credit_limit.value() if isinstance(account, CreditAccount) else None

        self.__account_service.update_client_and_account(
            account.get_account_number(),
            self.le_paternal.text(),
            self.le_maternal.text(),
            self.le_name.text(),
            credit_limit
        )

        self.saved.emit()
        self.accept() #Cierra el diálogo

    #--------------------------------------------------------------------------
    # LIMPIAR
    #--------------------------------------------------------------------------
    def clear_form(self):
        self.le_paternal.clear()
        self.le_maternal.clear()
        self.le_name.clear()
        self.dsb_balance.setValue(0)
        self.dsb_credit_limit.setValue(0)
        self.reset_created_at()
        self.rb_debit.setChecked(True)
        self.le_paternal.setFocus()

    def reset_created_at(self):
        #El máximo se recalcula cada vez: si la ventana sigue abierta después de medianoche
        #el nuevo día debe poder seleccionarse
        today = QDate.currentDate()
        self.de_created_at.setMaximumDate(today)
        self.de_created_at.setDate(today)
