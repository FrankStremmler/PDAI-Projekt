'''Google Calendar API Integration'''
# Basismodul für Google API integration laden
#import os
import datetime
from zoneinfo import ZoneInfo

from providers.google_parts import google_base as google_base

# Google Calendar API benötigt diese Berechtigung, um auf Kalenderdaten zuzugreifen
SCOPES = google_base.GOOGLE_SCOPES


class GoogleCalendar:
    service = None

    def __init__(self):
        self.service = google_base.create_service()

    def create_service (self):
        '''
        Nutzt die create_service() Funktion aus google_base, um einen Dienst zu erstellen, um mit der Google API zu kommunizieren.
        '''
        return google_base.create_service('calendar')


    def get_all_calendar(self):
        '''
        Ruft alle Kalender ab, auf die der Benutzer Zugriff hat, und gibt deren Namen und IDs aus.
        :return: Gibt eine Liste der Kalender zurück, die der Benutzer hat, mit deren Namen und IDs.
        Wird später als list[CalEvents] zurückgegeben, um die Kalender-Objekte zu kapseln.
        CalEvents-Objekt enthält dann die Kalender-ID, den Namen und die nächsten Termine.
        Wrapper für ALLE Kalender, damit die Funktionalität für alle Kalender-APIs einheitlich bleibt,
        auch wenn die Implementierung der API-Aufrufe unterschiedlich ist.
        '''
        #service = self.create_service()
        calendar_list = self.service.calendarList().list().execute()
        return calendar_list


    def get_next_events(self, calendar_id='primary', max_results=3)->list:
        '''
        Ruft den nächsten Termin aus dem angegebenen Kalender ab und gibt dessen Zusammenfassung und Startzeit aus.
        :param calendar_id: Die ID des Kalenders, aus dem der Termin abgerufen werden soll (Standard ist 'primary' für den Hauptkalender).
        :param max_results: Die maximale Anzahl an Ergebnissen, die zurückgegeben werden sollen.
        :return: Gibt den nächsten Termin mit Zusammenfassung und Startzeit zurück.
        '''
        service = google_base.create_service('calendar')

        # Aktuelle Zeit im ISO-Format (UTC)
        # now = datetime.datetime.utcnow().isoformat() + 'Z'
        now = datetime.datetime.now(datetime.UTC).isoformat() #+ 'Z'

        # Nächsten 3 Termine abrufen
        # maxResults ist variabel, Standard ist 3, um mehr Termine abzurufen, wenn nötig
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=now,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events: list = events_result.get('items', [])

        if not events:
            events = []
            print('Keine anstehenden Termine gefunden.')
        else:
            for event in events:
                startzeit_utc = datetime.datetime.fromisoformat(event['start'].get('dateTime', event['start'].get('date')))
                # Umwandeln in lokale Zeit (z.B. MEZ)
                startzeit = startzeit_utc.astimezone(ZoneInfo('Europe/Berlin'))
        return events

if __name__ == '__main__':
    pass
