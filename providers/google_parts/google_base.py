
# # Berechtigungen für die APIS - volle Berechtigung für Zugriff auf Google Calendar, Contacts und Drive API.
# # Unterfuntionen wie calender.readonly oder drive.file können später hinzugefügt werden, um die Berechtigungen zu begrenzen.

# # interne Bibliotheken
# # Datum/Zeit implementation
# import datetime
# # zoneinfo für Zeitzonen-Umwandlung (tzdata muss installiert sein)
# from zoneinfo import ZoneInfo

# import os
# # import json

#externe Bibliotheken
# from google.auth.transport.requests import Request
# from google.oauth2.credentials import Credentials
# from google_auth_oauthlib.flow import InstalledAppFlow
# from googleapiclient.discovery import build

# eigene Module importieren
import os as os
import standards_and_constants.google_constants as google_constants

GOOGLE_SCOPES = google_constants.GOOGLE_SCOPES
import os

# Baut den Pfad plattformübergreifend mit Vorwärts-Slashes (/)
# CREDENTIALS_FILE = os.path.join(google_constants.CONFIG_PATH, 'credentials.json').replace(os.sep, '/')
# TOKEN_FILE = os.path.join(google_constants.CONFIG_PATH, 'token.json').replace(os.sep, '/')
CREDENTIALS_FILE = os.path.join(google_constants.CONFIG_PATH, 'credentials.json')
TOKEN_FILE = os.path.join(google_constants.CONFIG_PATH, 'token.json')

# Standradfunktion für die Erstellung eines Dienstes, um mit der Google API zu kommunizieren.
def create_service(app_name='calendar'):
    '''
    Erstellt einen Dienst, um mit Google API's zu kommunizieren.
    Handhabt die Authentifizierung und Token-Verwaltung.
    Gibt ein Service-Objekt zurück, das für API-Aufrufe verwendet werden kann.
    '''
    creds = None
    # Token speichert die Benutzeranmeldung für den nächsten Lauf
    if os.path.exists(TOKEN_FILE):
        creds = google_constants.Credentials.from_authorized_user_file(TOKEN_FILE, GOOGLE_SCOPES)

    # Login, falls kein gültiger Token existiert, ruft die Login-Seite auf, um die Berechtigungen zu erteilen
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(google_constants.Request())
        else:
            flow = google_constants.InstalledAppFlow.from_client_secrets_file(
                client_secrets_file=CREDENTIALS_FILE,
                scopes=GOOGLE_SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    service = google_constants.build(app_name, 'v3', credentials=creds)
    return service

if __name__ == '__main__':
    pass
    # service = create_service()
    # print("Google Service erfolgreich erstellt:", service)
