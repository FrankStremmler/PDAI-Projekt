'''
Google API Konstanten , Funktionen und imports, die von mehreren Modulen verwendet werden.
'''
# Berechtigungen für die APIS - volle Berechtigung für Zugriff auf Google Calendar, Contacts und Drive API.
# Unterfuntionen wie calender.readonly oder drive.file können später hinzugefügt werden, um die Berechtigungen zu begrenzen.

import os

import google.auth.exceptions
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


GOOGLE_SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/contacts',
    'https://www.googleapis.com/auth/drive'
]

CONFIG_PATH = '.secrets'
