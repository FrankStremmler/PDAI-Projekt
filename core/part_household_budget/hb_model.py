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
