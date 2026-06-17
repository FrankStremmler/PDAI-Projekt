from datetime import datetime
from pydantic import BaseModel, Field, model_validator, field_validator
from typing import List, Optional


class NormalizedItem(BaseModel):
    name: str = Field(..., description="Beschreibung des Artikels auf dem Beleg")
    amount: Optional[float] = Field(None, description="Stückzahl oder Menge")
    unit_price: Optional[float] = Field(None, description="Stückpreis in Euro")
    price: Optional[float] = Field(None, description="Gesamtpreis des Postens. Bei Pfand NEGATIV.")
    category: str = Field(..., description="Warengruppe, z.B. Lebensmittel, Getränke, Drogerie")
    sub_category: str = Field("", description="Unterkategorie, z.B. Tiefkühlkost, Obst, Milchprodukte")

    @model_validator(mode="before")
    @classmethod
    def _normalize_quantity(cls, data):
        if isinstance(data, dict) and "quantity" in data and "amount" not in data:
            data["amount"] = data.pop("quantity")
        return data

    @model_validator(mode="after")
    def _fill_missing(self):
        if self.amount is None:
            self.amount = 1.0
        if self.price is None and self.unit_price is not None:
            self.price = round(self.amount * self.unit_price, 2)
        if self.unit_price is None and self.price is not None and self.amount != 0:
            self.unit_price = round(self.price / self.amount, 2)
        if self.price is None:
            self.price = 0.0
        if self.unit_price is None:
            self.unit_price = 0.0
        return self


class NormalizedReceipt(BaseModel):
    merchant: str = Field(..., description="Name des Geschäfts, z.B. Aldi, Lidl, Rewe")
    date_time: str = Field(..., description="Datum des Belegs")
    total_sum: float = Field(..., description="Die finale Gesamtsumme des Belegs")
    payment_method: bool = Field(..., description="Zahlungsmethode: True = bar (cash), False = Karte (card)")
    items: List[NormalizedItem] = Field(default_factory=list)

    @field_validator("date_time")
    @classmethod
    def _normalize_datetime(cls, v: str) -> str:
        for fmt in (
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%d.%m.%Y %H:%M:%S",
            "%Y-%m-%d",
            "%d.%m.%Y",
        ):
            try:
                dt = datetime.strptime(v, fmt)
                return dt.strftime("%d.%m.%Y %H:%M:%S")
            except ValueError:
                continue
        return v


class NormalizedBankPosition(BaseModel):
    buchungsdatum: str = Field(..., description="Buchungsdatum im Format YYYY-MM-DD")
    verwendungszweck: str = Field("", description="Verwendungszweck der Buchung")
    beguenstigter_auftraggeber: str = Field("", description="Begünstigter oder Auftraggeber")
    betrag: float = Field(..., description="Betrag der Buchung (negativ = Ausgabe, positiv = Einnahme)")
    category: str = Field(..., description="Warengruppe, z.B. Lebensmittel, Gehalt, Miete")
    sub_category: str = Field("", description="Unterkategorie, z.B. Tiefkühlkost, Monatsgehalt")


class NormalizedBankStatement(BaseModel):
    bank_name: str = Field(..., description="Name der Bank")
    iban: str = Field(..., description="IBAN des Kontos")
    inhaber: str = Field(..., description="Kontoinhaber")
    zeitraum_von: str = Field(..., description="Beginn des Auszugszeitraums im Format YYYY-MM-DD")
    zeitraum_bis: str = Field(..., description="Ende des Auszugszeitraums im Format YYYY-MM-DD")
    anfangsbestand: float = Field(..., description="Anfangsbestand/Kontostand zu Beginn")
    endbestand: float = Field(..., description="Endbestand/Kontostand am Ende")
    positionen: List[NormalizedBankPosition] = Field(default_factory=list)


# ==========================================
# Alias für Abwärtskompatibilität
# ==========================================
ReceiptSchema = NormalizedReceipt
ReceiptItemSchema = NormalizedItem
BankStatementSchema = NormalizedBankStatement
BankPositionSchema = NormalizedBankPosition
