"""
Financial Summary Aggregator

Aggregates financial data from business transactions for CEO briefing.
Calculates revenue, expenses, profit, trends, and top items.
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
import logging

from watchers.shared.database import Database
from watchers.briefing_watcher.config import BriefingConfig

logger = logging.getLogger(__name__)


class FinancialAggregator:
    """
    Aggregates financial data for CEO briefing.
    """

    def __init__(self, db: Database = None):
        """Initialize financial aggregator."""
        self.db = db or Database()
        self.config = BriefingConfig

    def aggregate_financial_summary(
        self,
        period_start: datetime,
        period_end: datetime
    ) -> Dict[str, Any]:
        """
        Aggregate financial summary for a time period.

        Args:
            period_start: Start of period (Monday)
            period_end: End of period (Sunday)

        Returns:
            Financial summary dictionary
        """
        try:
            # Get current week transactions
            current_transactions = self._get_transactions(period_start, period_end)

            # Get previous week transactions for comparison
            previous_start = period_start - timedelta(days=7)
            previous_end = period_end - timedelta(days=7)
            previous_transactions = self._get_transactions(previous_start, previous_end)

            # Calculate metrics
            current_revenue = self._calculate_revenue(current_transactions)
            previous_revenue = self._calculate_revenue(previous_transactions)

            current_expenses = self._calculate_expenses(current_transactions)
            previous_expenses = self._calculate_expenses(previous_transactions)

            current_profit = current_revenue - current_expenses
            previous_profit = previous_revenue - previous_expenses

            # Calculate trends
            revenue_change = self._calculate_change_percent(current_revenue, previous_revenue)
            expenses_change = self._calculate_change_percent(current_expenses, previous_expenses)
            profit_change = self._calculate_change_percent(current_profit, previous_profit)

            # Get top items
            top_revenue_sources = self._get_top_revenue_sources(current_transactions)
            top_expenses = self._get_top_expenses(current_transactions)

            summary = {
                "revenue": {
                    "current_week": current_revenue,
                    "last_week": previous_revenue,
                    "change_percent": revenue_change,
                    "trend": self._get_trend_direction(revenue_change)
                },
                "expenses": {
                    "current_week": current_expenses,
                    "last_week": previous_expenses,
                    "change_percent": expenses_change,
                    "trend": self._get_trend_direction(expenses_change)
                },
                "profit": {
                    "current_week": current_profit,
                    "last_week": previous_profit,
                    "change_percent": profit_change,
                    "trend": self._get_trend_direction(profit_change)
                },
                "top_revenue_sources": top_revenue_sources,
                "top_expenses": top_expenses,
                "transaction_count": len(current_transactions)
            }

            logger.info(
                f"Financial summary: Revenue ${current_revenue:,.2f}, "
                f"Expenses ${current_expenses:,.2f}, Profit ${current_profit:,.2f}"
            )

            return summary

        except Exception as e:
            logger.error(f"Failed to aggregate financial summary: {e}", exc_info=True)
            return self._get_empty_summary()

    def _get_transactions(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get transactions for date range."""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT * FROM business_transactions
            WHERE date >= ? AND date <= ?
            AND state = 'posted'
            ORDER BY date ASC
        """, (start_date.isoformat(), end_date.isoformat()))

        return [dict(row) for row in cursor.fetchall()]

    def _calculate_revenue(self, transactions: List[Dict]) -> float:
        """Calculate total revenue from transactions."""
        revenue = 0.0
        for txn in transactions:
            if self.config.is_revenue_category(txn["category"]):
                revenue += txn["amount"]
        return revenue

    def _calculate_expenses(self, transactions: List[Dict]) -> float:
        """Calculate total expenses from transactions."""
        expenses = 0.0
        for txn in transactions:
            if self.config.is_expense_category(txn["category"]):
                expenses += txn["amount"]
        return expenses

    def _calculate_change_percent(self, current: float, previous: float) -> float:
        """Calculate percentage change."""
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        return ((current - previous) / previous) * 100

    def _get_trend_direction(self, change_percent: float) -> str:
        """Get trend direction from change percentage."""
        if change_percent > 5:
            return "up"
        elif change_percent < -5:
            return "down"
        else:
            return "flat"

    def _get_top_revenue_sources(self, transactions: List[Dict]) -> List[Dict]:
        """Get top revenue sources."""
        revenue_by_source = {}

        for txn in transactions:
            if self.config.is_revenue_category(txn["category"]):
                source = txn.get("subcategory") or txn["category"]
                if source not in revenue_by_source:
                    revenue_by_source[source] = 0.0
                revenue_by_source[source] += txn["amount"]

        # Sort and get top N
        sorted_sources = sorted(
            revenue_by_source.items(),
            key=lambda x: x[1],
            reverse=True
        )[:self.config.TOP_ITEMS_LIMIT]

        return [
            {"name": name, "amount": amount}
            for name, amount in sorted_sources
        ]

    def _get_top_expenses(self, transactions: List[Dict]) -> List[Dict]:
        """Get top expenses."""
        expenses_by_category = {}

        for txn in transactions:
            if self.config.is_expense_category(txn["category"]):
                category = txn.get("subcategory") or txn["category"]
                if category not in expenses_by_category:
                    expenses_by_category[category] = 0.0
                expenses_by_category[category] += txn["amount"]

        # Sort and get top N
        sorted_expenses = sorted(
            expenses_by_category.items(),
            key=lambda x: x[1],
            reverse=True
        )[:self.config.TOP_ITEMS_LIMIT]

        return [
            {"name": name, "amount": amount}
            for name, amount in sorted_expenses
        ]

    def _get_empty_summary(self) -> Dict[str, Any]:
        """Get empty summary structure."""
        return {
            "revenue": {
                "current_week": 0.0,
                "last_week": 0.0,
                "change_percent": 0.0,
                "trend": "flat"
            },
            "expenses": {
                "current_week": 0.0,
                "last_week": 0.0,
                "change_percent": 0.0,
                "trend": "flat"
            },
            "profit": {
                "current_week": 0.0,
                "last_week": 0.0,
                "change_percent": 0.0,
                "trend": "flat"
            },
            "top_revenue_sources": [],
            "top_expenses": [],
            "transaction_count": 0
        }
