from __future__ import annotations

import os

from typing import List

from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QHeaderView,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QMenu,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
    QFileDialog,
)

from .drive_model import DriveItem


class DriveTableView(QTableView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.drop_callback = None

    def dragEnterEvent(self, event):
        mime = event.mimeData()
        if self._has_local_file_urls(mime):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        mime = event.mimeData()
        if self._has_local_file_urls(mime):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        mime = event.mimeData()
        paths = [url.toLocalFile() for url in mime.urls() if url.isLocalFile()]
        if not paths and mime.hasText():
            text = mime.text().strip()
            if os.path.exists(text):
                paths.append(text)

        if paths and self.drop_callback:
            self.drop_callback(paths)
            event.acceptProposedAction()
        else:
            event.ignore()

    @staticmethod
    def _has_local_file_urls(mime):
        return mime.hasUrls() and any(url.isLocalFile() for url in mime.urls())


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
        self.upload_button = QPushButton("Hochladen")
        self.create_folder_button = QPushButton("Neu Ordner")
        toolbar.addWidget(self.back_button)
        toolbar.addWidget(self.refresh_button)
        toolbar.addWidget(self.upload_button)
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

        self.table_view = DriveTableView()
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
        self.table_view.drop_callback = self._upload_from_paths

        self.upload_button.clicked.connect(self._on_upload_requested)
        self.paste_shortcut = QShortcut(QKeySequence.StandardKey.Paste, self)
        self.paste_shortcut.activated.connect(self._on_paste)

        # Menübar Buttons verbinden
        self.up_one_button.clicked.connect(self._on_up_one)
        self.root_button.clicked.connect(self._on_root)

    def set_qt_model(self, model: QAbstractTableModel):
        self.table_view.setModel(model)

    def attach_controller(self, controller):
        self._controller = controller

    def _on_upload_requested(self):
        if not self._controller:
            return

        file_paths, _ = QFileDialog.getOpenFileNames(self, "Dateien hochladen")
        if file_paths:
            self._controller.upload_files(file_paths)

    def _on_paste(self):
        if not self._controller:
            return

        mime = QApplication.clipboard().mimeData()
        paths = []
        if mime.hasUrls():
            paths = [url.toLocalFile() for url in mime.urls() if url.isLocalFile()]
        elif mime.hasText():
            text = mime.text().strip()
            if os.path.exists(text):
                paths = [text]

        if paths:
            self._controller.upload_files(paths)

    def _upload_from_paths(self, paths: list[str]):
        if not self._controller or not paths:
            return
        self._controller.upload_files(paths)

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

    def _on_table_context_menu(self, position):
        if not self._controller:
            return

        index = self.table_view.indexAt(position)
        if not index.isValid():
            return

        model = self.table_view.model()
        items = getattr(model, "_items", None)
        if not items or index.row() < 0 or index.row() >= len(items):
            return

        drive_item: DriveItem = items[index.row()]
        menu = QMenu(self)
        download_action = menu.addAction("Download")
        if drive_item.is_folder:
            download_action.setEnabled(False)

        action = menu.exec(self.table_view.viewport().mapToGlobal(position))
        if action == download_action:
            self._controller.download_item(drive_item)

    def _on_up_one(self):
        # vereinfacht: zurück auf Root (ohne Breadcrumbs/History)
        if self._controller:
            self._controller.go_back()

    def _on_root(self):
        if self._controller:
            self._controller.current_folder_id = "root"
            self._controller.refresh()

