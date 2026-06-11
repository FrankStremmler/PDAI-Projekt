from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox

from core.part_calendar.cal_gui import CalendarAppView, DynamicCalendarTableModel
from core.part_calendar.cal_main import CalendarController
from core.part_calendar.cal_calendar import get_today_events, get_upcoming_events

from core.part_contacts.contact_controller import ContactController
from core.part_contacts.contact_gui import DynamicContactTableModel
from core.part_contacts.contact_view import ContactAppView

from core.part_cloud.drive_gui import DriveCloudWidget, DriveItemsTableModel
from core.part_cloud.drive_controller import DriveController



from core.part_household_budget import HouseholdBudgetView, HouseholdBudgetController


class HomeWidget(QWidget):

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        title = QLabel("Willkommen bei PDAI")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        text = QLabel(
            "Dies ist die Startseite. Wähle links eine Sub-App aus, um die Funktionalität zu sehen."
        )
        text.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(text)

        boxes = QHBoxLayout()

        today_box = QGroupBox("Termine heute")
        today_box.setStyleSheet("QGroupBox { font-weight: bold; margin-top: 10px; }")
        today_layout = QVBoxLayout(today_box)

        upcoming_box = QGroupBox("Nächste Termine")
        upcoming_box.setStyleSheet("QGroupBox { font-weight: bold; margin-top: 10px; }")
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
        title = QLabel("Notizen")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        text = QLabel(
            "Hier können später Notizen erstellt und durchsucht werden."
        )
        text.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(text)


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







class BudgetWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        title = QLabel("Budgetverwaltung")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        text = QLabel(
            "Hier können später Budget-Analysen, Ausgaben und Haushaltstracker eingebunden werden."
        )
        text.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(text)


class HouseholdBookWidget(QWidget):

    def __init__(self):
        super().__init__()
        self.household_view = HouseholdBudgetView()
        self.household_controller = HouseholdBudgetController(self.household_view)

        layout = QVBoxLayout(self)
        layout.addWidget(self.household_view)

