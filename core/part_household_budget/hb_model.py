from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Category:
    id: int
    description: str


@dataclass
class Receipt:
    id: int
    store: str
    date_time: datetime


@dataclass
class Item:
    id: int
    receipt_id: int
    category_id: int
    description: str
    amount: int
    price: float


@dataclass
class PeriodEntry:
    id: int
    type: str
    time_distance: int
    date: datetime


@dataclass
class RegularEntry:
    id: int
    category_id: int
    period_id: int
    amount: float
    description: str

def save_receipt_path(file_path: str) -> Optional[int]:
    # Hier würden Sie die Logik implementieren, um den Pfad in der Datenbank zu speichern
    # und eine neue Receipt-ID zurückzugeben. Zum Beispiel:
    # new_receipt_id = database.insert_receipt(file_path)
    # return new_receipt_id
    pass    
