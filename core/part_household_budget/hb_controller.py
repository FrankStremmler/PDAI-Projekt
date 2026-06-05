from PySide6.QtWidgets import QMessageBox
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

    def on_add_receipt(self):
        QMessageBox.information(
            self.view,
            "Beleg hinzufügen",
            "Diese Funktion ist noch nicht implementiert.",
        )

    def on_scan_receipt(self):
        QMessageBox.information(
            self.view,
            "Beleg analysieren",
            "Die Beleganalyse mit OpenAI ist als Platzhalter vorgesehen.",
        )
