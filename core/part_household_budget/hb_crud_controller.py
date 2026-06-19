from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select

from .hb_model_db import (
    Status, SyncStatus, Category, SubCategory,
    Bank, BankAccount, BankStatement, StatementPosition,
    Receipt, Items, Regular, AllocationProfile,
)
from .hb_database import DatabaseController
from .hb_base import NormalizedReceipt, NormalizedBankStatement


class DuplicateError(Exception):
    def __init__(self, message: str, db_entry, new_entry):
        super().__init__(message)
        self.db_entry = db_entry
        self.new_entry = new_entry


class CrudController:
    def __init__(self, db_controller: DatabaseController):
        self.db_controller = db_controller

    def _get_session(self) -> Session:
        return Session(self.db_controller.get_engine())

    # ==========================================
    # HILFSMETHODEN
    # ==========================================

    def _get_or_create_category(self, session, name: str) -> Optional[int]:
        if not name:
            return None
        cat = session.scalar(select(Category).where(Category.name == name))
        if cat:
            return cat.id
        c = Category(name=name)
        session.add(c)
        session.flush()
        return c.id

    def _get_or_create_subcategory(self, session, name: str, category_id: int) -> Optional[int]:
        if not name or not category_id:
            return None
        sub = session.scalar(
            select(SubCategory).where(SubCategory.name == name, SubCategory.category_id == category_id)
        )
        if sub:
            return sub.id
        s = SubCategory(name=name, category_id=category_id)
        session.add(s)
        session.flush()
        return s.id

    def _get_status_id(self, session, status_name: str) -> int:
        st = session.scalar(select(Status).where(Status.name == status_name))
        if st:
            return st.id
        s = Status(name=status_name)
        session.add(s)
        session.flush()
        return s.id

    def _init_status_values(self, session):
        for name in ["pending", "booked", "suspicious"]:
            existing = session.scalar(select(Status).where(Status.name == name))
            if not existing:
                session.add(Status(name=name))
        session.flush()

    # ==========================================
    # DUPLIKATPRÜFUNG & MERCHANT-NORMALISIERUNG
    # ==========================================

    def normalize_merchant(self, merchant: str) -> str:
        with self._get_session() as session:
            import sqlalchemy as sa
            existing = session.scalar(
                select(Receipt).where(sa.func.lower(Receipt.merchant) == merchant.lower())
            )
            if existing:
                return existing.merchant
            return merchant

    def _parse_receipt_date(self, date_str: str):
        try:
            return datetime.strptime(date_str, "%d.%m.%Y %H:%M:%S")
        except ValueError:
            try:
                return datetime.strptime(date_str, "%d.%m.%Y")
            except ValueError:
                try:
                    return datetime.fromisoformat(date_str)
                except ValueError:
                    return None

    def find_duplicate_receipt(self, receipt_data: NormalizedReceipt):
        parsed_date = self._parse_receipt_date(receipt_data.date_time)
        if not parsed_date:
            return None

        with self._get_session() as session:
            import sqlalchemy as sa
            existing = session.scalar(
                select(Receipt).where(
                    sa.func.lower(Receipt.merchant) == receipt_data.merchant.lower(),
                    Receipt.datum == parsed_date,
                    Receipt.total_sum == Decimal(str(receipt_data.total_sum)),
                )
            )
            if existing:
                return existing
            return None

    def find_duplicate_bank_statement(self, statement_data: NormalizedBankStatement):
        with self._get_session() as session:
            iban_clean = statement_data.iban.replace(" ", "")
            account = session.scalar(select(BankAccount).where(BankAccount.iban == iban_clean))
            if not account:
                return None

            zeitraum_von = datetime.strptime(statement_data.zeitraum_von, "%Y-%m-%d").date()
            existing = session.scalar(
                select(BankStatement).where(
                    BankStatement.bank_account_id == account.id,
                    BankStatement.zeitraum_von == zeitraum_von,
                    BankStatement.anfangsbestand == Decimal(str(statement_data.anfangsbestand)),
                )
            )
            if existing:
                return existing
            return None

    # ==========================================
    # KASSENZETTEL (RECEIPTS)
    # ==========================================

    def save_receipt(self, receipt_data: NormalizedReceipt) -> bool:
        receipt_data.merchant = self.normalize_merchant(receipt_data.merchant)

        dup = self.find_duplicate_receipt(receipt_data)
        if dup:
            raise DuplicateError(
                "Beleg vorhanden",
                f"{dup.datum.strftime('%d.%m.%Y')} | {dup.merchant} | {float(dup.total_sum):.2f} €",
                f"{receipt_data.date_time} | {receipt_data.merchant} | {receipt_data.total_sum:.2f} €",
            )

        with self._get_session() as session:
            try:
                self._init_status_values(session)

                status_name = "booked" if receipt_data.payment_method else "pending"
                status_id = self._get_status_id(session, status_name)

                parsed_date = self._parse_receipt_date(receipt_data.date_time)
                if not parsed_date:
                    parsed_date = datetime.utcnow()

                new_receipt = Receipt(
                    merchant=receipt_data.merchant,
                    datum=parsed_date,
                    total_sum=Decimal(str(receipt_data.total_sum)),
                    payment_method=int(receipt_data.payment_method),
                    status_id=status_id,
                )
                session.add(new_receipt)
                session.flush()

                for item in receipt_data.items:
                    category_id = self._get_or_create_category(session, item.category)
                    sub_category_id = self._get_or_create_subcategory(session, item.sub_category, category_id)

                    new_item = Items(
                        receipt_id=new_receipt.id,
                        category_id=category_id,
                        sub_category_id=sub_category_id,
                        amount=Decimal(str(item.amount)),
                        name=item.name,
                        price=Decimal(str(item.price)),
                    )
                    session.add(new_item)

                session.commit()
                print(f"[CRUD] Beleg '{receipt_data.merchant}' gespeichert (ID={new_receipt.id})")
                self.db_controller.update_last_update()
                self.db_controller.save_and_sync_back()
                return True

            except Exception as e:
                session.rollback()
                print(f"[CRUD] Fehler beim Speichern des Belegs: {e}")
                return False

    def save_bank_statement(self, statement_data: NormalizedBankStatement) -> bool:
        dup = self.find_duplicate_bank_statement(statement_data)
        if dup:
            raise DuplicateError(
                "Kontoauszug vorhanden",
                f"{dup.zeitraum_von} | {statement_data.bank_name} | {float(dup.anfangsbestand):.2f} €",
                f"{statement_data.zeitraum_von} | {statement_data.bank_name} | {statement_data.anfangsbestand:.2f} €",
            )
        with self._get_session() as session:
            try:
                bank = session.scalar(select(Bank).where(Bank.name == statement_data.bank_name))
                if not bank:
                    bank = Bank(name=statement_data.bank_name)
                    session.add(bank)
                    session.flush()

                iban_clean = statement_data.iban.replace(" ", "")
                account = session.scalar(select(BankAccount).where(BankAccount.iban == iban_clean))
                if not account:
                    account = BankAccount(
                        bank_id=bank.id,
                        iban=iban_clean,
                        inhaber=statement_data.inhaber,
                    )
                    session.add(account)
                    session.flush()

                new_statement = BankStatement(
                    bank_account_id=account.id,
                    zeitraum_von=datetime.strptime(statement_data.zeitraum_von, "%Y-%m-%d").date(),
                    zeitraum_bis=datetime.strptime(statement_data.zeitraum_bis, "%Y-%m-%d").date(),
                    anfangsbestand=Decimal(str(statement_data.anfangsbestand)),
                    endbestand=Decimal(str(statement_data.endbestand)),
                )
                session.add(new_statement)
                session.flush()

                for pos in statement_data.positionen:
                    category_id = self._get_or_create_category(session, pos.category)
                    sub_category_id = self._get_or_create_subcategory(session, pos.sub_category, category_id)

                    new_pos = StatementPosition(
                        bank_statement_id=new_statement.id,
                        category_id=category_id,
                        sub_category_id=sub_category_id,
                        buchungsdatum=datetime.strptime(pos.buchungsdatum, "%Y-%m-%d").date(),
                        verwendungszweck=pos.verwendungszweck,
                        beguenstigter_auftraggeber=pos.beguenstigter_auftraggeber,
                        betrag=Decimal(str(pos.betrag)),
                    )
                    session.add(new_pos)

                session.commit()
                print(f"[CRUD] Kontoauszug '{statement_data.bank_name}' gespeichert (ID={new_statement.id})")
                self.db_controller.update_last_update()
                self.db_controller.save_and_sync_back()
                return True

            except Exception as e:
                session.rollback()
                print(f"[CRUD] Fehler beim Speichern des Kontoauszugs: {e}")
                return False

    # ==========================================
    # LESE-METHODEN
    # ==========================================

    def get_all_receipts(self) -> list:
        with self._get_session() as session:
            rows = session.execute(
                select(
                    Receipt.id,
                    Receipt.merchant,
                    Receipt.datum,
                    Receipt.total_sum,
                    Status.name.label("status"),
                )
                .join(Status, Receipt.status_id == Status.id)
                .order_by(Receipt.id.desc())
            ).all()
            return [(r.id, r.merchant, r.datum.strftime("%d.%m.%Y"), float(r.total_sum), r.status) for r in rows]

    def get_all_bank_statements(self) -> list:
        with self._get_session() as session:
            rows = session.execute(
                select(
                    BankStatement.id,
                    Bank.name,
                    BankAccount.iban,
                    BankStatement.zeitraum_von,
                    BankStatement.zeitraum_bis,
                    BankStatement.endbestand,
                )
                .join(BankAccount, BankStatement.bank_account_id == BankAccount.id)
                .join(Bank, BankAccount.bank_id == Bank.id)
                .order_by(BankStatement.id.desc())
            ).all()
            return [
                (r.id, r.name, r.iban, f"{r.zeitraum_von} - {r.zeitraum_bis}", float(r.endbestand))
                for r in rows
            ]

    def get_all_categories(self) -> list:
        with self._get_session() as session:
            cats = session.scalars(select(Category)).all()
            session.expunge_all()
            return cats

    def get_all_banks(self) -> list:
        with self._get_session() as session:
            banks = session.scalars(select(Bank)).all()
            session.expunge_all()
            return banks

    def get_all_bank_accounts(self) -> list:
        with self._get_session() as session:
            accounts = session.scalars(select(BankAccount)).all()
            session.expunge_all()
            return accounts

    def get_all_regular_expenses(self) -> list:
        with self._get_session() as session:
            regulars = session.scalars(select(Regular)).all()
            session.expunge_all()
            return regulars

    # ==========================================
    # DELETE
    # ==========================================

    def delete_receipt(self, receipt_id: int) -> bool:
        with self._get_session() as session:
            try:
                receipt = session.get(Receipt, receipt_id)
                if not receipt:
                    return False
                for pos in session.scalars(
                    select(StatementPosition).where(StatementPosition.matched_receipt_id == receipt_id)
                ).all():
                    pos.matched_receipt_id = None
                session.delete(receipt)
                session.commit()
                print(f"[CRUD] Beleg ID={receipt_id} gelöscht")
                self.db_controller.update_last_update()
                self.db_controller.save_and_sync_back()
                return True
            except Exception as e:
                session.rollback()
                print(f"[CRUD] Fehler beim Löschen des Belegs: {e}")
                return False

    def delete_bank_statement(self, statement_id: int) -> bool:
        with self._get_session() as session:
            try:
                statement = session.get(BankStatement, statement_id)
                if not statement:
                    return False
                session.delete(statement)
                session.commit()
                print(f"[CRUD] Kontoauszug ID={statement_id} gelöscht")
                self.db_controller.update_last_update()
                self.db_controller.save_and_sync_back()
                return True
            except Exception as e:
                session.rollback()
                print(f"[CRUD] Fehler beim Löschen des Kontoauszugs: {e}")
                return False

    # ==========================================
    # CREATE / UPDATE
    # ==========================================

    def create_category(self, name: str) -> bool:
        with self._get_session() as session:
            try:
                existing = session.scalar(select(Category).where(Category.name == name))
                if existing:
                    return False
                session.add(Category(name=name))
                session.commit()
                self.db_controller.update_last_update()
                self.db_controller.save_and_sync_back()
                return True
            except Exception as e:
                session.rollback()
                print(f"[CRUD] Fehler: {e}")
                return False

    def create_regular_expense(self, category_id: int, name: str, amount: Decimal, interval: str) -> bool:
        with self._get_session() as session:
            try:
                session.add(Regular(
                    category_id=category_id, name=name,
                    amount=amount, interval=interval
                ))
                session.commit()
                self.db_controller.update_last_update()
                self.db_controller.save_and_sync_back()
                return True
            except Exception as e:
                session.rollback()
                print(f"[CRUD] Fehler: {e}")
                return False
