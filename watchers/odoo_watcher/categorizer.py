"""
Transaction Categorizer

Automatically categorizes business transactions based on Odoo account codes.
Maps account codes to standard accounting categories.
"""

import logging
from typing import Dict, Any, Optional

from watchers.odoo_watcher.config import OdooConfig, AccountCategory

logger = logging.getLogger(__name__)


class TransactionCategorizer:
    """
    Categorizes business transactions based on account codes.

    Uses Odoo chart of accounts structure to map account codes
    to standard accounting categories.
    """

    def __init__(self):
        """Initialize categorizer with configuration."""
        self.config = OdooConfig

    def categorize(self, account_code: str) -> Dict[str, Any]:
        """
        Categorize a transaction based on its account code.

        Args:
            account_code: Odoo account code (3-digit)

        Returns:
            Dictionary with category, subcategory suggestions, and confidence
        """
        try:
            # Get category from account code
            category = self.config.get_category_for_account(account_code)

            # Get subcategory suggestions
            subcategory_suggestions = self.config.get_subcategory_suggestions(account_code)

            # Determine confidence level
            confidence = self._calculate_confidence(account_code, category)

            logger.debug(f"Categorized account {account_code} as {category} (confidence: {confidence})")

            return {
                "category": category,
                "subcategory_suggestions": subcategory_suggestions,
                "confidence": confidence,
                "account_code": account_code
            }

        except ValueError as e:
            logger.warning(f"Failed to categorize account code {account_code}: {e}")
            return {
                "category": "Operating Expenses",  # Default fallback
                "subcategory_suggestions": [],
                "confidence": "low",
                "account_code": account_code,
                "error": str(e)
            }

    def categorize_batch(self, transactions: list) -> list:
        """
        Categorize multiple transactions.

        Args:
            transactions: List of transaction dictionaries with account_code field

        Returns:
            List of transactions with added category information
        """
        categorized = []

        for transaction in transactions:
            account_code = transaction.get("account_code", "000")
            category_info = self.categorize(account_code)

            # Add category info to transaction
            transaction_with_category = {
                **transaction,
                "category": category_info["category"],
                "subcategory_suggestions": category_info["subcategory_suggestions"],
                "categorization_confidence": category_info["confidence"]
            }

            categorized.append(transaction_with_category)

        return categorized

    def _calculate_confidence(self, account_code: str, category: str) -> str:
        """
        Calculate confidence level for categorization.

        Args:
            account_code: Account code
            category: Assigned category

        Returns:
            Confidence level: high, medium, or low
        """
        # Exact match in mapping = high confidence
        if account_code in self.config.ACCOUNT_CATEGORY_MAPPING:
            return "high"

        # Prefix match (first digit) = medium confidence
        if account_code and len(account_code) >= 1:
            first_digit = account_code[0]
            if first_digit in ["1", "2", "3", "4", "5", "6"]:
                return "medium"

        # Fallback = low confidence
        return "low"

    def get_category_statistics(self, transactions: list) -> Dict[str, Any]:
        """
        Get statistics about categorization for a set of transactions.

        Args:
            transactions: List of transactions with account_code field

        Returns:
            Statistics dictionary
        """
        stats = {
            "total": len(transactions),
            "by_category": {},
            "by_confidence": {"high": 0, "medium": 0, "low": 0},
            "uncategorized": 0
        }

        for transaction in transactions:
            account_code = transaction.get("account_code", "000")
            category_info = self.categorize(account_code)

            # Count by category
            category = category_info["category"]
            if category not in stats["by_category"]:
                stats["by_category"][category] = 0
            stats["by_category"][category] += 1

            # Count by confidence
            confidence = category_info["confidence"]
            stats["by_confidence"][confidence] += 1

            # Count errors
            if "error" in category_info:
                stats["uncategorized"] += 1

        return stats
