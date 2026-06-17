from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QApplication, QListWidgetItem

from pdai_gui.settings_dialog import SettingsDialog

from standards_and_constants.view_constants import (
    FONT_FAMILY, FONT_SIZE_TITLE, FONT_SIZE_BODY,
    FONT_SIZE_DATETIME_DISPLAY,
    COLOR_CALENDAR_SIDEBAR_BG, COLOR_CALENDAR_SIDEBAR_TEXT,
)
from standards_and_constants.config_manager import load_config


def apply_view_settings(parent=None):
    cfg = load_config().get("view", {})
    ff = cfg.get("font_family", FONT_FAMILY)
    font_cfg = cfg.get("font", {})
    color_cfg = cfg.get("color", {})

    body_size = font_cfg.get("body", FONT_SIZE_BODY)

    app = QApplication.instance()
    if app:
        app.setFont(QFont(ff, body_size))

    if parent:
        sidebar_style = (
            f"background-color: {color_cfg.get('sidebar_bg', COLOR_CALENDAR_SIDEBAR_BG)}; "
            f"color: {color_cfg.get('sidebar_text', COLOR_CALENDAR_SIDEBAR_TEXT)};"
        )
        parent.sidebar.setStyleSheet(sidebar_style)

        for child in parent.findChildren(object):
            meta = getattr(child, 'metaObject', None)
            if not meta:
                continue
            cls = meta().className()
            if "HomeWidget" in cls:
                for label in child.findChildren(object):
                    lm = getattr(label, 'metaObject', None)
                    if not lm:
                        continue
                    if "QLabel" in lm().className():
                        txt = getattr(label, 'text', lambda: "")()
                        ali = getattr(label, 'alignment', lambda: None)()
                        if txt == "Willkommen bei PDAI":
                            label.setStyleSheet(
                                f"font-size: {font_cfg.get('title', FONT_SIZE_TITLE)}px; "
                                f"font-weight: bold; font-family: '{ff}';"
                            )
                        elif ali == Qt.AlignCenter:
                            label.setStyleSheet(
                                f"font-size: {font_cfg.get('datetime', FONT_SIZE_DATETIME_DISPLAY)}px; "
                                f"font-weight: bold; font-family: '{ff}';"
                            )
                break


class MainController:
    ICONS = {
        "home": ":/assets/icons/home.svg",
        "calendar": ":/assets/icons/calendar.svg",
        "contacts": ":/assets/icons/contacts.svg",
        "cloud": ":/assets/icons/cloud.svg",
        "notes": ":/assets/icons/notes.svg",
        "household": ":/assets/icons/household.svg",
        "budget": ":/assets/icons/budget.svg",
        "settings": ":/assets/icons/settings.svg",
    }

    def __init__(self, model, view):
        self.model = model
        self.view = view
        self._settings_dialog = None
        self._populate()
        self.view.sidebar.currentRowChanged.connect(self._on_selection_changed)

    def _populate(self):
        self.view.add_collapse_item("Einklappen", QIcon(":/assets/icons/collapse.svg"))
        self.view.add_spacer(12)

        for entry in self.model.list():
            widget = entry.factory()
            icon_path = self.ICONS.get(entry.id)
            icon = QIcon(icon_path) if icon_path else None
            self.view.add_app(entry.name, widget, icon, entry_id=entry.id)

        self.view.add_spacer(8)
        self.view.add_settings_item("Einstellungen", QIcon(":/assets/icons/settings.svg"))
        self.view.add_exit_item("Beenden", QIcon(":/assets/icons/exit.svg"))

        apply_view_settings(self.view)

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

        if role == "settings":
            self._settings_dialog = SettingsDialog(self.view)
            self._settings_dialog.applied.connect(self._on_settings_applied)
            self._settings_dialog.exec()
            self._settings_dialog = None
            self.view.restore_last_app_selection()
            return

        self.view.set_current_index(index)

    def _on_settings_applied(self):
        apply_view_settings(self.view)
