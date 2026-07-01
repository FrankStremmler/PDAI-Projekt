from PySide6.QtCore import Qt, QTimer, QDateTime
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox
from standards_and_constants.view_constants import (
    STYLE_TITLE_BOLD,
    STYLE_DATETIME_DISPLAY,
    STYLE_GROUPBOX,
    DATETIME_DISPLAY_FORMAT,
)

from core.part_calendar.cal_gui import CalendarAppView, DynamicCalendarTableModel
from core.part_calendar.cal_main import CalendarController
from core.part_calendar.cal_calendar import get_today_events, get_upcoming_events

from core.part_contacts.contact_controller import ContactController
from core.part_contacts.contact_gui import DynamicContactTableModel
from core.part_contacts.contact_view import ContactAppView

from core.part_cloud.drive_gui import DriveCloudWidget, DriveItemsTableModel
from core.part_cloud.drive_controller import DriveController



from core.part_household_budget import HouseholdBudgetView, HouseholdBudgetController
from core.part_notes.notes_gui import NotesListView
from core.part_notes.notes_controller import NotesController
from providers.google_parts import google_base


class HomeWidget(QWidget):

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        title = QLabel("Willkommen bei PDAI")
        title.setStyleSheet(STYLE_TITLE_BOLD)
        layout.addWidget(title)

        self.datetime_label = QLabel(QDateTime.currentDateTime().toString(DATETIME_DISPLAY_FORMAT))
        self.datetime_label.setStyleSheet(STYLE_DATETIME_DISPLAY)
        self.datetime_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.datetime_label)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_datetime)
        self.timer.start(1000)

        boxes = QHBoxLayout()

        today_box = QGroupBox("Termine heute")
        today_box.setStyleSheet(STYLE_GROUPBOX)
        today_layout = QVBoxLayout(today_box)

        upcoming_box = QGroupBox("Nächste Termine")
        upcoming_box.setStyleSheet(STYLE_GROUPBOX)
        upcoming_layout = QVBoxLayout(upcoming_box)

        try:
            today_events = get_today_events()
        except Exception as e:
            today_error_label = QLabel(
                f"Kalenderdaten für heute konnten nicht geladen werden: {e}"
            )
            today_error_label.setWordWrap(True)
            today_layout.addWidget(today_error_label)
        else:
            if today_events:
                for event in today_events:
                    event_label = QLabel(f"{event.start_time} - {event.title} ({event.location})")
                    event_label.setWordWrap(True)
                    today_layout.addWidget(event_label)
            else:
                none_label = QLabel("Keine Termine für heute.")
                none_label.setWordWrap(True)
                today_layout.addWidget(none_label)

        try:
            upcoming_events = get_upcoming_events(5)
        except Exception as e:
            upcoming_error_label = QLabel(
                f"Kommende Termine konnten nicht geladen werden: {e}"
            )
            upcoming_error_label.setWordWrap(True)
            upcoming_layout.addWidget(upcoming_error_label)
        else:
            if upcoming_events:
                for event in upcoming_events:
                    event_label = QLabel(f"{event.start_time} - {event.title} ({event.location})")
                    event_label.setWordWrap(True)
                    upcoming_layout.addWidget(event_label)
            else:
                none_label = QLabel("Keine kommenden Termine.")
                none_label.setWordWrap(True)
                upcoming_layout.addWidget(none_label)

        boxes.addWidget(today_box)
        boxes.addWidget(upcoming_box)
        layout.addLayout(boxes)

    def _update_datetime(self):
        self.datetime_label.setText(QDateTime.currentDateTime().toString(DATETIME_DISPLAY_FORMAT))


class CalendarWidget(QWidget):

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        self.calendar_view = CalendarAppView()
        self.qt_model = DynamicCalendarTableModel()
        self.calendar_controller = CalendarController(self.calendar_view, self.qt_model)

        layout.addWidget(self.calendar_view)


class ContactsWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        # MVC Wiring: View + Model + Controller
        self.view = ContactAppView()
        self.qt_model = DynamicContactTableModel()
        self.controller = ContactController(self.view, self.qt_model)

        layout.addWidget(self.view)



class NotesWidget(QWidget):

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        self.view = NotesListView()
        self.controller = NotesController(self.view)
        self.view.attach_controller(self.controller)

        layout.addWidget(self.view)

    def hideEvent(self, event):
        self.view.editor.try_save()
        super().hideEvent(event)


class CloudStorageWidget(QWidget):

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        self.view = DriveCloudWidget()
        self.qt_model = DriveItemsTableModel()
        self.controller = DriveController(self.view, self.qt_model)
        self.view.attach_controller(self.controller)
        self.view.set_qt_model(self.qt_model)

        layout.addWidget(self.view)




class DriveContactsWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        title = QLabel("(wird aktuell nicht verwendet)")
        layout.addWidget(title)







class HouseholdBookWidget(QWidget):

    def __init__(self):
        super().__init__()
        self.household_view = HouseholdBudgetView()
        self._was_visible = False

        drive_service = None
        try:
            drive_service = google_base.create_service("drive")
            print("[HouseholdBook] Google Drive-Service initialisiert")
        except Exception as e:
            print(f"[HouseholdBook] Kein Drive-Zugriff ({e}), verwende lokale DB")

        self.household_controller = HouseholdBudgetController(
            self.household_view, drive_service=drive_service
        )

        layout = QVBoxLayout(self)
        layout.addWidget(self.household_view)

    def showEvent(self, event):
        self._was_visible = True
        super().showEvent(event)

    def hideEvent(self, event):
        if self._was_visible and self.household_controller:
            print("[HouseholdBook] SubApp verlassen, lade zur Drive hoch...")
            self.household_controller.save_to_drive()
        super().hideEvent(event)

