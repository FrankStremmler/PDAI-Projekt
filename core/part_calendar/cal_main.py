import sys
from PySide6.QtWidgets import QApplication, QMessageBox, QListWidgetItem, QDialog
from core.part_calendar.cal_gui import CalendarAppView, DynamicCalendarTableModel, EventEditDialog, EventCreateDialog
from core.part_calendar.cal_calendar import fetch_calendar_data, CalendarContainer, AccountCalendarData, update_google_event, delete_google_event, create_google_event

class CalendarController:
    def __init__(self, view: CalendarAppView, qt_model: DynamicCalendarTableModel):
        self.view = view
        self.qt_model = qt_model
        self.account_data = None
        self.current_calendar_events = []
        self.current_calendar_id = None

        self.load_data_and_init_ui()

    def load_data_and_init_ui(self):
        try:
            self.account_data = fetch_calendar_data()
        except Exception as e:
            QMessageBox.critical(self.view, "Fehler beim Datenabruf", f"Es gab ein Problem mit der Google API:\n{str(e)}")
            self.account_data = AccountCalendarData(
                account_email="Fehler beim Laden",
                calendars=[],
            )
            return

        # 1. E-Mail in Sidebar eintragen
        self.view.account_label.setText(f"👤 {self.account_data.account_email}")

        # 2. Sidebar-Liste mit Kalendernamen befüllen
        for cal in self.account_data.calendars:
            item = QListWidgetItem(f"📅 {cal.calendar_name}")
            # Speichere das Pydantic-Objekt direkt im Listen-Eintrag
            item.setData(0x0100, cal)
            self.view.calendar_list_widget.addItem(item)

        # 3. Model an View binden
        self.view.set_qt_model(self.qt_model)

        # 4. Signale/Events verknüpfen
        self.view.calendar_list_widget.currentRowChanged.connect(self.on_sidebar_calendar_changed)
        self.view.btn_dashboard.clicked.connect(self.show_dashboard)
        self.view.table_view.clicked.connect(self.on_table_row_clicked)
        self.view.create_event_button.clicked.connect(self.on_create_event_clicked)
        self.view.create_event_button.setVisible(False)

        # 5. Dashboard-Kacheln generieren und initial anzeigen
        self.show_dashboard()

    def show_dashboard(self):
        """Schaltet das UI auf die reine Kalender-Übersicht (ohne Tabelle) um"""
        # Selektion in Sidebar aufheben, damit es optisch passt
        self.view.calendar_list_widget.setCurrentRow(-1)

        # create button auf der Dashboard-Ansicht ausblenden
        self.view.create_event_button.setVisible(False)

        # Kacheln rendern und diese Funktion als Klick-Callback übergeben
        self.view.render_dashboard_tiles(
            self.account_data.calendars,
            self.on_tile_clicked,
            self.on_create_for_calendar,
        )

        # StackedWidget auf Seite 0 (Dashboard) setzen
        self.view.content_stack.setCurrentIndex(0)

    def on_tile_clicked(self, index):
        """Wird aufgerufen, wenn der Nutzer auf eine Dashboard-Kachel klickt"""
        # Synchronisiere die Auswahl mit der Sidebar
        self.view.calendar_list_widget.setCurrentRow(index)

    def on_create_for_calendar(self, calendar_id: str):
        self._select_calendar_by_id(calendar_id)
        self.on_create_event_clicked()

    def on_create_event_clicked(self):
        if not self.current_calendar_id:
            QMessageBox.warning(self.view, "Kein Kalender ausgewählt", "Bitte wähle zuerst einen Kalender aus.")
            return

        dialog = EventCreateDialog(self.view)
        if dialog.exec() == QDialog.Accepted:
            new_event = dialog.get_new_event()
            if not new_event.start_time or not new_event.end_time:
                QMessageBox.warning(self.view, "Unvollständiger Termin", "Bitte gib Beginn und Ende des Termins an.")
                return

            try:
                created = create_google_event(self.current_calendar_id, new_event)
                new_event.id = created.get('id', '')
                self.current_calendar_events.append(new_event)
                self.qt_model.set_events(self.current_calendar_events)
                self.view.table_view.selectRow(len(self.current_calendar_events) - 1)
            except Exception as e:
                QMessageBox.warning(
                    self.view,
                    "Erstellen fehlgeschlagen",
                    f"Der Termin konnte nicht in Google erstellt werden:\n{e}"
                )

    def _select_calendar_by_id(self, calendar_id: str):
        for row in range(self.view.calendar_list_widget.count()):
            item = self.view.calendar_list_widget.item(row)
            cal: CalendarContainer = item.data(0x0100)
            if cal and cal.calendar_id == calendar_id:
                self.view.calendar_list_widget.setCurrentRow(row)
                return

    def on_sidebar_calendar_changed(self, index):
        """Wird aufgerufen, wenn in der Sidebar ein Kalender gewählt wird"""
        if index == -1:
            return  # Nichts tun, wenn die Auswahl aufgehoben wurde

        # Hole das Pydantic-Objekt aus dem ausgewählten Sidebar-Eintrag
        item = self.view.calendar_list_widget.item(index)
        selected_calendar: CalendarContainer = item.data(0x0100)

        if selected_calendar:
            # Titel über der Tabelle anpassen
            self.view.current_cal_title.setText(f"Termine für: {selected_calendar.calendar_name}")

            # Zugriff auf die aktuelle Kalenderliste und Kalender-ID speichern
            self.current_calendar_events = selected_calendar.events
            self.current_calendar_id = selected_calendar.calendar_id
            self.view.create_event_button.setVisible(True)

            # Daten ins Tabellenmodell laden
            self.qt_model.set_events(self.current_calendar_events)

            # Spaltenbreite automatisch an Text anpassen
            self.view.table_view.resizeColumnsToContents()

            # StackedWidget auf Seite 1 (Tabelle) umschalten
            self.content_stack_switch(1)

    def on_table_row_clicked(self, index):
        if not index.isValid() or index.row() < 0:
            return

        if index.row() >= len(self.current_calendar_events):
            return

        selected_event = self.current_calendar_events[index.row()]
        dialog = EventEditDialog(selected_event, self.view)
        if dialog.exec() == QDialog.Accepted:
            if getattr(dialog, 'delete_requested', False):
                if self.current_calendar_id:
                    try:
                        delete_google_event(self.current_calendar_id, selected_event.id)
                    except Exception as e:
                        QMessageBox.warning(
                            self.view,
                            "Löschen fehlgeschlagen",
                            f"Der Termin wurde lokal entfernt, aber nicht in Google gelöscht:\n{e}"
                        )
                self.current_calendar_events.pop(index.row())
                self.qt_model.set_events(self.current_calendar_events)
                return

            updated_event = dialog.get_updated_event()
            self.current_calendar_events[index.row()] = updated_event
            self.qt_model.set_events(self.current_calendar_events)
            self.view.table_view.selectRow(index.row())

            if self.current_calendar_id:
                try:
                    update_google_event(self.current_calendar_id, updated_event)
                except Exception as e:
                    QMessageBox.warning(
                        self.view,
                        "Speichern fehlgeschlagen",
                        f"Der Termin wurde lokal aktualisiert, aber nicht in Google gespeichert:\n{e}"
                    )

    def content_stack_switch(self, index: int):
        self.view.content_stack.setCurrentIndex(index)


def cal_main():
    app = QApplication(sys.argv)

    view = CalendarAppView()
    qt_model = DynamicCalendarTableModel()
    controller = CalendarController(view, qt_model)

    view.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    cal_main()
