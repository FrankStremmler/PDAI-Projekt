from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from standards_and_constants.view_constants import STATEMENT_DIALOG_MIN_WIDTH, STATEMENT_DIALOG_MIN_HEIGHT
from .hb_base import NormalizedBankStatement, NormalizedBankPosition

POSITION_COLUMNS = ["Buchungsdatum", "Verwendungszweck", "Begünstigter/Auftraggeber", "Betrag", "Warengruppe", "Unterkategorie"]


class BankStatementReviewDialog(QDialog):
    def __init__(self, statement: NormalizedBankStatement, parent=None):
        super().__init__(parent)
        self.original = statement
        self.setWindowTitle("Kontoauszug-Analyse prüfen")
        self.setMinimumSize(STATEMENT_DIALOG_MIN_WIDTH, STATEMENT_DIALOG_MIN_HEIGHT)

        layout = QVBoxLayout(self)

        header_group = QVBoxLayout()
        header_group.addWidget(QLabel("<b>Kopfdaten</b>"))

        form = QFormLayout()
        self.edit_bank = QLineEdit(statement.bank_name)
        self.edit_iban = QLineEdit(statement.iban)
        self.edit_owner = QLineEdit(statement.inhaber)
        self.edit_period_from = QLineEdit(statement.zeitraum_von)
        self.edit_period_to = QLineEdit(statement.zeitraum_bis)
        self.edit_balance_start = QLineEdit(f"{statement.anfangsbestand:.2f}")
        self.edit_balance_end = QLineEdit(f"{statement.endbestand:.2f}")

        form.addRow("Bank:", self.edit_bank)
        form.addRow("IBAN:", self.edit_iban)
        form.addRow("Inhaber:", self.edit_owner)
        form.addRow("Zeitraum von:", self.edit_period_from)
        form.addRow("Zeitraum bis:", self.edit_period_to)
        form.addRow("Anfangsbestand (€):", self.edit_balance_start)
        form.addRow("Endbestand (€):", self.edit_balance_end)
        header_group.addLayout(form)
        layout.addLayout(header_group)

        layout.addWidget(QLabel("<b>Buchungen</b>"))

        self.table = QTableWidget(len(statement.positionen), len(POSITION_COLUMNS))
        self.table.setHorizontalHeaderLabels(POSITION_COLUMNS)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)

        for row, pos in enumerate(statement.positionen):
            self.table.setItem(row, 0, QTableWidgetItem(pos.buchungsdatum))
            self.table.setItem(row, 1, QTableWidgetItem(pos.verwendungszweck))
            self.table.setItem(row, 2, QTableWidgetItem(pos.beguenstigter_auftraggeber))
            betrag_item = QTableWidgetItem(f"{pos.betrag:.2f}")
            betrag_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            if pos.betrag < 0:
                betrag_item.setForeground(Qt.GlobalColor.red)
            else:
                betrag_item.setForeground(Qt.GlobalColor.darkGreen)
            self.table.setItem(row, 3, betrag_item)
            self.table.setItem(row, 4, QTableWidgetItem(pos.category))
            self.table.setItem(row, 5, QTableWidgetItem(pos.sub_category))

        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        btn_discard = QPushButton("Verwerfen")
        btn_reset = QPushButton("Zurücksetzen")
        btn_ok = QPushButton("OK")

        btn_discard.clicked.connect(self.reject)
        btn_reset.clicked.connect(self._reset)
        btn_ok.clicked.connect(self.accept)

        btn_layout.addWidget(btn_discard)
        btn_layout.addWidget(btn_reset)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_ok)
        layout.addLayout(btn_layout)

    def _reset(self):
        s = self.original
        self.edit_bank.setText(s.bank_name)
        self.edit_iban.setText(s.iban)
        self.edit_owner.setText(s.inhaber)
        self.edit_period_from.setText(s.zeitraum_von)
        self.edit_period_to.setText(s.zeitraum_bis)
        self.edit_balance_start.setText(f"{s.anfangsbestand:.2f}")
        self.edit_balance_end.setText(f"{s.endbestand:.2f}")

        for row, pos in enumerate(s.positionen):
            self.table.item(row, 0).setText(pos.buchungsdatum)
            self.table.item(row, 1).setText(pos.verwendungszweck)
            self.table.item(row, 2).setText(pos.beguenstigter_auftraggeber)
            self.table.item(row, 3).setText(f"{pos.betrag:.2f}")
            self.table.item(row, 4).setText(pos.category)
            self.table.item(row, 5).setText(pos.sub_category)

    def get_statement(self) -> NormalizedBankStatement:
        positionen = []
        for row in range(self.table.rowCount()):
            col0 = self.table.item(row, 0)
            if col0 is None or not col0.text().strip():
                continue
            positionen.append(NormalizedBankPosition(
                buchungsdatum=col0.text().strip(),
                verwendungszweck=self.table.item(row, 1).text().strip(),
                beguenstigter_auftraggeber=self.table.item(row, 2).text().strip(),
                betrag=float(self.table.item(row, 3).text().strip().replace("€", "").strip() or "0"),
                category=self.table.item(row, 4).text().strip(),
                sub_category=self.table.item(row, 5).text().strip(),
            ))

        return NormalizedBankStatement(
            bank_name=self.edit_bank.text().strip(),
            iban=self.edit_iban.text().strip(),
            inhaber=self.edit_owner.text().strip(),
            zeitraum_von=self.edit_period_from.text().strip(),
            zeitraum_bis=self.edit_period_to.text().strip(),
            anfangsbestand=float(self.edit_balance_start.text().strip() or "0"),
            endbestand=float(self.edit_balance_end.text().strip() or "0"),
            positionen=positionen,
        )
