from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QGroupBox,
    QHeaderView,
    QTextEdit,
)


class HouseholdBudgetView(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Haushaltsbuch")
        self.setMinimumSize(900, 600)

        root_layout = QVBoxLayout(self)

        header = QLabel("Haushaltsbuch")
        header.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 16px;")
        root_layout.addWidget(header)

        overview_box = QGroupBox("Übersicht")
        overview_layout = QHBoxLayout(overview_box)
        self.total_receipts_label = QLabel("Belege: 0")
        self.total_amount_label = QLabel("Gesamtbetrag: 0,00 €")
        self.latest_receipt_label = QLabel("Letzter Beleg: -")
        overview_layout.addWidget(self.total_receipts_label)
        overview_layout.addWidget(self.total_amount_label)
        overview_layout.addWidget(self.latest_receipt_label)
        root_layout.addWidget(overview_box)

        actions_box = QGroupBox("Aktionen")
        actions_layout = QHBoxLayout(actions_box)
        self.add_receipt_button = QPushButton("Beleg hinzufügen")
        self.scan_receipt_button = QPushButton("Kassenbon analysieren")
        actions_layout.addWidget(self.add_receipt_button)
        actions_layout.addWidget(self.scan_receipt_button)
        root_layout.addWidget(actions_box)

        self.receipt_table = QTableWidget(0, 4)
        self.receipt_table.setHorizontalHeaderLabels(["Datum", "Händler", "Gesamt", "Status"])
        self.receipt_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        root_layout.addWidget(self.receipt_table)

        details_box = QGroupBox("Beleg-Details / Analyse")
        details_layout = QVBoxLayout(details_box)
        self.receipt_details_text = QTextEdit()
        self.receipt_details_text.setReadOnly(True)
        self.receipt_details_text.setPlaceholderText(
            "Hier erscheinen später ausgewählte Belegdaten und Analyseergebnisse."
        )
        details_layout.addWidget(self.receipt_details_text)
        root_layout.addWidget(details_box)

        root_layout.addStretch()
