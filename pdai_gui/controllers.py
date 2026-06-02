from PySide6.QtCore import Qt
from PySide6.QtWidgets import QListWidgetItem


class MainController:
    def __init__(self, model, view):
        self.model = model
        self.view = view
        self._populate()
        self.view.sidebar.currentRowChanged.connect(self._on_selection_changed)

    def _populate(self):
        for entry in self.model.list():
            widget = entry.factory()
            # try to use some sensible default icons via QStyle
            icon_id = None
            if entry.id == "home":
                from PySide6.QtWidgets import QStyle

                icon_id = QStyle.SP_DesktopIcon
            elif entry.id == "budget":
                from PySide6.QtWidgets import QStyle

                icon_id = QStyle.SP_DriveHDIcon
            self.view.add_app(entry.name, widget, icon_id)

    def _on_selection_changed(self, index: int):
        self.view.set_current_index(index)
