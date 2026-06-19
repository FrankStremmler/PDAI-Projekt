from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget, QMenu,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon

from .hb_config_model import ConfigManager
from standards_and_constants.hb_prompts_constants import PROVIDER_GEMINI, PROVIDER_OPENAI, MODEL_OPENAI, MODEL_GEMINI, RECEIPT_COLUMNS, STATEMENT_COLUMNS


MODEL_NAMES = {
    PROVIDER_GEMINI: MODEL_GEMINI,
    PROVIDER_OPENAI: MODEL_OPENAI,
}


class HouseholdBudgetView(QWidget):
    receipt_delete_requested = Signal(int)
    statement_delete_requested = Signal(int)

    def __init__(self):
        super().__init__()
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(10, 10, 10, 10)
        root_layout.setSpacing(10)

        # Top Bar
        top_bar = QHBoxLayout()

        self.btn_analyze = QPushButton(" Analysieren mit ...")
        self.update_analyze_button()
        self.btn_analyze.setCursor(Qt.CursorShape.PointingHandCursor)

        self.btn_analyze_statement = QPushButton(" Kontoauszug analysieren")
        self.btn_analyze_statement.setCursor(Qt.CursorShape.PointingHandCursor)

        self.btn_switch_provider = QPushButton(" KI wechseln")
        self.btn_switch_provider.setCursor(Qt.CursorShape.PointingHandCursor)

        top_bar.addWidget(self.btn_analyze)
        top_bar.addWidget(self.btn_analyze_statement)
        top_bar.addWidget(self.btn_switch_provider)
        top_bar.addStretch()

        root_layout.addLayout(top_bar)

        # Tabs
        self.tabs = QTabWidget()

        # Tab: Belege
        self.receipt_tab = QWidget()
        receipt_layout = QVBoxLayout(self.receipt_tab)
        receipt_layout.setContentsMargins(0, 8, 0, 0)
        self.receipt_table = QTableWidget(0, len(RECEIPT_COLUMNS))
        self.receipt_table.setHorizontalHeaderLabels(RECEIPT_COLUMNS)
        self.receipt_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.receipt_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.receipt_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.receipt_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.receipt_table.customContextMenuRequested.connect(self._show_receipt_context_menu)
        receipt_layout.addWidget(self.receipt_table)

        # Tab: Kontoauszüge
        self.statement_tab = QWidget()
        statement_layout = QVBoxLayout(self.statement_tab)
        statement_layout.setContentsMargins(0, 8, 0, 0)
        self.statement_table = QTableWidget(0, len(STATEMENT_COLUMNS))
        self.statement_table.setHorizontalHeaderLabels(STATEMENT_COLUMNS)
        self.statement_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.statement_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.statement_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.statement_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.statement_table.customContextMenuRequested.connect(self._show_statement_context_menu)
        statement_layout.addWidget(self.statement_table)

        self.tabs.addTab(self.receipt_tab, "Belege")
        self.tabs.addTab(self.statement_tab, "Kontoauszüge")

        root_layout.addWidget(self.tabs, 1)

    def update_analyze_button(self):
        provider = ConfigManager().config.ai_provider.lower()
        model = MODEL_NAMES.get(provider, provider)
        self.btn_analyze.setText(f" Analysieren mit {model}")

    def set_loading_state(self, is_loading: bool):
        if is_loading:
            self.btn_analyze.setText("Analysiere mit KI...")
            self.btn_analyze.setEnabled(False)
            self.btn_analyze_statement.setText("Analysiere Kontoauszug...")
            self.btn_analyze_statement.setEnabled(False)
            self.btn_switch_provider.setEnabled(False)
        else:
            self.update_analyze_button()
            self.btn_analyze.setEnabled(True)
            self.btn_analyze_statement.setText(" Kontoauszug analysieren")
            self.btn_analyze_statement.setEnabled(True)
            self.btn_switch_provider.setEnabled(True)

    def update_table_data(self, receipts_list):
        self.receipt_table.setRowCount(0)
        for row_idx, row_data in enumerate(receipts_list):
            self.receipt_table.insertRow(row_idx)
            for col_idx, value in enumerate(row_data):
                if col_idx == 3:
                    item_text = f"{value:.2f} €"
                else:
                    item_text = str(value)
                item = QTableWidgetItem(item_text)
                if col_idx in (0, 2, 4):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                elif col_idx == 3:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                if col_idx == 4:
                    if value == "booked":
                        item.setForeground(Qt.GlobalColor.green)
                    elif value == "pending":
                        item.setForeground(Qt.GlobalColor.yellow)
                    elif value == "suspicious":
                        item.setForeground(Qt.GlobalColor.red)
                self.receipt_table.setItem(row_idx, col_idx, item)

    def update_statement_table(self, statements_list):
        self.statement_table.setRowCount(0)
        for row_idx, row_data in enumerate(statements_list):
            self.statement_table.insertRow(row_idx)
            for col_idx, value in enumerate(row_data):
                if col_idx == 4:
                    item_text = f"{value:.2f} €"
                else:
                    item_text = str(value)
                item = QTableWidgetItem(item_text)
                if col_idx in (0, 3):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                elif col_idx == 4:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.statement_table.setItem(row_idx, col_idx, item)

    def _show_receipt_context_menu(self, pos):
        row = self.receipt_table.rowAt(pos.y())
        if row < 0:
            return
        receipt_id = int(self.receipt_table.item(row, 0).text())
        menu = QMenu(self)
        delete_action = menu.addAction("Löschen")
        action = menu.exec(self.receipt_table.viewport().mapToGlobal(pos))
        if action == delete_action:
            self.receipt_delete_requested.emit(receipt_id)

    def _show_statement_context_menu(self, pos):
        row = self.statement_table.rowAt(pos.y())
        if row < 0:
            return
        statement_id = int(self.statement_table.item(row, 0).text())
        menu = QMenu(self)
        delete_action = menu.addAction("Löschen")
        action = menu.exec(self.statement_table.viewport().mapToGlobal(pos))
        if action == delete_action:
            self.statement_delete_requested.emit(statement_id)
