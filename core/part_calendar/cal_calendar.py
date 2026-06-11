import os
import re
import datetime
from zoneinfo import ZoneInfo
from typing import List, Optional
from pydantic import BaseModel, Field

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from providers.google_parts.google_base import create_service
from providers.google_parts.google_constants import GOOGLE_SCOPES, CONFIG_PATH

SCOPES = GOOGLE_SCOPES
# Pfade sauber definieren (Nutzt den Unterordner .secret)
SECRET_DIR = os.path.abspath(CONFIG_PATH)
TOKEN_PATH = os.path.join(SECRET_DIR, "token.json")
CREDENTIALS_PATH = os.path.join(SECRET_DIR, "credentials.json")  # Falls du dich neu einloggen musst

class CalendarEvent(BaseModel):
    id: str = Field(description="Eindeutige ID des Termins")
    title: str = Field(description="Titel des Termins")
    start_time: str = Field(description="Startzeit im ISO-Format")
    end_time: str = Field(description="Endzeit im ISO-Format")
    location: Optional[str] = Field(description="Ort des Termins", default="Keine Angabe")

class CalendarContainer(BaseModel):
    calendar_id: str = Field(description="Eindeutige ID des Kalenders")
    calendar_name: str = Field(description="Anzeigename des Kalenders")
    color_code: Optional[str] = Field(description="Farbe für die UI", default="#ffffff")
    events: List[CalendarEvent] = Field(description="Termine in diesem Kalender", default=[])

class AccountCalendarData(BaseModel):
    account_email: str = Field(description="E-Mail-Adresse des Accounts")
    calendars: List[CalendarContainer] = Field(description="Alle Kalender des Accounts")


def get_google_credentials() -> Credentials:
    """Nutzt die token.json aus dem .secret Ordner"""
    creds = None

    # 1. Prüfen, ob die token.json im .secret Ordner existiert
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    # 2. Wenn kein gültiges Token existiert, erneuern oder neu einloggen
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

        # Sicherstellen, dass der .secret Ordner existiert, bevor wir schreiben
        os.makedirs(SECRET_DIR, exist_ok=True)

        # Token im .secret Ordner speichern
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())

    return creds


def _normalize_datetime_string(value: str) -> str:
    if not value:
        return value

    # Fix malformed strings like "2026-06-12 07:45T00:00:00"
    if re.match(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}T', value):
        return value.split('T')[0]

    # Fix date/time values with space instead of T
    if ' ' in value and 'T' not in value and re.match(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}(:\d{2})?$', value):
        return value.replace(' ', 'T')

    return value


def _parse_google_datetime(value: str) -> str:
    if not value:
        return ''

    value = _normalize_datetime_string(value)

    # All-day events liefern nur ein Datum ohne Uhrzeit.
    if 'T' not in value:
        return value

    try:
        if value.endswith('Z'):
            dt = datetime.datetime.fromisoformat(value.replace('Z', '+00:00'))
        else:
            dt = datetime.datetime.fromisoformat(value)
        local_dt = dt.astimezone(ZoneInfo('Europe/Berlin'))
        return local_dt.strftime('%Y-%m-%d %H:%M')
    except Exception:
        return value.replace('T', ' ').replace('Z', '')[:16]


def _get_today_date_range() -> tuple[str, str]:
    local_tz = ZoneInfo('Europe/Berlin')
    today = datetime.datetime.now(local_tz).date()
    start = datetime.datetime(today.year, today.month, today.day, 0, 0, 0, tzinfo=local_tz)
    end = start + datetime.timedelta(days=1)
    return start.isoformat(), end.isoformat()


def _get_all_calendars(service):
    calendars = []
    page_token = None
    while True:
        response = service.calendarList().list(pageToken=page_token).execute()
        calendars.extend(response.get('items', []))
        page_token = response.get('nextPageToken')
        if not page_token:
            break
    return calendars


def get_today_events() -> List[CalendarEvent]:
    creds = get_google_credentials()
    service = build('calendar', 'v3', credentials=creds)

    time_min, time_max = _get_today_date_range()
    calendars = _get_all_calendars(service)

    mapped_events: List[CalendarEvent] = []
    for cal in calendars:
        cal_id = cal.get('id')
        if not cal_id:
            continue

        try:
            events_obj = service.events().list(
                calendarId=cal_id,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            raw_events = events_obj.get('items', [])
        except Exception:
            raw_events = []

        for ev in raw_events:
            start = ev.get('start', {}).get('dateTime') or ev.get('start', {}).get('date', '')
            end = ev.get('end', {}).get('dateTime') or ev.get('end', {}).get('date', '')
            start_clean = _parse_google_datetime(start)
            end_clean = _parse_google_datetime(end)
            mapped_events.append(CalendarEvent(
                id=ev.get('id', ''),
                title=ev.get('summary', 'Kein Titel'),
                start_time=start_clean,
                end_time=end_clean,
                location=ev.get('location', 'Keine Angabe')
            ))

    return sorted(mapped_events, key=lambda ev: _parse_event_datetime(ev.start_time))


def _parse_event_datetime(value: str) -> datetime.datetime:
    if not value:
        return datetime.datetime.max.replace(tzinfo=ZoneInfo('Europe/Berlin'))

    value = _normalize_datetime_string(value)

    if value.endswith('Z'):
        dt = datetime.datetime.fromisoformat(value.replace('Z', '+00:00'))
    elif 'T' in value:
        dt = datetime.datetime.fromisoformat(value)
    else:
        dt = datetime.datetime.fromisoformat(value + 'T00:00:00')

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo('Europe/Berlin'))
    else:
        dt = dt.astimezone(ZoneInfo('Europe/Berlin'))

    return dt


def get_upcoming_events(limit: int = 5) -> List[CalendarEvent]:
    creds = get_google_credentials()
    service = build('calendar', 'v3', credentials=creds)

    now = datetime.datetime.now(ZoneInfo('Europe/Berlin')).isoformat()
    calendars = _get_all_calendars(service)

    mapped_events: List[CalendarEvent] = []
    for cal in calendars:
        cal_id = cal.get('id')
        if not cal_id:
            continue

        try:
            events_obj = service.events().list(
                calendarId=cal_id,
                timeMin=now,
                singleEvents=True,
                orderBy='startTime',
                maxResults=50
            ).execute()
            raw_events = events_obj.get('items', [])
        except Exception:
            raw_events = []

        for ev in raw_events:
            start = ev.get('start', {}).get('dateTime') or ev.get('start', {}).get('date', '')
            end = ev.get('end', {}).get('dateTime') or ev.get('end', {}).get('date', '')
            start_clean = _parse_google_datetime(start)
            end_clean = _parse_google_datetime(end)
            mapped_events.append(CalendarEvent(
                id=ev.get('id', ''),
                title=ev.get('summary', 'Kein Titel'),
                start_time=start_clean,
                end_time=end_clean,
                location=ev.get('location', 'Keine Angabe')
            ))

    mapped_events.sort(key=lambda ev: _parse_event_datetime(ev.start_time))
    return mapped_events[:limit]


def _format_google_event_time(value: str) -> dict:
    if not value:
        return {}

    if 'T' not in value and ' ' not in value:
        return {
            'date': value
        }

    try:
        if value.endswith('Z'):
            dt = datetime.datetime.fromisoformat(value.replace('Z', '+00:00'))
        else:
            dt = datetime.datetime.fromisoformat(value)
    except ValueError:
        try:
            dt = datetime.datetime.strptime(value, '%Y-%m-%d %H:%M')
            dt = dt.replace(tzinfo=ZoneInfo('Europe/Berlin'))
        except Exception:
            return {
                'dateTime': value,
                'timeZone': 'Europe/Berlin'
            }

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo('Europe/Berlin'))
    else:
        dt = dt.astimezone(ZoneInfo('Europe/Berlin'))

    return {
        'dateTime': dt.isoformat(),
        'timeZone': 'Europe/Berlin'
    }


def create_google_event(calendar_id: str, event: CalendarEvent) -> dict:
    service = create_service('calendar')
    body = {
        'summary': event.title,
        'location': event.location or '',
        'start': _format_google_event_time(event.start_time),
        'end': _format_google_event_time(event.end_time),
    }
    return service.events().insert(
        calendarId=calendar_id,
        body=body
    ).execute()


def update_google_event(calendar_id: str, event: CalendarEvent) -> dict:
    service = create_service('calendar')
    body = {
        'summary': event.title,
        'location': event.location or '',
        'start': _format_google_event_time(event.start_time),
        'end': _format_google_event_time(event.end_time),
    }
    return service.events().update(
        calendarId=calendar_id,
        eventId=event.id,
        body=body
    ).execute()


def delete_google_event(calendar_id: str, event_id: str) -> dict:
    service = create_service('calendar')
    return service.events().delete(
        calendarId=calendar_id,
        eventId=event_id
    ).execute()


def fetch_calendar_data() -> AccountCalendarData:
    creds = get_google_credentials()
    service = build('calendar', 'v3', credentials=creds)

    primary_cal = service.calendars().get(calendarId='primary').execute()
    account_email = primary_cal.get('summary', 'Google Account')

    calendar_list_obj = service.calendarList().list().execute()
    items = calendar_list_obj.get('items', [])

    mapped_calendars = []
    now = datetime.datetime.utcnow().isoformat() + 'Z'

    for cal in items:
        cal_id = cal['id']
        cal_name = cal.get('summary', 'Unbenannter Kalender')
        color = cal.get('backgroundColor', '#ffffff')

        try:
            events_obj = service.events().list(
                calendarId=cal_id,
                timeMin=now,
                maxResults=50,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            raw_events = events_obj.get('items', [])
        except Exception:
            raw_events = []

        mapped_events = []
        for ev in raw_events:
            start = ev.get('start', {}).get('dateTime') or ev.get('start', {}).get('date', '')
            end = ev.get('end', {}).get('dateTime') or ev.get('end', {}).get('date', '')

            start_clean = _parse_google_datetime(start)
            end_clean = _parse_google_datetime(end)

            event_item = CalendarEvent(
                id=ev.get('id', ''),
                title=ev.get('summary', 'Kein Titel'),
                start_time=start_clean,
                end_time=end_clean,
                location=ev.get('location', 'Keine Angabe')
            )
            mapped_events.append(event_item)

        container = CalendarContainer(
            calendar_id=cal_id,
            calendar_name=cal_name,
            color_code=color,
            events=mapped_events
        )
        mapped_calendars.append(container)

    return AccountCalendarData(account_email=account_email, calendars=mapped_calendars)
