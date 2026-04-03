"""
Odoo Watcher Configuration

Defines configuration for Odoo transaction monitoring including
polling intervals, category mappings, and transaction state definitions.
"""

from enum import Enum
from typing import Dict, List
from dataclasses import dataclass


class TransactionCategory(Enum):
    """Standard business accounting categories."""
    REVENUE = "Revenue"
    COGS = "COGS"  # Cost of Goods Sold
    OPERATING_EXPENSES = "Operating Expenses"
    ASSETS = "Assets"
    LIABILITIES = "Liabilities"
    EQUITY = "Equity"


class TransactionState(Enum):
    """Odoo transaction states."""
    DRAFT = "draft"
    POSTED = "posted"
    CANCELLED = "cancelled"


class MoveType(Enum):
    """Odoo move types."""
    INVOICE = "invoice"
    PAYMENT = "payment"
    EXPENSE = "expense"
    REFUND = "refund"


@dataclass
class OdooConfig:
    """Configuration for Odoo watcher."""

    # Polling configuration
    polling_interval: int = 300  # 5 minutes in seconds

    # Transaction filtering
    fetch_limit: int = 100  # Max transactions per poll
    only_posted: bool = True  # Only fetch posted transactions

    # Duplicate detection window
    duplicate_window_hours: int = 24  # 24-hour window for duplicate detection
    duplicate_similarity_threshold: float = 0.80  # 80% description similarity

    # Category mappings (Odoo account code prefix -> Category)
    # These are standard account code prefixes used in chart of accounts
    category_mappings: Dict[str, TransactionCategory] = None

    def __post_init__(self):
        """Initialize default category mappings if not provided."""
        if self.category_mappings is None:
            self.category_mappings = {
                # Revenue accounts (4xxx)
                "4": TransactionCategory.REVENUE,
                "40": TransactionCategory.REVENUE,
                "41": TransactionCategory.REVENUE,

                # COGS accounts (5xxx)
                "5": TransactionCategory.COGS,
                "50": TransactionCategory.COGS,
                "51": TransactionCategory.COGS,

                # Operating Expenses (6xxx)
                "6": TransactionCategory.OPERATING_EXPENSES,
                "60": TransactionCategory.OPERATING_EXPENSES,
                "61": TransactionCategory.OPERATING_EXPENSES,
                "62": TransactionCategory.OPERATING_EXPENSES,
                "63": TransactionCategory.OPERATING_EXPENSES,
                "64": TransactionCategory.OPERATING_EXPENSES,
                "65": TransactionCategory.OPERATING_EXPENSES,

                # Assets (1xxx, 2xxx)
                "1": TransactionCategory.ASSETS,
                "10": TransactionCategory.ASSETS,
                "11": TransactionCategory.ASSETS,
                "12": TransactionCategory.ASSETS,
                "2": TransactionCategory.ASSETS,
                "20": TransactionCategory.ASSETS,
                "21": TransactionCategory.ASSETS,

                # Liabilities (4xxx for payables)
                "42": TransactionCategory.LIABILITIES,
                "43": TransactionCategory.LIABILITIES,
                "44": TransactionCategory.LIABILITIES,

                # Equity (3xxx)
                "3": TransactionCategory.EQUITY,
                "30": TransactionCategory.EQUITY,
                "31": TransactionCategory.EQUITY,
            }

    def get_category_from_account_code(self, account_code: str) -> TransactionCategory:
        """
        Map Odoo account code to transaction category.

        Args:
            account_code: Odoo account code (e.g., "400000", "600100")

        Returns:
            TransactionCategory enum value

        Raises:
            ValueError: If account code cannot be mapped to a category
        """
        # Try exact match first
        if account_code in self.category_mappings:
            return self.category_mappings[account_code]

        # Try prefix matching (longest prefix first)
        for length in range(len(account_code), 0, -1):
            prefix = account_code[:length]
            if prefix in self.category_mappings:
                return self.category_mappings[prefix]

        # Default to Operating Expenses if no match found
        # This is a safe default for unknown accounts
        return TransactionCategory.OPERATING_EXPENSES

    def is_valid_state(self, state: str) -> bool:
        """Check if transaction state is valid."""
        try:
            TransactionState(state)
            return True
        except ValueError:
            return False

    def should_process_transaction(self, state: str) -> bool:
        """
        Determine if transaction should be processed based on state.

        Args:
            state: Transaction state from Odoo

        Returns:
            True if transaction should be processed, False otherwise
        """
        if self.only_posted:
            return state == TransactionState.POSTED.value
        return state in [TransactionState.DRAFT.value, TransactionState.POSTED.value]


# Global configuration instance
config = OdooConfig()
