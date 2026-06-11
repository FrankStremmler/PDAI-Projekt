# models.py
from decimal import Decimal
from datetime import date, datetime
from typing import List, Optional
from sqlalchemy import ForeignKey, String, Integer, Numeric, Date, DateTime, Boolean, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

# ==========================================
# BANK-MODUL
# ==========================================

class Bank(Base):
    __tablename__ = "bank"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    bic: Mapped[Optional[str]] = mapped_column(String(11), nullable=True)

    accounts: Mapped[List["BankAccount"]] = relationship(back_populates="bank")


class BankAccount(Base):
    __tablename__ = "bankaccount"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bank_id: Mapped[int] = mapped_column(ForeignKey("bank.id"), nullable=False)
    account_name: Mapped[str] = mapped_column(String(50), nullable=False)
    iban: Mapped[str] = mapped_column(String(34), nullable=False, unique=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="EUR")

    bank: Mapped["Bank"] = relationship(back_populates="accounts")
    statements: Mapped[List["BankStatement"]] = relationship(back_populates="account")


class BankStatement(Base):
    __tablename__ = "bankstatement"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bankaccount_id: Mapped[int] = mapped_column(ForeignKey("bankaccount.id"), nullable=False)
    statement_number: Mapped[str] = mapped_column(String(20), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    starting_balance: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    ending_balance: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    is_reconciled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    account: Mapped["BankAccount"] = relationship(back_populates="statements")
    positions: Mapped[List["StatementPosition"]] = relationship(back_populates="statement")


class StatementPosition(Base):
    __tablename__ = "statementposition"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bankstatement_id: Mapped[int] = mapped_column(ForeignKey("bankstatement.id"), nullable=False)
    booking_date: Mapped[date] = mapped_column(Date, nullable=False)
    valuta_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    raw_description: Mapped[str] = mapped_column(text("TEXT"), nullable=False)
    check_status: Mapped[str] = mapped_column(String(20), nullable=False, default="UNCHECKED")

    statement: Mapped["BankStatement"] = relationship(back_populates="positions")
    receipts: Mapped[List["Receipt"]] = relationship(back_populates="statement_position")


# ==========================================
# BELEG-MODUL
# ==========================================

class SalesType(Base):
    __tablename__ = "salestype"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)

    receipts: Mapped[List["Receipt"]] = relationship(back_populates="sales_type")


class Category(Base):
    __tablename__ = "category"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)

    items: Mapped[List["Items"]] = relationship(back_populates="category")
    regular_expenses: Mapped[List["Regular"]] = relationship(back_populates="category")


class Receipt(Base):
    __tablename__ = "receipt"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    salestype_id: Mapped[int] = mapped_column(ForeignKey("salestype.id"), nullable=False)
    statementposition_id: Mapped[Optional[int]] = mapped_column(ForeignKey("statementposition.id"), nullable=True)
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    shop_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    sales_type: Mapped["SalesType"] = relationship(back_populates="receipts")
    statement_position: Mapped[Optional["StatementPosition"]] = relationship(back_populates="receipts")
    items: Mapped[List["Items"]] = relationship(back_populates="receipt")


class Items(Base):
    __tablename__ = "items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    receipt_id: Mapped[int] = mapped_column(ForeignKey("receipt.id"), nullable=False)
    category_id: Mapped[int] = mapped_column(ForeignKey("category.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    receipt: Mapped["Receipt"] = relationship(back_populates="items")
    category: Mapped["Category"] = relationship(back_populates="items")


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
# METADATEN / STATUS
# ==========================================

class SyncStatus(Base):
    __tablename__ = "sync_status"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    latest_update: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    last_sync_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
