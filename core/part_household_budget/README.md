# Household Budget Modul

## Überblick

Das Household Budget-Modul verwaltet die Finanzdaten eines Haushalts mit SQLAlchemy ORM.

## Datenbankstruktur

### Tabellen (11 insgesamt)

#### Bank-Modul
- **bank**: Bankinstitute mit Name und BIC-Code
- **bankaccount**: Bankkonten mit IBAN und Währung
- **bankstatement**: Bankauszüge mit Start-/Enddatum und Salden
- **statementposition**: Einzelne Buchungen eines Auszugs
- **allocationprofile**: Allokationsprofile für Konten

#### Beleg-Modul
- **receipt**: Einzelne Belege/Quittungen mit Datum und Betrag
- **items**: Einzelne Positionen aus Belegen
- **salestype**: Zahlungsarten (z.B. Bargeld, Karte)
- **category**: Ausgabenkategorien
- **regular**: Regelmäßige Ausgaben

#### Metadaten
- **sync_status**: Synchronisierungsstatus für Cloud-Integration

## Komponenten

### DatabaseController (`hb_database.py`)

Verwaltet die Datenbankverbindung mit drei Phasen:

1. **Working Phase**: Datenbank wird im Temp-Ordner geladen
2. **Operations Phase**: Alle Änderungen happen im Temp-Ordner
3. **Sync Phase**: Änderungen werden auf Master-DB synchronized

```python
from core.part_household_budget import ensure_database

db = ensure_database()
db.create_db()
db.save_and_sync_back()
```

### CrudController (`hb_crud_controller.py`)

CRUD-Operationen für alle Entitäten:

#### Kategorien
```python
crud.create_category("Lebensmittel")
crud.get_all_categories()
```

#### Belege
```python
receipt_data = {
    "merchant": "Aldi",
    "date_time": "2026-06-12",
    "sales_type": "Bargeld",
    "total_sum": "45.67",
    "items": [
        {
            "name": "Milch",
            "category": "Lebensmittel",
            "price": "1.99"
        }
    ]
}
crud.save_receipt_json(receipt_data)
crud.get_all_receipts()
```

#### Bankauszüge
```python
statement_data = {
    "bank_name": "Deutsche Bank",
    "iban": "DE89...",
    "account_name": "Girokonto",
    "statement_number": "2026-06",
    "start_date": "2026-06-01",
    "end_date": "2026-06-30",
    "starting_balance": "1500.00",
    "ending_balance": "1650.00",
    "positions": [...]
}
crud.save_bank_statement_json(statement_data)
```

#### Regelmäßige Ausgaben
```python
crud.create_regular_expense(
    category_id=1,
    name="Miete",
    amount=Decimal("850.00"),
    interval="monthly"
)
crud.get_all_regular_expenses()
```

#### Sync-Status
```python
crud.update_sync_status("google_drive")
```

## Models (`hb_model_db.py`)

Alle Modelle verwenden SQLAlchemy mit Type Hints:

```python
from core.part_household_budget import Category, Receipt, BankAccount

# Laden von Objekten
with session() as s:
    category = s.get(Category, 1)
    receipts = s.scalars(select(Receipt)).all()
```

## Integration mit der App

### In der Main-App
```python
from pdai_gui.subapps import HouseholdBudgetWidget

# Widget zur App hinzufügen
household_widget = HouseholdBudgetWidget()
```

### Mit OpenAI (AI-Analyse)
```python
from core.part_household_budget import ReceiptAnalyzer

analyzer = ReceiptAnalyzer()
result = analyzer.analyze_receipt("bild.jpg")
# Speichert Ergebnis in response.json
```

## Dateistruktur

```
core/part_household_budget/
├── __init__.py              # Package-Exporte
├── hb_database.py           # Database Controller (SQLAlchemy)
├── hb_model_db.py           # SQLAlchemy ORM Models
├── hb_crud_controller.py    # CRUD-Operationen
├── hb_controller.py         # GUI-Controller
├── hb_view.py               # GUI-View (PySide6)
├── hb_ai.py                 # OpenAI Integration
├── hb_prompts_constants.py  # AI-Prompts
├── global_functions.py      # Hilfsfunktionen
└── README.md                # Diese Datei
```

## Status

✅ Alle 11 Tabellen erstellt
✅ CRUD-Operationen implementiert
✅ SQLAlchemy ORM vollständig
✅ Datenbankinitialisierung getestet
✅ Sync-Mechanismus implementiert

## Nächste Schritte

- [ ] GUI-Integration in Hauptapp
- [ ] Google Drive Cloud-Sync
- [ ] Erweiterte Filterung und Reporting
- [ ] Fehlerbehandlung und Validierung
