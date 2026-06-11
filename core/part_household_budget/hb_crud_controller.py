# hb_crud_controller.py
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import select

# Importiert Ihre MVC-Modelle und den DB-Infrastruktur-Controller
from hb_model_db import Bank, BankAccount, BankStatement, StatementPosition, SalesType, Category, Receipt, Items
from hb_database_controller import DatabaseController

class CrudController:
    def __init__(self, db_controller: DatabaseController):
        self.db_controller = db_controller

    def _get_session(self) -> Session:
        """Erzeugt eine frische Arbeits-Session für eine Transaktion."""
        return Session(self.db_controller.get_engine())

    # ==========================================
    # VERARBEITUNG: KASSENZETTEL (RECEIPTS)
    # ==========================================

    def save_receipt_json(self, receipt_data: dict) -> bool:
        """
        Nimmt das validierte JSON-dict von gpt-4.1-mini entgegen
        und persistiert den Kassenbeleg samt Artikelsplittung.
        """
        with self._get_session() as session:
            try:
                # 1. Zahlungsart (SalesType) ermitteln oder neu anlegen
                sales_type_name = receipt_data.get("sales_type", "Manual")
                sales_type = session.scalar(
                    select(SalesType).where(SalesType.name == sales_type_name)
                )
                if not sales_type:
                    sales_type = SalesType(name=sales_type_name)
                    session.add(sales_type)
                    session.flush() # ID generieren ohne Commit

                # 2. Datum parsen (Unterstützt DD.MM.YYYY HH:MM oder nur DD.MM.YYYY)
                date_str = receipt_data["date_time"]
                try:
                    parsed_date = datetime.strptime(date_str, "%d.%m.%Y %H:%M")
                except ValueError:
                    parsed_date = datetime.strptime(date_str, "%d.%m.%Y")

                # 3. Haupt-Beleg (Receipt) anlegen
                new_receipt = Receipt(
                    sales_type=sales_type,
                    date=parsed_date,
                    total_amount=Decimal(str(receipt_data["total_sum"])),
                    shop_name=receipt_data.get("merchant")
                )
                session.add(new_receipt)
                session.flush()

                # 4. Einzelne Posten (Items) und Kategorien verarbeiten
                for item_dict in receipt_data.get("items", []):
                    category_name = item_dict.get("category", "Sonstiges")

                    # Kategorie ermitteln/anlegen
                    category = session.scalar(
                        select(Category).where(Category.name == category_name)
                    )
                    if not category:
                        category = Category(name=category_name)
                        session.add(category)
                        session.flush()

                    # Artikel-Zeile hinzufügen
                    new_item = Items(
                        receipt=new_receipt,
                        category=category,
                        name=item_dict["name"],
                        amount=Decimal(str(item_dict["price"])) # Nutzt korrigiertes Feld 'amount'
                    )
                    session.add(new_item)

                # Gesamte Transaktion festschreiben
                session.commit()
                print(f"[CRUD-Controller] Beleg von '{new_receipt.shop_name}' erfolgreich gebucht.")
                return True

            except Exception as e:
                session.rollback()
                print(f"[CRUD-Controller] Fehler beim Speichern des Belegs: {e}")
                return False

    # ==========================================
    # VERARBEITUNG: BANKAUSZÜGE (BANK STATEMENTS)
    # ==========================================

    def save_bank_statement_json(self, statement_data: dict) -> bool:
        """
        Nimmt das validierte JSON-dict von gpt-4.1-mini entgegen
        und persistiert den Bankauszug mit allen Umsatzpositionen.
        """
        with self._get_session() as session:
            try:
                # 1. Bank ermitteln oder neu anlegen
                bank_name = statement_data["bank_name"]
                bank = session.scalar(select(Bank).where(Bank.name == bank_name))
                if not bank:
                    bank = Bank(name=bank_name, bic=statement_data.get("bic"))
                    session.add(bank)
                    session.flush()

                # 2. Bankkonto (BankAccount) ermitteln oder neu anlegen
                iban = statement_data["iban"].replace(" ", "")
                account = session.scalar(select(BankAccount).where(BankAccount.iban == iban))
                if not account:
                    account = BankAccount(
                        bank=bank,
                        account_name=statement_data["account_name"],
                        iban=iban
                    )
                    session.add(account)
                    session.flush()

                # 3. Datumsfelder des Auszugs konvertieren
                start_dt = datetime.strptime(statement_data["start_date"], "%Y-%m-%d").date()
                end_dt = datetime.strptime(statement_data["end_date"], "%Y-%m-%d").date()

                # 4. Bankauszug (BankStatement) eintragen
                new_statement = BankStatement(
                    account=account,
                    statement_number=statement_data["statement_number"],
                    start_date=start_dt,
                    end_date=end_dt,
                    starting_balance=Decimal(str(statement_data["starting_balance"])),
                    ending_balance=Decimal(str(statement_data["ending_balance"])),
                    is_reconciled=False
                )
                session.add(new_statement)
                session.flush()

                # 5. Einzelne Umsatzpositionen (StatementPositions) einfügen
                for pos_dict in statement_data.get("positions", []):
                    b_date = datetime.strptime(pos_dict["booking_date"], "%Y-%m-%d").date()
                    v_date = datetime.strptime(pos_dict["valuta_date"], "%Y-%m-%d").date()

                    new_position = StatementPosition(
                        statement=new_statement,
                        booking_date=b_date,
                        valuta_date=v_date,
                        amount=Decimal(str(pos_dict["amount"])),
                        raw_description=pos_dict["raw_description"],
                        check_status="UNCHECKED" # Status für Ihr späteres Check-System
                    )
                    session.add(new_position)

                session.commit()
                print(f"[CRUD-Controller] Bankauszug Nr. {new_statement.statement_number} erfolgreich eingepflegt.")
                return True

            except Exception as e:
                session.rollback()
                print(f"[CRUD-Controller] Fehler beim Speichern des Bankauszugs: {e}")
                return False
