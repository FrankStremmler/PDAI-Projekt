import os
import sqlite3
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
DB_PATH = ROOT_DIR / "hb_database.db"

CATEGORY_TABLE = """
CREATE TABLE IF NOT EXISTS category (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    description TEXT NOT NULL UNIQUE
);
"""

RECEIPTS_TABLE = """
CREATE TABLE IF NOT EXISTS receipts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    store TEXT NOT NULL,
    date_time DATETIME NOT NULL UNIQUE
);
"""

ITEMS_TABLE = """
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    receipt_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    description TEXT NOT NULL,
    amount INTEGER NOT NULL,
    price REAL NOT NULL,
    FOREIGN KEY(receipt_id) REFERENCES receipts(id),
    FOREIGN KEY(category_id) REFERENCES category(id)
);
"""

PERIOD_TABLE = """
CREATE TABLE IF NOT EXISTS period (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL UNIQUE,
    time_distance INTEGER NOT NULL,
    date DATETIME NOT NULL
);
"""

REGULAR_TABLE = """
CREATE TABLE IF NOT EXISTS regular (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL,
    period_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    description TEXT NOT NULL,
    FOREIGN KEY(category_id) REFERENCES category(id),
    FOREIGN KEY(period_id) REFERENCES period(id)
);
"""


def ensure_database() -> None:
    os.makedirs(ROOT_DIR, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    try:
        cursor = connection.cursor()
        cursor.execute(CATEGORY_TABLE)
        cursor.execute(RECEIPTS_TABLE)
        cursor.execute(ITEMS_TABLE)
        cursor.execute(PERIOD_TABLE)
        cursor.execute(REGULAR_TABLE)
        connection.commit()
    finally:
        connection.close()


def get_database_path() -> str:
    return str(DB_PATH)
