# hb_base.py
from typing import Optional, List
from pydantic import BaseModel, Field

# ==========================================
# PYDANTIC MODELLE FÜR KASSENZETTEL (RECEIPTS)
# ==========================================

class ReceiptItemSchema(BaseModel):
    name: str = Field(
        description="Beschreibung des Artikels auf dem Beleg (z.B. Milch, Cola oder auch 'Pfand / Leergut')."
    )
    quantity: float = Field(
        description="Stückzahl oder Menge. Bei mehreren Artikeln steht die Stückzahl in der Zeile über dem Artikel. Bei Artikeln mit Gewicht steht das Gewicht in der Zeile über dem Artikel (das Gewicht ist dann die Stückzahl)."
    )
    unit_price: float = Field(
        description="Stückpreis oder kg-Preis in Euro. Bei mehreren Artikeln oder Artikeln mit Gewicht steht dieser in der Zeile über dem Artikel."
    )
    price: float = Field(
        description="Endpreis des Postens in Euro. WICHTIG: Wenn es sich um eine Pfandrückgabe/Guthaben handelt, trage den Wert als NEGATIVEN Betrag ein (z.B. -0.25)."
    )
    category: str = Field(
        description="Kategorie des Artikels. Nutze 'Pfand' für alle Pfand- und Leergutzeilen. Ansonsten klassische Kategorien wie 'Lebensmittel', 'Tabakwaren', 'Hygiene', 'Getränke ohne Alkohol' oder 'alkoholische Getränke'."
    )

class ReceiptSchema(BaseModel):
    merchant: str = Field(description="Name des Geschäfts oder Geschäftsname, z.B. Aldi, Lidl, Rewe")
    date_time: str = Field(description="Datum und Uhrzeit des Belegs im Format DD.MM.YYYY HH:MM. Falls keine Uhrzeit vorhanden, nur DD.MM.YYYY")
    total_sum: float = Field(description="Gesamtsumme des Belegs in Euro.")
    sales_type: str = Field(description="Zahlungsart, z.B. 'Cash', 'Girocard', 'Credit Card' oder 'Manual'")
    items: List[ReceiptItemSchema] = Field(description="Liste aller extrahierten Posten des Kassenzettels.")


# ==========================================
# PYDANTIC MODELLE FÜR BANKAUSZÜGE (BANK STATEMENTS)
# ==========================================

class BankPositionSchema(BaseModel):
    booking_date: str = Field(description="Buchungstag im Format YYYY-MM-DD")
    valuta_date: str = Field(description="Wertstellung (Valuta) im Format YYYY-MM-DD")
    amount: float = Field(description="Betrag der Buchung. Ausgaben negativ (z.B. -101.50), Eingänge positiv.")
    raw_description: str = Field(description="Vollständiger, ungeschnittener Verwendungszweck aus dem PDF inkl. Anbieter/Empfänger.")

class BankStatementSchema(BaseModel):
    bank_name: str = Field(description="Name der Bank (z.B. Postbank)")
    bic: Optional[str] = Field(None, description="BIC der Bank, falls vorhanden, sonst null")
    iban: str = Field(description="IBAN des Kontos")
    account_name: str = Field(description="Bezeichnung des Kontos (z.B. Girokonto)")
    statement_number: str = Field(description="Offizielle Auszugsnummer (z.B. 2025/003)")
    start_date: str = Field(description="Startdatum des Auszugszeitraums im Format YYYY-MM-DD")
    end_date: str = Field(description="Enddatum des Auszugszeitraums im Format YYYY-MM-DD")
    starting_balance: float = Field(description="Der alte Kontostand (Anfangssaldo) zu Beginn des Auszugs.")
    ending_balance: float = Field(description="Der neue Kontostand (Endsaldo) am Ende des Auszugs.")
    positions: List[BankPositionSchema] = Field(description="Liste aller einzelnen Umsatzbuchungen auf dem Auszug.")


# ==========================================
# ABSTRAKTE WRAPPER (Für spätere Cloud- / KI-Provider)
# ==========================================
# Hier platzieren Sie später Ihre abstrakten Basisklassen (ABC)
# class AbstractCloudWrapper: ...
# class AbstractAIProvider: ...
