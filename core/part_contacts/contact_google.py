import os
from typing import List

from core.part_contacts.contact_model import Contact, ContactGroup, AccountContactData

from providers.google_parts.google_constants import GOOGLE_SCOPES, CONFIG_PATH

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = GOOGLE_SCOPES
SECRET_DIR = os.path.abspath(CONFIG_PATH)
TOKEN_PATH = os.path.join(SECRET_DIR, "token.json")
CREDENTIALS_PATH = os.path.join(SECRET_DIR, "credentials.json")


def get_google_credentials() -> Credentials:
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_PATH):
                raise FileNotFoundError(
                    f"Weder eine gültige '{TOKEN_PATH}' noch eine '{CREDENTIALS_PATH}' im Hauptverzeichnis gefunden!"
                )
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)

        os.makedirs(SECRET_DIR, exist_ok=True)
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())

    return creds


def fetch_contacts() -> AccountContactData:
    creds = get_google_credentials()
    service = build('people', 'v1', credentials=creds)

    results = service.people().connections().list(
        resourceName='people/me',
        pageSize=100,
        personFields='names,emailAddresses,phoneNumbers,addresses'
    ).execute()

    connections = results.get('connections', [])

    contacts = []

    for person in connections:
        resource_name = person.get('resourceName', '')
        names = person.get('names', [])
        emails = person.get('emailAddresses', [])
        phones = person.get('phoneNumbers', [])
        addresses = person.get('addresses', [])

        contact = Contact(
            id=resource_name,
            name=names[0]['displayName'] if names else 'Unbekannt',
            email=emails[0]['value'] if emails else None,
            phone=phones[0]['value'] if phones else None,
            address=addresses[0]['formattedValue'] if addresses else None
        )

        contacts.append(contact)

    account_data = AccountContactData(
        account_email='Unbekannt',  # TODO: Evtl. Account E-Mail aus Credentials ziehen
        contact_groups=[ContactGroup(group_id='default', group_name='Alle Kontakte', contacts=contacts)]
    )

    return account_data

# TODO: Funktionen zum Erstellen, Bearbeiten und Löschen von Kontakten implementieren analog zum Kalendermodul

