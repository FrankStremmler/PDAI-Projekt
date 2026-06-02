from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QListWidgetItem


class MainController:
    ICONS = {
        "home": ":/icons/home.svg",
        "calendar": ":/icons/calendar.svg",
        "contacts": ":/icons/contacts.svg",
        "cloud": ":/icons/cloud.svg",
        "notes": ":/icons/notes.svg",
        "household": ":/icons/household.svg",
        "budget": ":/icons/budget.svg",
    }

    def __init__(self, model, view):
        self.model = model
        self.view = view
        self._populate()
        self.view.sidebar.currentRowChanged.connect(self._on_selection_changed)

    def _populate(self):
        self.view.add_collapse_item("Einklappen", QIcon(":/icons/collapse.svg"))
        self.view.add_spacer(24)

        for entry in self.model.list():
            widget = entry.factory()
            icon_path = self.ICONS.get(entry.id)
            icon = QIcon(icon_path) if icon_path else None
            self.view.add_app(entry.name, widget, icon, entry_id=entry.id)

        self.view.add_spacer(16)
        self.view.add_exit_item("Beenden", QIcon(":/icons/exit.svg"))

    def _on_selection_changed(self, index: int):
        item = self.view.sidebar.item(index)
        if item is None:
            return

        role = item.data(Qt.UserRole)
        if role == "exit":
            self.view.close()
            return

        if role == "collapse":
            self.view.toggle_sidebar()
            self.view.restore_last_app_selection()
            return

        self.view.set_current_index(index)
