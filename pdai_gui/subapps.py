from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel


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


class CalendarWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        title = QLabel("Kalender")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        text = QLabel(
            "Hier wird später der Kalender angezeigt. Dies ist ein Dummy-Widget für die Kalender-App."
        )
        text.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(text)


class ContactsWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        title = QLabel("Kontakte")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        text = QLabel(
            "Hier werden später Kontakte und Adressinformationen verwaltet."
        )
        text.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(text)


class CloudStorageWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        title = QLabel("Cloud-Storage")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        text = QLabel(
            "Hier werden später Cloud-Speicher und Synchronisation geöffnet."
        )
        text.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(text)


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


class HouseholdBookWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        title = QLabel("Haushaltsbuch")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        text = QLabel(
            "Dies ist ein Dummy für das Haushaltsbuch mit Ausgaben und Budgetverwaltung."
        )
        text.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(text)
