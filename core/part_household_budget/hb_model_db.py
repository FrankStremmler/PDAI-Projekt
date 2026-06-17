from decimal import Decimal
from datetime import date, datetime
from typing import List, Optional
from sqlalchemy import ForeignKey, String, Integer, Numeric, Date, DateTime, Boolean, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

# ==========================================
# STATUS (pending, booked, suspicious)
# ==========================================

class Status(Base):
    __tablename__ = "status"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)

    receipts: Mapped[List["Receipt"]] = relationship(back_populates="status_ref")


# ==========================================
# SYNC-STATUS (file tracking)
# ==========================================

class SyncStatus(Base):
    __tablename__ = "sync_status"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    datei_name: Mapped[str] = mapped_column(String(255), nullable=False)
    datei_typ: Mapped[str] = mapped_column(String(20), nullable=False)  # RECEIPT or STATEMENT
    verarbeitet_am: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # SUCCESS or ERROR
    fehler_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    receipts: Mapped[List["Receipt"]] = relationship(back_populates="sync")
    statements: Mapped[List["BankStatement"]] = relationship(back_populates="sync")


# ==========================================
# CATEGORY / SUB_CATEGORY
# ==========================================

class Category(Base):
    __tablename__ = "category"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    beschreibung: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    items: Mapped[List["Items"]] = relationship(back_populates="category")
    regular_expenses: Mapped[List["Regular"]] = relationship(back_populates="category")
    subcategories: Mapped[List["SubCategory"]] = relationship(back_populates="category")
    statement_positions: Mapped[List["StatementPosition"]] = relationship(back_populates="category")


class SubCategory(Base):
    __tablename__ = "sub_category"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("category.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    beschreibung: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    category: Mapped["Category"] = relationship(back_populates="subcategories")
    items: Mapped[List["Items"]] = relationship(back_populates="sub_category")
    statement_positions: Mapped[List["StatementPosition"]] = relationship(back_populates="sub_category")


# ==========================================
# BELEG-MODUL
# ==========================================

class Receipt(Base):
    __tablename__ = "receipt"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    merchant: Mapped[str] = mapped_column(String(100), nullable=False)
    datum: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    total_sum: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    payment_method: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # 0=card, 1=cash
    status_id: Mapped[int] = mapped_column(ForeignKey("status.id"), nullable=False)
    sync_id: Mapped[Optional[int]] = mapped_column(ForeignKey("sync_status.id"), nullable=True)

    status_ref: Mapped["Status"] = relationship(back_populates="receipts")
    sync: Mapped[Optional["SyncStatus"]] = relationship(back_populates="receipts")
    items: Mapped[List["Items"]] = relationship(back_populates="receipt", cascade="all, delete-orphan")


class Items(Base):
    __tablename__ = "items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    receipt_id: Mapped[int] = mapped_column(ForeignKey("receipt.id"), nullable=False)
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("category.id"), nullable=True)
    sub_category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("sub_category.id"), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=1)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)

    receipt: Mapped["Receipt"] = relationship(back_populates="items")
    category: Mapped[Optional["Category"]] = relationship(back_populates="items")
    sub_category: Mapped[Optional["SubCategory"]] = relationship(back_populates="items")


# ==========================================
# BANK-MODUL
# ==========================================

class Bank(Base):
    __tablename__ = "bank"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    blz: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    bic: Mapped[Optional[str]] = mapped_column(String(11), nullable=True)

    accounts: Mapped[List["BankAccount"]] = relationship(back_populates="bank")


class BankAccount(Base):
    __tablename__ = "bank_account"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bank_id: Mapped[int] = mapped_column(ForeignKey("bank.id"), nullable=False)
    kontonummer: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    iban: Mapped[str] = mapped_column(String(34), nullable=False, unique=True)
    inhaber: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    waehrung: Mapped[str] = mapped_column(String(3), nullable=False, default="EUR")

    bank: Mapped["Bank"] = relationship(back_populates="accounts")
    statements: Mapped[List["BankStatement"]] = relationship(back_populates="account")
    allocation_profiles: Mapped[List["AllocationProfile"]] = relationship(back_populates="account")


class BankStatement(Base):
    __tablename__ = "bank_statement"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bank_account_id: Mapped[int] = mapped_column(ForeignKey("bank_account.id"), nullable=False)
    zeitraum_von: Mapped[date] = mapped_column(Date, nullable=False)
    zeitraum_bis: Mapped[date] = mapped_column(Date, nullable=False)
    anfangsbestand: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    endbestand: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    sync_id: Mapped[Optional[int]] = mapped_column(ForeignKey("sync_status.id"), nullable=True)

    account: Mapped["BankAccount"] = relationship(back_populates="statements")
    sync: Mapped[Optional["SyncStatus"]] = relationship(back_populates="statements")
    positions: Mapped[List["StatementPosition"]] = relationship(back_populates="statement", cascade="all, delete-orphan")


class StatementPosition(Base):
    __tablename__ = "bank_statement_position"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bank_statement_id: Mapped[int] = mapped_column(ForeignKey("bank_statement.id"), nullable=False)
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("category.id"), nullable=True)
    sub_category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("sub_category.id"), nullable=True)
    matched_receipt_id: Mapped[Optional[int]] = mapped_column(ForeignKey("receipt.id"), nullable=True)
    buchungsdatum: Mapped[date] = mapped_column(Date, nullable=False)
    verwendungszweck: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    beguenstigter_auftraggeber: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    betrag: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    statement: Mapped["BankStatement"] = relationship(back_populates="positions")
    category: Mapped[Optional["Category"]] = relationship(back_populates="statement_positions")
    sub_category: Mapped[Optional["SubCategory"]] = relationship(back_populates="statement_positions")
    matched_receipt: Mapped[Optional["Receipt"]] = relationship()


# ==========================================
# REGELMÄßIGE AUSGABEN
# ==========================================

class Regular(Base):
    __tablename__ = "regular"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("category.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    interval: Mapped[str] = mapped_column(String(20), nullable=False)

    category: Mapped["Category"] = relationship(back_populates="regular_expenses")


# ==========================================
# ALLOKATIONSPROFILE (unverändert)
# ==========================================

class AllocationProfile(Base):
    __tablename__ = "allocation_profile"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bank_account_id: Mapped[int] = mapped_column(ForeignKey("bank_account.id"), nullable=False)
    date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    account: Mapped["BankAccount"] = relationship(back_populates="allocation_profiles")


class DbSync(Base):
    __tablename__ = "db_sync"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    last_update: Mapped[datetime] = mapped_column(DateTime, nullable=False)
