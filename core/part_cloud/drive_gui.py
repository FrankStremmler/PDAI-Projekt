from __future__ import annotations

from typing import List

from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from .drive_model import DriveItem


class DriveItemsTableModel(QAbstractTableModel):
    def __init__(self):
        super().__init__()
        self._items: List[DriveItem] = []
        self._headers = ["Name", "Typ"]

    def set_items(self, items: List[DriveItem]):
        self.beginResetModel()
        self._items = items or []
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return len(self._items)

    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None

        it = self._items[index.row()]
        col = index.column()
        if col == 0:
            return it.name
        if col == 1:
            return "Ordner" if it.is_folder else "Datei"
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self._headers[section]
        return None


class DriveCloudWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Google Drive - Cloud Storage")

        root_layout = QVBoxLayout(self)

        toolbar = QHBoxLayout()
        self.back_button = QPushButton("Zurück")
        self.refresh_button = QPushButton("Aktualisieren")
        self.create_folder_button = QPushButton("Neu Ordner")
        toolbar.addWidget(self.back_button)
        toolbar.addWidget(self.refresh_button)
        toolbar.addStretch(1)
        toolbar.addWidget(self.create_folder_button)
        root_layout.addLayout(toolbar)

        # wird im Controller befüllt
        self.current_folder_label = QLabel("Ordner: root")
        root_layout.addWidget(self.current_folder_label)

        # Menübar über der Tabelle (Navigation)
        nav_layout = QHBoxLayout()
        self.up_one_button = QPushButton("⬆️ Eine Ebene nach oben")
        self.root_button = QPushButton("🏠 Root")
        nav_layout.addWidget(self.up_one_button)
        nav_layout.addWidget(self.root_button)
        nav_layout.addStretch(1)
        root_layout.addLayout(nav_layout)

        # Layout: optional navigation left + table right
        main = QHBoxLayout()
        left_nav = QVBoxLayout()
        left_nav.addWidget(QLabel("Navigation"))

        self.items_list_widget = QListWidget()
        self.items_list_widget.setVisible(False)
        left_nav.addWidget(self.items_list_widget, 1)

        main.addLayout(left_nav, 1)

        self.table_view = QTableView()
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table_view.setSortingEnabled(False)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        main.addWidget(self.table_view, 3)

        root_layout.addLayout(main, 1)

        self._controller = None

        self.table_view.doubleClicked.connect(self._on_table_double_clicked)
        self.table_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(self._on_table_context_menu)

        # Menübar Buttons verbinden
        self.up_one_button.clicked.connect(self._on_up_one)
        self.root_button.clicked.connect(self._on_root)

    def set_qt_model(self, model: QAbstractTableModel):
        self.table_view.setModel(model)

    def attach_controller(self, controller):
        self._controller = controller

    def prompt_folder_name(self) -> str:
        text, ok = QInputDialog.getText(self, "Neuer Ordner", "Ordnername:")
        if ok and text.strip():
            return text.strip()
        return "Neuer Ordner"

    def _on_table_double_clicked(self, model_index: QModelIndex):
        if not self._controller:
            return

        try:
            row = model_index.row()
            model = self.table_view.model()
            items = getattr(model, "_items", None)
            if not items or row < 0 or row >= len(items):
                return

            drive_item: DriveItem = items[row]
            if drive_item.is_folder:
                self._controller.current_folder_id = drive_item.id
                self._controller.refresh()
        except Exception as e:
            QMessageBox.warning(self, "Fehler", f"Konnte Ordner nicht öffnen:\n{e}")

    def _on_up_one(self):
        # vereinfacht: zurück auf Root (ohne Breadcrumbs/History)
        if self._controller:
            self._controller.go_back()

    def _on_root(self):
        if self._controller:
            self._controller.current_folder_id = "root"
            self._controller.refresh()

