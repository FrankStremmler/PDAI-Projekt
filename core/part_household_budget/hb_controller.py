from PySide6.QtWidgets import QMessageBox, QFileDialog
from .hb_view import HouseholdBudgetView
from .hb_database import ensure_database
from .hb_ai import ReceiptAnalyzer


class HouseholdBudgetController:
    def __init__(self, view: HouseholdBudgetView):
        self.view = view
        ensure_database()
        self.ai = ReceiptAnalyzer()
        self._connect_signals()

    def _connect_signals(self):
        self.view.add_receipt_button.clicked.connect(self.on_add_receipt)
        self.view.scan_receipt_button.clicked.connect(self.on_scan_receipt)


    # Innerhalb Ihrer Controller-Klasse:
    def on_add_receipt(self):
        # 1. Dialog direkt über den Controller öffnen (Nutzt self.view als Parent)
        file_path, _ = QFileDialog.getOpenFileName(
            parent=self.view,
            caption="Quittung auswählen",
            dir="",
            filter="Alle Dateien (*.*);;PDF-Dateien (*.pdf);;Bilder (*.jpg *.jpeg *.png)",
        )

        # 2. Prüfen, ob der Benutzer den Dialog abgebrochen hat
        if not file_path:
            return  # Abbruch ohne weitere Aktion

        # 3. Weiterleitung an das Model (Beispiel für MVC-Datenfluss)
        try:
            # ToDo: self.model.save_receipt_path(file_path)

            # Optionale Erfolgsmeldung in der View anzeigen
            QMessageBox.information(
                self.view,
                "Beleg hinzugefügt",
                f"Der Beleg wurde erfolgreich geladen:\n{file_path}",
            )
        except Exception as e:
            QMessageBox.critical(
                self.view, "Fehler", f"Fehler beim Verarbeiten des Belegs: {str(e)}"
            )
        return file_path


    def on_scan_receipt(self):
        filepath = self.on_add_receipt()  # Öffnet den Dialog und erhält den Pfad
        # QMessageBox.information(
        #     self.view,
        #     "Beleg analysieren",
        #     "Die Beleganalyse mit OpenAI ist als Platzhalter vorgesehen.",
        # )
        self.ai.analyze_receipt(filepath)

