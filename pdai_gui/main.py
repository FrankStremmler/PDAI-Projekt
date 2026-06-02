import os
import sys
from PySide6.QtWidgets import QApplication

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from pdai_gui.controllers import MainController
from pdai_gui.models import AppModel
from pdai_gui.subapps import (
    BudgetWidget,
    CalendarWidget,
    CloudStorageWidget,
    ContactsWidget,
    HomeWidget,
    HouseholdBookWidget,
    NotesWidget,
)
from pdai_gui.views import MainWindow

import pdai_gui.resources_rc  # load Qt resource icons


def create_application():
    app = QApplication(sys.argv)
    model = AppModel()
    model.register("home", "Startseite", HomeWidget)
    model.register("calendar", "Kalender", CalendarWidget)
    model.register("contacts", "Kontakte", ContactsWidget)
    model.register("cloud", "Cloud-Storage", CloudStorageWidget)
    model.register("notes", "Notizen", NotesWidget)
    model.register("household", "Haushaltsbuch", HouseholdBookWidget)
    model.register("budget", "Budgetverwaltung", BudgetWidget)

    view = MainWindow()
    controller = MainController(model, view)
    view.set_current_index(2)
    return app, view, controller


def run_app():
    app, view, _ = create_application()
    view.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(run_app())
