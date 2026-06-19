import os
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox

from .hb_view import HouseholdBudgetView
from .hb_database import ensure_database
from .hb_file_input_controller import AIPlatformWrapper
from .hb_crud_controller import CrudController, DuplicateError
from .hb_receipt_review_dialog import ReceiptReviewDialog
from .hb_statement_review_dialog import BankStatementReviewDialog
from .hb_config_model import ConfigManager
from standards_and_constants.view_constants import FONT_SIZE_BODY
from standards_and_constants.hb_prompts_constants import (
    RECEIPTS_FOLDER, STATEMENTS_FOLDER, SUPPORTED_EXTENSIONS,
    PROVIDER_GEMINI, PROVIDER_OPENAI,
)


class AnalysisWorker(QThread):
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, file_path: str, mime_type: str, doc_type: str):
        super().__init__()
        self.file_path = file_path
        self.mime_type = mime_type
        self.doc_type = doc_type
        self.wrapper = AIPlatformWrapper()

    def run(self):
        try:
            if self.doc_type == "receipt":
                result = self.wrapper.analyze_receipt(self.file_path, self.mime_type)
            else:
                result = self.wrapper.analyze_bank_statement(self.file_path, self.mime_type)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class HouseholdBudgetController:
    def __init__(self, view: HouseholdBudgetView, drive_service=None):
        self.view = view
        self.db = ensure_database(drive_service=drive_service)
        self.crud = CrudController(self.db)

        self.view.btn_analyze.clicked.connect(self.start_receipt_analysis)
        self.view.btn_analyze_statement.clicked.connect(self.start_bank_statement_analysis)
        self.view.btn_switch_provider.clicked.connect(self.toggle_ai_provider)
        self.view.receipt_delete_requested.connect(self._delete_receipt)
        self.view.statement_delete_requested.connect(self._delete_bank_statement)
        self.refresh_tables()

    def toggle_ai_provider(self):
        cfg = ConfigManager()
        current = cfg.config.ai_provider
        cfg.config.ai_provider = PROVIDER_OPENAI if current == PROVIDER_GEMINI else PROVIDER_GEMINI
        cfg.save_config()
        self.view.update_analyze_button()

    def save_to_drive(self):
        self.db.save_to_drive()
        self.db.dispose()

    def _delete_receipt(self, receipt_id: int):
        reply = QMessageBox.question(
            self.view, "Löschen bestätigen",
            f"Beleg ID={receipt_id} wirklich löschen?\nAlle zugehörigen Artikel werden ebenfalls gelöscht.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.crud.delete_receipt(receipt_id):
                self.refresh_tables()
            else:
                self._show_error("Fehler beim Löschen des Belegs.")

    def _delete_bank_statement(self, statement_id: int):
        reply = QMessageBox.question(
            self.view, "Löschen bestätigen",
            f"Kontoauszug ID={statement_id} wirklich löschen?\nAlle zugehörigen Buchungspositionen werden ebenfalls gelöscht.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.crud.delete_bank_statement(statement_id):
                self.refresh_tables()
            else:
                self._show_error("Fehler beim Löschen des Kontoauszugs.")

    def refresh_tables(self):
        self.view.update_table_data(self.crud.get_all_receipts())
        self.view.update_statement_table(self.crud.get_all_bank_statements())

    def start_receipt_analysis(self):
        filter_str = "Unterstützte Formate (*.pdf *.jpg *.jpeg *.png);;Alle Dateien (*.*)"
        file_path, _ = QFileDialog.getOpenFileName(
            self.view, "Kassenzettel auswählen", RECEIPTS_FOLDER, filter_str
        )
        if not file_path:
            return

        ext = os.path.splitext(file_path)[1].lstrip(".").lower()
        mime_type = SUPPORTED_EXTENSIONS.get(ext, "application/octet-stream")
        self.view.set_loading_state(True)

        self._ensure_input_dirs()

        self.worker = AnalysisWorker(file_path, mime_type, "receipt")
        self.worker.finished.connect(self._on_receipt_analysis_success)
        self.worker.error.connect(self._on_analysis_error)
        self.worker.start()

    def start_bank_statement_analysis(self):
        filter_str = "Unterstützte Formate (*.pdf *.jpg *.jpeg *.png);;Alle Dateien (*.*)"
        file_path, _ = QFileDialog.getOpenFileName(
            self.view, "Kontoauszug auswählen", STATEMENTS_FOLDER, filter_str
        )
        if not file_path:
            return

        ext = os.path.splitext(file_path)[1].lstrip(".").lower()
        mime_type = SUPPORTED_EXTENSIONS.get(ext, "application/octet-stream")
        self.view.set_loading_state(True)

        self._ensure_input_dirs()

        self.worker = AnalysisWorker(file_path, mime_type, "statement")
        self.worker.finished.connect(self._on_statement_analysis_success)
        self.worker.error.connect(self._on_analysis_error)
        self.worker.start()

    def _ensure_input_dirs(self):
        for d in [RECEIPTS_FOLDER, STATEMENTS_FOLDER]:
            if not os.path.exists(d):
                try:
                    os.makedirs(d)
                except OSError:
                    pass

    def _on_receipt_analysis_success(self, normalized_receipt):
        self.view.set_loading_state(False)
        if not normalized_receipt:
            self._show_error("Die KI hat keine strukturierten Daten zurückgegeben.")
            return

        normalized_receipt.merchant = self.crud.normalize_merchant(normalized_receipt.merchant)

        dup = self.crud.find_duplicate_receipt(normalized_receipt)
        if dup:
            msg = QMessageBox(self.view)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Beleg vorhanden")
            msg.setMinimumWidth(600)
            msg.setStyleSheet(f"font-size: {FONT_SIZE_BODY}px;")
            msg.setText("Ein Beleg mit denselben Daten existiert bereits:")
            msg.setInformativeText(
                f"Vorhanden: {dup.datum.strftime('%d.%m.%Y %H:%M:%S')} | {dup.merchant} | {float(dup.total_sum):.2f}€\n"
                f"Neu:       {normalized_receipt.date_time} | {normalized_receipt.merchant} | {normalized_receipt.total_sum:.2f}€"
            )
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec()
            return

        dialog = ReceiptReviewDialog(normalized_receipt, self.view)
        if dialog.exec():
            reviewed = dialog.get_receipt()
            try:
                if self.crud.save_receipt(reviewed):
                    self.refresh_tables()
                else:
                    self._show_error("Fehler beim Schreiben in die Datenbank.")
            except DuplicateError as e:
                msg = QMessageBox(self.view)
                msg.setIcon(QMessageBox.Icon.Warning)
                msg.setWindowTitle("Beleg vorhanden")
                msg.setMinimumWidth(600)
                msg.setText("Ein Beleg mit denselben Daten existiert bereits:")
                msg.setInformativeText(f"Vorhanden: {e.db_entry}\nNeu:       {e.new_entry}")
                msg.setStandardButtons(QMessageBox.StandardButton.Ok)
                msg.exec()

    def _on_statement_analysis_success(self, normalized_statement):
        self.view.set_loading_state(False)
        if not normalized_statement:
            self._show_error("Die KI hat keine strukturierten Daten zurückgegeben.")
            return

        dialog = BankStatementReviewDialog(normalized_statement, self.view)
        if dialog.exec():
            reviewed = dialog.get_statement()
            if self.crud.save_bank_statement(reviewed):
                self.refresh_tables()
            else:
                self._show_error("Fehler beim Schreiben in die Datenbank.")

    def _on_analysis_error(self, error_msg):
        self.view.set_loading_state(False)
        print(f"[Controller] Fehler: {error_msg}")
        self._show_error(str(error_msg))

    def _show_error(self, message: str):
        msg = QMessageBox(self.view)
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("Fehler")
        msg.setText("Die Datei konnte nicht verarbeitet werden.")
        msg.setInformativeText(message)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()
