import os
import tempfile

##############
# Pfade
##############
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_NAME = "household_budget.db"
DB_PATH = os.path.join(ROOT_DIR, DB_NAME)

INPUT_DIR = os.path.join(ROOT_DIR, "file_input")
RECEIPTS_FOLDER = os.path.join(INPUT_DIR, "receipts")
STATEMENTS_FOLDER = os.path.join(INPUT_DIR, "bank_statements")
LOCAL_TEMP_DIR = tempfile.gettempdir()
TEMP_DB_PATH = os.path.join(LOCAL_TEMP_DIR, DB_NAME)

DRIVE_FOLDER_NAME = "Household_Budget"

##############
# for views
##############
RECEIPT_COLUMNS = ["ID", "Händler", "Datum", "Gesamtsumme", "Status"]
STATEMENT_COLUMNS = ["ID", "Bank", "IBAN", "Zeitraum", "Endbestand"]

##############
# Dateitypen
##############
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}
MIME_PDF = "application/pdf"
MIME_JPEG = "image/jpeg"
MIME_PNG = "image/png"

SUPPORTED_EXTENSIONS = {
    "pdf": MIME_PDF,
    "jpg": MIME_JPEG,
    "jpeg": MIME_JPEG,
    "png": MIME_PNG,
}

##############
# KI-Provider
##############
PROVIDER_GEMINI = "gemini"
MODEL_GEMINI = "gemini-3.5-flash"
PROVIDER_OPENAI = "openai"
MODEL_OPENAI = "gpt-4.1-mini"

##############
# Status
##############
STATUS_PENDING = "pending"
STATUS_BOOKED = "booked"
STATUS_SUSPICIOUS = "suspicious"
STATUS_VALUES = [STATUS_PENDING, STATUS_BOOKED, STATUS_SUSPICIOUS]
STATUS_SYNC_SUCCESS = "SUCCESS"
STATUS_SYNC_ERROR = "ERROR"

##############
# Zahlungsmethoden
##############
PAYMENT_CASH = True
PAYMENT_CARD = False

##############
# Prompts
##############
PROMPT_RECEIPT = """
Analysiere den Kassenzettel und extrahiere das Geschäft (merchant), das Datum mit Uhrzeit (date_time), die Gesamtsumme (total_sum), die Zahlungsmethode (payment_method: true = Barzahlung, false = Kartenzahlung) und alle Posten (items) strikt gemäß dem vorgegebenen JSON-Schema.

Befolge dabei penibel diese Regeln:
1. Erfasse Pfandzeilen (Leergut/Flaschenpfand) als normale Posten, ordne ihnen die Kategorie 'Pfand' zu und achte exakt auf das Vorzeichen beim Preis: Rückgaben/Auszahlungen müssen NEGATIV sein.
2. Die äußerst rechte Spalte stellt die Mehrwertsteuerart dar (1 bzw. 2). Diese Spalte muss NICHT erfasst werden.
3. Bei einem Einkauf mit mehreren Artikeln steht die Stückzahl und der Stückpreis in der Zeile ÜBER dem Artikel.
4. Bei einem Einkauf mit Gewichtsangabe steht das Gewicht (Menge) und der kg-Preis (Stückpreis) in der Zeile ÜBER dem Artikel.
5. Jeder Posten benötigt eine Warengruppe (category) und eine passende Unterkategorie (sub_category). Beispiel: category "Lebensmittel", sub_category "Tiefkühlkost" oder category "Getränke", sub_category "Wasser".
6. Halte dich strikt an die vorgegebenen Getränke- und Tabak-Unterkategorien.

Gib AUSSCHLIESSLICH das pure JSON-Objekt zurück. Keine Erklärungen, kein Markdown.
"""

PROMPT_BANK_STATEMENT = """
Du bist ein präzises System zur Analyse von Bankauszügen für ein Haushaltsbuch.
Analysiere das Dokument des Bankauszugs und extrahiere ALLE allgemeinen Kopfdaten sowie sämtliche einzelnen Umsatzbuchungen strikt gemäß dem vorgegebenen JSON-Schema.

JSON-Struktur (Kopfdaten):
- bank_name: Name der Bank
- iban: IBAN des Kontos
- inhaber: Kontoinhaber
- zeitraum_von: Beginn des Auszugszeitraums (YYYY-MM-DD)
- zeitraum_bis: Ende des Auszugszeitraums (YYYY-MM-DD)
- anfangsbestand: Anfangsbestand/Kontostand zu Beginn
- endbestand: Endbestand/Kontostand am Ende
- positionen: Liste der einzelnen Buchungen

Jede Buchung (position) enthält:
- buchungsdatum: Buchungsdatum (YYYY-MM-DD)
- verwendungszweck: Verwendungszweck (ungekürzt)
- beguenstigter_auftraggeber: Begünstigter oder Auftraggeber
- betrag: Betrag (negativ = Ausgabe, positiv = Einnahme)
- category: Warengruppe, z.B. Lebensmittel, Gehalt, Miete
- sub_category: Unterkategorie, z.B. Tiefkühlkost, Monatsgehalt

Regeln:
1. Verändere keine Vorzeichen (Ausgaben zwingend negativ, Geldeingänge zwingend positiv).
2. Alle Datumsfelder innerhalb der Buchungen müssen strikt im Format YYYY-MM-DD ausgegeben werden.
3. Übernimm den Verwendungszweck ungekürzt.

Gib AUSSCHLIESSLICH das pure JSON-Objekt zurück. Keine Erklärungen, kein Markdown.
"""
