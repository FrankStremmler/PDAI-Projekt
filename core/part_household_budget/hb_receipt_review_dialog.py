from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QLineEdit, QCheckBox, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from standards_and_constants.view_constants import RECEIPT_DIALOG_MIN_WIDTH, RECEIPT_DIALOG_MIN_HEIGHT
from .hb_base import NormalizedReceipt, NormalizedItem

ITEM_COLUMNS = ["Name", "Menge", "Einzelpreis", "Gesamtpreis", "Warengruppe", "Unterkategorie"]


class ReceiptReviewDialog(QDialog):
    def __init__(self, receipt: NormalizedReceipt, parent=None):
        super().__init__(parent)
        self.original = receipt
        self.setWindowTitle("Beleg-Analyse prüfen")
        self.setMinimumSize(RECEIPT_DIALOG_MIN_WIDTH, RECEIPT_DIALOG_MIN_HEIGHT)

        layout = QVBoxLayout(self)

        header_group = QVBoxLayout()
        header_group.addWidget(QLabel("<b>Kopfdaten</b>"))

        form = QFormLayout()
        self.edit_merchant = QLineEdit(receipt.merchant)
        self.edit_date = QLineEdit(receipt.date_time)
        self.edit_total = QLineEdit(f"{receipt.total_sum:.2f}")
        self.chk_cash = QCheckBox("Barzahlung")
        self.chk_cash.setChecked(receipt.payment_method)

        form.addRow("Händler:", self.edit_merchant)
        form.addRow("Datum/Uhrzeit:", self.edit_date)
        form.addRow("Gesamtsumme (€):", self.edit_total)
        form.addRow("Zahlungsart:", self.chk_cash)
        header_group.addLayout(form)
        layout.addLayout(header_group)

        layout.addWidget(QLabel("<b>Artikel</b>"))

        self.table = QTableWidget(len(receipt.items), len(ITEM_COLUMNS))
        self.table.setHorizontalHeaderLabels(ITEM_COLUMNS)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)

        for row, item in enumerate(receipt.items):
            self.table.setItem(row, 0, QTableWidgetItem(item.name))
            self.table.setItem(row, 1, QTableWidgetItem(str(item.amount)))
            self.table.setItem(row, 2, QTableWidgetItem(f"{item.unit_price:.2f}"))
            self.table.setItem(row, 3, QTableWidgetItem(f"{item.price:.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem(item.category))
            self.table.setItem(row, 5, QTableWidgetItem(item.sub_category))

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
        self.edit_merchant.setText(self.original.merchant)
        self.edit_date.setText(self.original.date_time)
        self.edit_total.setText(f"{self.original.total_sum:.2f}")
        self.chk_cash.setChecked(self.original.payment_method)

        for row, item in enumerate(self.original.items):
            self.table.item(row, 0).setText(item.name)
            self.table.item(row, 1).setText(str(item.amount))
            self.table.item(row, 2).setText(f"{item.unit_price:.2f}")
            self.table.item(row, 3).setText(f"{item.price:.2f}")
            self.table.item(row, 4).setText(item.category)
            self.table.item(row, 5).setText(item.sub_category)

    def get_receipt(self) -> NormalizedReceipt:
        items = []
        for row in range(self.table.rowCount()):
            col0 = self.table.item(row, 0)
            if col0 is None or not col0.text().strip():
                continue
            items.append(NormalizedItem(
                name=col0.text().strip(),
                amount=float(self.table.item(row, 1).text().strip() or "1"),
                unit_price=float(self.table.item(row, 2).text().strip() or "0"),
                price=float(self.table.item(row, 3).text().strip() or "0"),
                category=self.table.item(row, 4).text().strip(),
                sub_category=self.table.item(row, 5).text().strip(),
            ))

        return NormalizedReceipt(
            merchant=self.edit_merchant.text().strip(),
            date_time=self.edit_date.text().strip(),
            total_sum=float(self.edit_total.text().strip() or "0"),
            payment_method=self.chk_cash.isChecked(),
            items=items,
        )
