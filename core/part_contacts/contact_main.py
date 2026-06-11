import sys
from PySide6.QtWidgets import QApplication
from core.part_contacts.contact_controller import ContactController
from core.part_contacts.contact_gui import DynamicContactTableModel, ContactEditDialog, ContactCreateDialog
from core.part_contacts.contact_gui import DynamicContactTableModel
from core.part_contacts.contact_view import ContactAppView


def contact_main():
    app = QApplication(sys.argv)

    view = ContactAppView()
    qt_model = DynamicContactTableModel()
    controller = ContactController(view, qt_model)

    view.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    contact_main()

