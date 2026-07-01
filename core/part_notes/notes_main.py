import sys
from PySide6.QtWidgets import QApplication

from .notes_controller import NotesController
from .notes_gui import NotesListView


def notes_main():
    app = QApplication(sys.argv)

    view = NotesListView()
    controller = NotesController(view)

    view.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    notes_main()
