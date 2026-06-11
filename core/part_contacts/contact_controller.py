from PySide6.QtWidgets import QMessageBox, QListWidgetItem, QDialog
from core.part_contacts.contact_gui import DynamicContactTableModel, ContactEditDialog, ContactCreateDialog
from core.part_contacts.contact_google import fetch_contacts
from core.part_contacts.contact_model import AccountContactData, ContactGroup, Contact

class ContactController:
    def __init__(self, view, qt_model: DynamicContactTableModel):

        self.view = view
        self.qt_model = qt_model
        self.account_data: AccountContactData = None
        self.current_contacts = []

        self.load_data_and_init_ui()

    def load_data_and_init_ui(self):
        try:
            self.account_data = fetch_contacts()
        except Exception as e:
            QMessageBox.critical(self.view, "Fehler beim Datenabruf", f"Problem mit der Google API:\n{str(e)}")
            self.account_data = AccountContactData(account_email="Fehler beim Laden", contact_groups=[])
            return

        self.view.account_label.setText(f"👤 {self.account_data.account_email}")

        for group in self.account_data.contact_groups:
            item = QListWidgetItem(f"👥 {group.group_name}")
            item.setData(0x0100, group)
            self.view.group_list_widget.addItem(item)

        self.view.set_qt_model(self.qt_model)

        # UI-Events verbinden (z.B. auf Auswahl reagieren)
        self.view.group_list_widget.currentRowChanged.connect(self.on_sidebar_group_changed)
        self.view.create_contact_button.clicked.connect(self.on_create_contact_clicked)
        self.view.table_view.clicked.connect(self.on_table_row_clicked)

        # Suche & Sortierung
        if hasattr(self.view, "search_input"):
            self.view.search_input.textChanged.connect(self.on_search_text_changed)
        if hasattr(self.view, "sort_button"):
            self.view.sort_button.clicked.connect(self.on_sort_clicked)


    def on_sidebar_group_changed(self, index):
        if index == -1:
            return

        item = self.view.group_list_widget.item(index)
        selected_group: ContactGroup = item.data(0x0100)

        if selected_group:
            self.current_contacts = selected_group.contacts
            self.qt_model.set_contacts(self.current_contacts)

            self.view.current_group_title.setText(f"Kontakte für: {selected_group.group_name}")
            self.view.create_contact_button.setVisible(True)

            self.view.content_stack.setCurrentIndex(1)

    def on_search_text_changed(self, text: str):
        # Filter apply auf aktuelle Kontakte (laufendes Set via Model)
        if self.qt_model:
            self.qt_model.set_filter_text(text)

    def on_sort_clicked(self):
        # Toggle A-Z / Z-A
        next_ascending = True
        if hasattr(self.qt_model, "_sort_ascending"):
            next_ascending = not getattr(self.qt_model, "_sort_ascending", True)

        if self.qt_model:
            # Sort only by name for now
            self.qt_model.set_sort("name", ascending=next_ascending)

        # Button text anpassen
        if hasattr(self.view, "sort_button"):
            self.view.sort_button.setText("A-Z" if next_ascending else "Z-A")

    def on_table_row_clicked(self, index):

        if not index.isValid() or index.row() < 0:
            return

        try:
            selected_contact = self.qt_model.get_contact_at(index.row())
        except Exception:
            return

        dialog = ContactEditDialog(selected_contact, self.view)
        if dialog.exec() == QDialog.Accepted:
            if getattr(dialog, 'delete_requested', False):
                # TODO: Kontakt löschen (Google API)
                self.current_contacts = [c for c in self.current_contacts if c.id != selected_contact.id]
                self.qt_model.set_contacts(self.current_contacts)
                return

            updated_contact = dialog.get_updated_contact()
            for idx, contact in enumerate(self.current_contacts):
                if contact.id == selected_contact.id:
                    self.current_contacts[idx] = updated_contact
                    break
            self.qt_model.set_contacts(self.current_contacts)

            # TODO: Google Kontakte aktualisieren

    def on_create_contact_clicked(self):
        dialog = ContactCreateDialog(self.view)
        if dialog.exec() == QDialog.Accepted:
            new_contact = dialog.get_new_contact()
            # TODO: Kontakt in Google anlegen und ID zurückbekommen
            self.current_contacts.append(new_contact)
            self.qt_model.set_contacts(self.current_contacts)
            self.view.table_view.selectRow(len(self.current_contacts) - 1)

