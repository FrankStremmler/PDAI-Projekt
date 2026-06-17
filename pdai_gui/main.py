import os
import sys
from PySide6.QtWidgets import QApplication

import pdai_gui.resources_rc

from pdai_gui.models import AppModel
from pdai_gui.views import MainWindow
from pdai_gui.controllers import MainController
from pdai_gui.subapps import (
    HomeWidget, CalendarWidget, ContactsWidget,
    CloudStorageWidget, NotesWidget, HouseholdBookWidget, BudgetWidget,
)
from standards_and_constants.hb_prompts_constants import TEMP_DB_PATH


def run_app() -> int:
    app = QApplication(sys.argv)

    def _cleanup():
        if os.path.exists(TEMP_DB_PATH):
            try:
                os.remove(TEMP_DB_PATH)
            except PermissionError:
                print("[Cleanup] Temp-DB wird noch verwendet, überspringe Löschung")

    app.aboutToQuit.connect(_cleanup)

    model = AppModel()
    model.register("home", "Startseite", HomeWidget)
    model.register("calendar", "Kalender", CalendarWidget)
    model.register("contacts", "Kontakte", ContactsWidget)
    model.register("cloud", "Cloud", CloudStorageWidget)
    model.register("notes", "Notizen", NotesWidget)
    model.register("household", "Haushaltsbuch", HouseholdBookWidget)
    model.register("budget", "Budget", BudgetWidget)

    view = MainWindow()
    controller = MainController(model, view)
    view.show()

    return app.exec()
