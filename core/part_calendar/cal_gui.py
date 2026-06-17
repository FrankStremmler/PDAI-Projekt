from typing import List
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, QDateTime
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QTableView, QVBoxLayout, QHBoxLayout,
    QWidget, QLabel, QPushButton, QListWidget, QStackedWidget, QFrame,
    QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QMessageBox, QDateTimeEdit
)
from standards_and_constants.view_constants import (

    STYLE_SECTION_BOLD,
    STYLE_SUBTITLE_BOLD,
    STYLE_DELETE_BUTTON,
    DIALOG_MIN_WIDTH,
    CALENDAR_SIDEBAR_WIDTH,
    CALENDAR_WINDOW_WIDTH,
    CALENDAR_WINDOW_HEIGHT,
    CALENDAR_SIDEBAR_STYLE,
    CALENDAR_ACCOUNT_LABEL_STYLE,
    CALENDAR_NAV_BUTTON_STYLE,
    CALENDAR_SECTION_LABEL_STYLE,
    CALENDAR_LIST_STYLE,
    CALENDAR_CREATE_EVENT_BUTTON_STYLE,
    CALENDAR_TILE_BUTTON_STYLE,
    CALENDAR_NEW_EVENT_BUTTON_STYLE,
    CALENDAR_DATETIME_FORMAT,
    COLOR_CALENDAR_TILE_BG,
)
from core.part_calendar.cal_calendar import CalendarEvent, CalendarContainer

class DynamicCalendarTableModel(QAbstractTableModel):
    def __init__(self):
        super().__init__()
        self._current_events: List[CalendarEvent] = []
        self._headers = ["Termin-Titel", "Beginn", "Ende", "Veranstaltungsort"]

    def set_events(self, events: List[CalendarEvent]):
        self.beginResetModel()
        self._current_events = events
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return len(self._current_events)

    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None

        event = self._current_events[index.row()]
        col = index.column()

        if col == 0: return event.title
        if col == 1: return event.start_time
        if col == 2: return event.end_time
        if col == 3: return event.location
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self._headers[section]
        return None


class EventEditDialog(QDialog):
    def __init__(self, event: CalendarEvent, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Termin bearbeiten")
        self.setMinimumWidth(DIALOG_MIN_WIDTH)

        self._event = event
        layout = QFormLayout(self)

        self.id_label = QLabel(event.id)
        self.title_edit = QLineEdit(event.title)
        self.start_edit = QDateTimeEdit(self._parse_datetime(event.start_time))
        self.end_edit = QDateTimeEdit(self._parse_datetime(event.end_time))
        self.location_edit = QLineEdit(event.location)

        self.start_edit.setDisplayFormat(CALENDAR_DATETIME_FORMAT)
        self.start_edit.setCalendarPopup(True)
        self.end_edit.setDisplayFormat(CALENDAR_DATETIME_FORMAT)
        self.end_edit.setCalendarPopup(True)

        layout.addRow("ID:", self.id_label)
        layout.addRow("Titel:", self.title_edit)
        layout.addRow("Beginn:", self.start_edit)
        layout.addRow("Ende:", self.end_edit)
        layout.addRow("Ort:", self.location_edit)

        button_layout = QHBoxLayout()
        self.delete_button = QPushButton("Termin löschen")
        self.delete_button.setStyleSheet(STYLE_DELETE_BUTTON)
        self.delete_button.clicked.connect(self.on_delete_clicked)
        button_layout.addWidget(self.delete_button)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        button_layout.addWidget(buttons)

        layout.addRow(button_layout)

        self.delete_requested = False

    def on_delete_clicked(self):
        answer = QMessageBox.question(
            self,
            "Termin löschen",
            "Soll dieser Termin wirklich gelöscht werden?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer == QMessageBox.Yes:
            self.delete_requested = True
            self.accept()

    def get_updated_event(self) -> CalendarEvent:
        self._event.title = self.title_edit.text().strip() or self._event.title
        self._event.start_time = self._format_datetime(self.start_edit)
        self._event.end_time = self._format_datetime(self.end_edit)
        self._event.location = self.location_edit.text().strip() or self._event.location
        return self._event

    def _parse_datetime(self, value: str) -> QDateTime:
        if not value:
            return QDateTime.currentDateTime()
        dt = QDateTime.fromString(value, CALENDAR_DATETIME_FORMAT)
        if dt.isValid():
            return dt
        dt = QDateTime.fromString(value, Qt.ISODate)
        if dt.isValid():
            return dt
        try:
            from datetime import datetime
            parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
            return QDateTime(parsed.year, parsed.month, parsed.day, parsed.hour, parsed.minute)
        except Exception:
            return QDateTime.currentDateTime()

    def _format_datetime(self, widget: QDateTimeEdit) -> str:
        return widget.dateTime().toString(CALENDAR_DATETIME_FORMAT)


class EventCreateDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Neuen Termin erstellen")
        self.setMinimumWidth(DIALOG_MIN_WIDTH)

        layout = QFormLayout(self)
        self.title_edit = QLineEdit()
        self.start_edit = QDateTimeEdit(QDateTime.currentDateTime())
        self.end_edit = QDateTimeEdit(QDateTime.currentDateTime().addSecs(3600))
        self.location_edit = QLineEdit()

        self.start_edit.setDisplayFormat(CALENDAR_DATETIME_FORMAT)
        self.start_edit.setCalendarPopup(True)
        self.end_edit.setDisplayFormat(CALENDAR_DATETIME_FORMAT)
        self.end_edit.setCalendarPopup(True)

        layout.addRow("Titel:", self.title_edit)
        layout.addRow("Beginn:", self.start_edit)
        layout.addRow("Ende:", self.end_edit)
        layout.addRow("Ort:", self.location_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_new_event(self) -> CalendarEvent:
        return CalendarEvent(
            id="",
            title=self.title_edit.text().strip() or "Neuer Termin",
            start_time=self.start_edit.dateTime().toString(CALENDAR_DATETIME_FORMAT),
            end_time=self.end_edit.dateTime().toString(CALENDAR_DATETIME_FORMAT),
            location=self.location_edit.text().strip() or "Keine Angabe",
        )


class CalendarAppView(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Google Calendar - Dashboard & Sidebar")
        self.resize(CALENDAR_WINDOW_WIDTH, CALENDAR_WINDOW_HEIGHT)

        # Hauptlayout für das eingebettete Kalender-Widget
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- LINKS: SIDEBAR ---
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(CALENDAR_SIDEBAR_WIDTH)
        self.sidebar.setStyleSheet(CALENDAR_SIDEBAR_STYLE)
        self.sidebar.setFont(QFont("", 9))
        sidebar_layout = QVBoxLayout(self.sidebar)

        self.account_label = QLabel("Konto: -")
        self.account_label.setStyleSheet(CALENDAR_ACCOUNT_LABEL_STYLE)
        sidebar_layout.addWidget(self.account_label)

        # Navigation-Buttons
        self.btn_dashboard = QPushButton("📊 Übersicht (Dashboard)")
        self.btn_dashboard.setStyleSheet(CALENDAR_NAV_BUTTON_STYLE)
        sidebar_layout.addWidget(self.btn_dashboard)

        # Trennlinie & Kalender-Liste in Sidebar
        cal_section_label = QLabel("Meine Kalender:")
        cal_section_label.setStyleSheet(CALENDAR_SECTION_LABEL_STYLE)
        sidebar_layout.addWidget(cal_section_label)

        self.calendar_list_widget = QListWidget()
        self.calendar_list_widget.setStyleSheet(CALENDAR_LIST_STYLE)
        sidebar_layout.addWidget(self.calendar_list_widget)

        main_layout.addWidget(self.sidebar)

        # --- RECHTS: DYNAMISCHER INHALT (Stacked Widget) ---
        self.content_stack = QStackedWidget()
        main_layout.addWidget(self.content_stack)

        # Seite 1: Das Dashboard (Wird angezeigt, wenn kein Kalender aktiv ist)
        self.dashboard_page = QWidget()
        self.dashboard_layout = QVBoxLayout(self.dashboard_page)
        self.dashboard_title = QLabel("Wähle einen Kalender oder nutze die Übersicht")
        self.dashboard_title.setStyleSheet(STYLE_SECTION_BOLD + " padding: 20px;")
        self.dashboard_layout.addWidget(self.dashboard_title)

        # Container für die dynamischen Kalender-Kacheln
        self.tiles_container = QWidget()
        self.tiles_container.setStyleSheet(CALENDAR_TILE_BUTTON_STYLE % COLOR_CALENDAR_TILE_BG)
        self.tiles_layout = QVBoxLayout(self.tiles_container)
        self.dashboard_layout.addWidget(self.tiles_container)
        self.dashboard_layout.addStretch() # Schiebt alles nach oben

        self.content_stack.addWidget(self.dashboard_page)

        # Seite 2: Die Termin-Tabelle
        self.table_page = QWidget()
        table_layout = QVBoxLayout(self.table_page)

        self.current_cal_title = QLabel("Termine")
        self.current_cal_title.setStyleSheet(STYLE_SUBTITLE_BOLD + " padding: 10px;")
        table_layout.addWidget(self.current_cal_title)

        self.create_event_button = QPushButton("Neuen Termin erstellen")
        self.create_event_button.setStyleSheet(CALENDAR_CREATE_EVENT_BUTTON_STYLE)
        table_layout.addWidget(self.create_event_button)

        self.table_view = QTableView()
        self.table_view.setAlternatingRowColors(True)
        table_layout.addWidget(self.table_view)

        self.content_stack.addWidget(self.table_page)

    def set_qt_model(self, qt_model):
        self.table_view.setModel(qt_model)
        self.table_view.setSelectionBehavior(QTableView.SelectRows)
        self.table_view.setSelectionMode(QTableView.SingleSelection)
        self.table_view.horizontalHeader().setStretchLastSection(True)

    def render_dashboard_tiles(self, calendars: List[CalendarContainer], on_tile_click_callback, on_create_callback=None):
        """Baut die Kacheln auf dem Dashboard dynamisch auf"""
        # Altes Layout leeren
        while self.tiles_layout.count():
            child = self.tiles_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for index, cal in enumerate(calendars):
            tile_widget = QWidget()
            tile_layout = QHBoxLayout(tile_widget)
            tile_layout.setContentsMargins(5, 5, 5, 5)
            tile_layout.setSpacing(10)

            tile_button = QPushButton(f"📅  {cal.calendar_name} ({len(cal.events)} Termine)")
            tile_button.setStyleSheet(CALENDAR_TILE_BUTTON_STYLE % cal.color_code)
            tile_button.clicked.connect(lambda checked=False, i=index: on_tile_click_callback(i))
            tile_layout.addWidget(tile_button, 1)

            if on_create_callback is not None:
                create_button = QPushButton("Neuen Termin")
                create_button.setStyleSheet(CALENDAR_NEW_EVENT_BUTTON_STYLE)
                create_button.clicked.connect(lambda checked=False, cal_id=cal.calendar_id: on_create_callback(cal_id))
                tile_layout.addWidget(create_button)

            self.tiles_layout.addWidget(tile_widget)
