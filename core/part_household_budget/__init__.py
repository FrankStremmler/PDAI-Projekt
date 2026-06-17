"""
Household Budget Module - Financial tracking and analysis for personal budgets.
Uses SQLAlchemy ORM for database management.
"""

from .hb_database import ensure_database, DatabaseController
from .hb_view import HouseholdBudgetView
from .hb_controller import HouseholdBudgetController
from .hb_ai import ReceiptAnalyzer
from .hb_crud_controller import CrudController
from .hb_file_input_controller import AIPlatformWrapper

# Pydantic Schemas
from .hb_base import (
    NormalizedReceipt, NormalizedItem,
    NormalizedBankStatement, NormalizedBankPosition,
    ReceiptSchema, ReceiptItemSchema,
    BankStatementSchema, BankPositionSchema,
)

# SQLAlchemy ORM Models
from .hb_model_db import (
    Base,
    Status, SyncStatus,
    Category, SubCategory,
    Bank, BankAccount, BankStatement, StatementPosition,
    Receipt, Items, Regular, AllocationProfile, DbSync,
)

__all__ = [
    "ensure_database",
    "DatabaseController",
    "HouseholdBudgetView",
    "HouseholdBudgetController",
    "CrudController",
    "ReceiptAnalyzer",
    "AIPlatformWrapper",
    "NormalizedReceipt",
    "NormalizedItem",
    "NormalizedBankStatement",
    "NormalizedBankPosition",
    "ReceiptSchema",
    "ReceiptItemSchema",
    "BankStatementSchema",
    "BankPositionSchema",
    "Base",
    "Status",
    "SyncStatus",
    "Category",
    "SubCategory",
    "Bank",
    "BankAccount",
    "BankStatement",
    "StatementPosition",
    "Receipt",
    "Items",
    "Regular",
    "AllocationProfile",
    "DbSync",
]
