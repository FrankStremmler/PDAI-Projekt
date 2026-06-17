from typing import List, Optional
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLabel, QLineEdit,
    QDialogButtonBox, QHBoxLayout, QPushButton
)
from standards_and_constants.view_constants import STYLE_DELETE_BUTTON, DIALOG_MIN_WIDTH
from core.part_contacts.contact_model import Contact



class DynamicContactTableModel(QAbstractTableModel):
    def __init__(self):
        super().__init__()
        self._all_contacts: List[Contact] = []
        self._current_contacts: List[Contact] = []
        self._headers = ["Name", "E-Mail", "Telefon", "Adresse"]
        self._filter_text: str = ""
        self._sort_key: str = "name"
        self._sort_ascending: bool = True


    def set_contacts(self, contacts: List[Contact]):
        self.beginResetModel()
        self._all_contacts = contacts
        self._apply_filter_and_sort()
        self.endResetModel()

    def set_filter_text(self, text: str):
        self._filter_text = text or ""
        self.beginResetModel()
        self._apply_filter_and_sort()
        self.endResetModel()

    def set_sort(self, key: str, ascending: bool = True):
        self._sort_key = key or "name"
        self._sort_ascending = ascending
        self.beginResetModel()
        self._apply_filter_and_sort()
        self.endResetModel()

    def _apply_filter_and_sort(self):
        filter_lower = (self._filter_text or "").strip().lower()

        if filter_lower:
            def matches(c: Contact) -> bool:
                fields = [
                    c.name or "",
                    c.email or "",
                    c.phone or "",
                    c.address or "",
                ]
                return any(filter_lower in (f or "").lower() for f in fields)

            filtered = [c for c in self._all_contacts if matches(c)]
        else:
            filtered = list(self._all_contacts)

        def sort_value(c: Contact):
            if self._sort_key == "name":
                return (c.name or "").lower()
            if self._sort_key == "email":
                return (c.email or "").lower()
            if self._sort_key == "phone":
                return (c.phone or "").lower()
            if self._sort_key == "address":
                return (c.address or "").lower()
            return (c.name or "").lower()

        filtered.sort(key=sort_value, reverse=not self._sort_ascending)
        self._current_contacts = filtered


    def rowCount(self, parent=QModelIndex()):
        return len(self._current_contacts)

    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None

        contact = self._current_contacts[index.row()]
        col = index.column()

        if col == 0: return contact.name
        if col == 1: return contact.email
        if col == 2: return contact.phone
        if col == 3: return contact.address
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self._headers[section]
        return None

    def get_contact_at(self, row: int) -> Contact:
        if row < 0 or row >= len(self._current_contacts):
            raise IndexError("Row out of range")
        return self._current_contacts[row]


class ContactEditDialog(QDialog):
    def __init__(self, contact: Contact, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Kontakt bearbeiten")
        self.setMinimumWidth(DIALOG_MIN_WIDTH)

        self._contact = contact
        layout = QFormLayout(self)

        self.id_label = QLabel(contact.id)
        self.name_edit = QLineEdit(contact.name)
        self.email_edit = QLineEdit(contact.email or "")
        self.phone_edit = QLineEdit(contact.phone or "")
        self.address_edit = QLineEdit(contact.address or "")

        layout.addRow("ID:", self.id_label)
        layout.addRow("Name:", self.name_edit)
        layout.addRow("E-Mail:", self.email_edit)
        layout.addRow("Telefon:", self.phone_edit)
        layout.addRow("Adresse:", self.address_edit)

        button_layout = QHBoxLayout()
        self.delete_button = QPushButton("Kontakt löschen")
        self.delete_button.setStyleSheet(STYLE_DELETE_BUTTON)
        self.delete_button.clicked.connect(self.on_delete_clicked)
        button_layout.addWidget(self.delete_button)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addRow(button_layout)
        layout.addRow(buttons)

        self.delete_requested = False

    def on_delete_clicked(self):
        self.delete_requested = True
        self.accept()

    def get_updated_contact(self) -> Contact:
        return Contact(
            id=self._contact.id,
            name=self.name_edit.text(),
            email=self.email_edit.text() or None,
            phone=self.phone_edit.text() or None,
            address=self.address_edit.text() or None
        )

class ContactCreateDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Neuen Kontakt erstellen")
        self.setMinimumWidth(DIALOG_MIN_WIDTH)

        layout = QFormLayout(self)

        self.name_edit = QLineEdit()
        self.email_edit = QLineEdit()
        self.phone_edit = QLineEdit()
        self.address_edit = QLineEdit()

        layout.addRow("Name:", self.name_edit)
        layout.addRow("E-Mail:", self.email_edit)
        layout.addRow("Telefon:", self.phone_edit)
        layout.addRow("Adresse:", self.address_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addRow(buttons)

    def get_new_contact(self) -> Contact:
        # ID wird später durch Google generiert, daher leer lassen
        return Contact(
            id="",
            name=self.name_edit.text(),
            email=self.email_edit.text() or None,
            phone=self.phone_edit.text() or None,
            address=self.address_edit.text() or None
        )

