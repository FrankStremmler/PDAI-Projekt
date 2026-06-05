'''
Interne Bibliothek für die Verwaltung von Google Kontakten.
Die Bibliothek verwendet die Google Contacts API v3, um auf die Google Kontakte des Benutzers zuzugreifen.
'''
# externe Bibliotheken
from providers.google_parts.google_base import create_service
from providers.google_parts import google_constants as google_constants

# volle Berechtigung für Zugriff auf Google Drive API
SCOPES = google_constants.GOOGLE_SCOPES



def get_all_contacts():
    service = create_service()

    results = service.people().connections().list(
        resourceName='people/me',
        pageSize=10,
        personFields='names,emailAddresses,phoneNumbers'
    ).execute()
    connections = results.get('connections', [])
    if not connections:
        print('No contacts found.')
    else:
        print('Contacts:')
        for person in connections:
            name = person.get('names', [{}])[0].get('displayName', 'N/A')
            email = person.get('emailAddresses', [{}])[0].get('value', 'N/A')
            phone = person.get('phoneNumbers', [{}])[0].get('value', 'N/A')
            print(f"Name: {name}, Email: {email}, Phone: {phone}")

if __name__ == '__main__':
    get_all_contacts()

