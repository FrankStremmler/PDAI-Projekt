from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

from core.part_calendar.cal_gui import CalendarAppView, DynamicCalendarTableModel
from core.part_calendar.cal_main import CalendarController
from core.part_calendar.cal_calendar import get_today_events

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

        today_title = QLabel("Aktuelle Termine heute")
        today_title.setStyleSheet("font-size: 16px; font-weight: bold; margin-top: 12px;")
        layout.addWidget(today_title)

        try:
            events = get_today_events()
            if events:
                for event in events:
                    event_label = QLabel(
                        f"{event.start_time} - {event.title} ({event.location})"
                    )
                    event_label.setWordWrap(True)
                    layout.addWidget(event_label)
            else:
                none_label = QLabel("Keine Termine für heute.")
                none_label.setWordWrap(True)
                layout.addWidget(none_label)
        except Exception:
            error_label = QLabel(
                "Kalenderdaten sind aktuell nicht verfügbar. Bitte prüfe deine Google-Verbindung."
            )
            error_label.setWordWrap(True)
            layout.addWidget(error_label)


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

