import os
import tempfile
from typing import Optional
from pydantic import BaseModel, Field

##############################
# Constants for household budget module
##############################
DB_NAME = "household_budget.db"

# Temp-Path for later use of the Cloud-Wrapper (using OS-Standard-Temp-folder)
LOCAL_TEMP_DIR = tempfile.gettempdir()
TEMP_DB_PATH = os.path.join(LOCAL_TEMP_DIR, DB_NAME)

##############################
# Constants for Input-Files, AI-Provider ...
##############################
INPUT_DIR = "file_input"
ALLOWED_EXTENSIONS = {'.pdf', '.png', '.jpg', '.jpeg'}

# NEU: OpenAI Modell-Konstante
OPENAI_MODEL = "gpt-4.1-mini"  # Beispiel: GPT-4.1 Mini, anpassbar je nach Verfügbarkeit und Kosten

# ==========================================
# TEXT-PROMPTS FÜR DIE KI
# ==========================================

PROMPT_RECEIPT = """
Analysiere den Kassenzettel und extrahiere das Geschäft (merchant), das Datum mit Uhrzeit (date_time), die Gesamtsumme (total_sum), die Zahlungsart (sales_type) und alle Posten (items) strikt gemäß dem vorgegebenen JSON-Schema.

Befolge dabei penibel diese Regeln:
1. Erfasse Pfandzeilen (Leergut/Flaschenpfand) als normale Posten, ordne ihnen die Kategorie 'Pfand' zu und achte exakt auf das Vorzeichen beim Preis: Rückgaben/Auszahlungen müssen NEGATIV sein.
2. Die äußerst rechte Spalte stellt die Mehrwertsteuerart dar (1 bzw. 2). Diese Spalte muss NICHT erfasst werden.
3. Bei einem Einkauf mit mehreren Artikeln steht die Stückzahl und der Stückpreis in der Zeile ÜBER dem Artikel.
4. Bei einem Einkauf mit Gewichtsangabe steht das Gewicht (Menge) und der kg-Preis (Stückpreis) in der Zeile ÜBER dem Artikel.
5. Halte dich strikt an die vorgegebenen Getränke- und Tabak-Unterkategorien.

Gib AUSSCHLIESSLICH das pure JSON-Objekt zurück. Keine Erklärungen, kein Markdown.
"""

PROMPT_BANK_STATEMENT = """
Du bist ein präzises System zur Analyse von Bankauszügen für ein Haushaltsbuch.
Analysiere das Dokument des Bankauszugs und extrahiere ALLE allgemeinen Kopfdaten sowie sämtliche einzelnen Umsatzbuchungen strikt gemäß dem vorgegebenen JSON-Schema.

Regeln:
1. Verändere keine Vorzeichen (Ausgaben zwingend negativ, Geldeingänge zwingend positiv).
2. Alle Datumsfelder innerhalb der Buchungen müssen strikt im Format YYYY-MM-DD ausgegeben werden.
3. Übernimm den Verwendungszweck ungekürzt in das Feld 'raw_description'.

Gib AUSSCHLIESSLICH das pure JSON-Objekt zurück. Keine Erklärungen, kein Markdown.
"""

# ##############################
# # Prompts for household budget module
# ##############################
# ITEM_DESCRIPTION ="Beschreibung des Artikels auf dem Beleg (z.B. Milch, Cola oder auch 'Pfand / Leergut') Bei mehreren Artikeln steht die Stückzahl in der Zeile über dem Artikel, ebenso der Stückpreis."
# ITEM_AMMOUNT = "Stückzahl oder Menge. Bei mehreren Artikeln steht die Stückzahl in der Zeile über dem Artikel, ebenso der Stückpreis. Bei Artikeln mit Gewicht steht der kg-Preis und das Gewicht in der Zeile über dem Artikel. Das Gewicht ist dann die Stückzahl, der kg-Preis entspricht dem Stückpreis."
# ITEM_UNIT_PRICE = "Stückpreis in Euro. Bei Artikeln mit Gewicht steht der kg-Preis und das Gewicht in der Zeile über dem Artikel. Das Gewicht ist dann die Stückzahl, der kg-Preis entspricht dem Stückpreis."
# ITEM_PRICE = "Preis des Postens in Euro. WICHTIG: Wenn es sich um eine Pfandrückgabe/Guthaben handelt, trage den Wert als NEGATIVEN Betrag ein (z.B. -0.25). Die Anzahl und der Stückprei stehen bei mehreren Artikeln in der Zeile über dem Artikel. Bei Artikeln mit Gewicht steht der kg-Preis und das Gewicht in der Zeile über dem Artikel. Das Gewicht ist dann die Stückzahl, der kg-Preis entspricht dem Stückpreis."
# ITEM_CATEGORY = "Kategorie des Artikels. Nutze 'Pfand' für alle Pfand- und Leergutzeilen. Ansonsten klassische Kategorien wie Lebensmittel, Tabakwaren, Hygiene etc."
# RECEIPT_DATE_TIME = "Datum und Uhrzeit des Belegs im Format DD.MM.YYYY HH:MM. Falls keine Uhrzeit vorhanden, nur DD.MM.YYYY"
# RECEIPT_MERCHANT = "Name des Geschäfts oder Geschäftsname, z.B. Aldi, Lidl, Rewe" # die Variable title gegen merchant tauschen
# RECEIPT_TOTAL_SUM = "Gesamtsumme des Belegs in Euro. Optional, da sie aus den Posten berechnet werden kann."
# MAIN_PROMPT = "Analysiere den Kassenzettel. Extrahiere das Geschäft (title), das Datum mit Uhrzeit (date_time), die GesamtSumme (total_sum)und alle Posten. Erfasse Pfandzeilen (Leergut/Flaschenpfand) als normale Posten, ordne ihnen die Kategorie 'Pfand' zu und achte penibel auf das Vorzeichen beim Preis: Rückgaben/Auszahlungen müssen NEGATIV sein. Die äußerst rechte Spalte stellt die Mehrwertsteuerart dar, 1 bzw. 2. Diese Spalte muss nicht erfasst werde. Bei einem Einkauf mit mehreren Artikeln steht die Stückzahl in der Zeile über dem Artikel, ebenso der Stückpreis. Bei einem Einkauf mit Gewichtsangabe steht das Gewicht und der kg-Preis in der Zeile über dem Artikel. Alle Posten müssen in einer Liste mit Beschreibung, Menge, Stk-Preis, Preis und Kategorie erfasst werden. Das Datum muss im Format DD.MM.YYYY HH:MM vorliegen, falls keine Uhrzeit vorhanden ist, nur DD.MM.YYYY. Die Kategorie Getränke besteht aus 2 Kategorien: Getränke ohne Alkohol (z.B. Wasser, Cola, Säfte) und alkoholische Getränke (z.B. Bier, Wein, Spirituosen wie Whisky). Zigaretten -Hülsen oder -papier und Tabakwaren müssen in der Kategorie 'Tabakwaren' erfasst werden. Alle Pfand- und Leergutzeilen müssen die Kategorie 'Pfand' haben."
