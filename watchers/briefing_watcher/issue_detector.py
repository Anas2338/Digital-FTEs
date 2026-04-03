"""
Critical Issue Detector

Detects critical issues requiring attention in CEO briefing.
Identifies overdue invoices, low engagement, high expenses, etc.
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta
import logging

from watchers.shared.database import Database
from watchers.briefing_watcher.config import BriefingConfig

logger = logging.getLogger(__name__)


class IssueDetector:
    """
    Detects critical issues for CEO briefing.
    """

    def __init__(self, db: Database = None):
        """Initialize issue detector."""
        self.db = db or Database()
        self.config = BriefingConfig

    def detect_critical_issues(
        self,
        period_start: datetime,
        period_end: datetime
    ) -> List[Dict[str, Any]]:
        """
        Detect critical issues for a time period.

        Args:
            period_start: Start of period
            period_end: End of period

        Returns:
            List of critical issue dictionaries
        """
        issues = []

        # Detect overdue invoices
        issues.extend(self._detect_overdue_invoices())

        # Detect high expenses
        issues.extend(self._detect_high_expenses(period_start, period_end))

        # Detect low engagement (if social media data available)
        issues.extend(self._detect_low_engagement(period_start, period_end))

        # Sort by priority
        issues.sort(key=lambda x: self._priority_order(x["priority"]))

        logger.info(f"Detected {len(issues)} critical issues")

        return issues

    def _detect_overdue_invoices(self) -> List[Dict[str, Any]]:
        """Detect overdue invoices."""
        issues = []

        try:
            cursor = self.db.conn.cursor()
            overdue_date = (datetime.now() - timedelta(days=self.config.OVERDUE_INVOICE_DAYS)).isoformat()

            cursor.execute("""
                SELECT * FROM business_transactions
                WHERE move_type = 'invoice'
                AND state = 'posted'
                AND date < ?
                AND category = 'Revenue'
            """, (overdue_date,))

            overdue_invoices = cursor.fetchall()

            for invoice in overdue_invoices:
                days_overdue = (datetime.now() - datetime.fromisoformat(invoice["date"].replace('Z', '+00:00'))).days

                issues.append({
                    "priority": "high",
                    "title": f"Invoice overdue by {days_overdue} days",
                    "description": f"{invoice['description']} - ${invoice['amount']:,.2f}",
                    "action_required": "Follow up with customer",
                    "created_at": datetime.now().isoformat() + "Z"
                })

        except Exception as e:
            logger.warning(f"Failed to detect overdue invoices: {e}")

        return issues

    def _detect_high_expenses(
        self,
        period_start: datetime,
        period_end: datetime
    ) -> List[Dict[str, Any]]:
        """Detect unusually high expenses."""
        issues = []

        try:
            cursor = self.db.conn.cursor()

            # Get current period expenses
            cursor.execute("""
                SELECT category, subcategory, SUM(amount) as total
                FROM business_transactions
                WHERE date >= ? AND date <= ?
                AND category IN ('COGS', 'Operating Expenses')
                GROUP BY category, subcategory
            """, (period_start.isoformat(), period_end.isoformat()))

            current_expenses = cursor.fetchall()

            # Get average expenses from last 4 weeks
            avg_start = period_start - timedelta(days=28)
            cursor.execute("""
                SELECT category, subcategory, AVG(amount) as avg_amount
                FROM business_transactions
                WHERE date >= ? AND date < ?
                AND category IN ('COGS', 'Operating Expenses')
                GROUP BY category, subcategory
            """, (avg_start.isoformat(), period_start.isoformat()))

            avg_expenses = {
                (row["category"], row["subcategory"]): row["avg_amount"]
                for row in cursor.fetchall()
            }

            # Check for expenses exceeding threshold
            for expense in current_expenses:
                key = (expense["category"], expense["subcategory"])
                avg = avg_expenses.get(key, 0)

                if avg > 0 and expense["total"] > avg * self.config.HIGH_EXPENSE_THRESHOLD:
                    percent_increase = ((expense["total"] - avg) / avg) * 100

                    issues.append({
                        "priority": "medium",
                        "title": f"High expense detected: {expense['subcategory'] or expense['category']}",
                        "description": f"${expense['total']:,.2f} ({percent_increase:.0f}% above average)",
                        "action_required": "Review expense category",
                        "created_at": datetime.now().isoformat() + "Z"
                    })

        except Exception as e:
            logger.warning(f"Failed to detect high expenses: {e}")

        return issues

    def _detect_low_engagement(
        self,
        period_start: datetime,
        period_end: datetime
    ) -> List[Dict[str, Any]]:
        """Detect low social media engagement."""
        issues = []

        try:
            # Check if social media table exists
            cursor = self.db.conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='social_media_posts'
            """)

            if not cursor.fetchone():
                return issues  # No social media data available

            # Get recent posts with low engagement
            cursor.execute("""
                SELECT * FROM social_media_posts
                WHERE published_time >= ? AND published_time <= ?
                AND status = 'published'
            """, (period_start.isoformat(), period_end.isoformat()))

            posts = cursor.fetchall()

            # Calculate average engagement
            if posts:
                total_engagement = 0
                for post in posts:
                    # Parse engagement metrics (simplified)
                    total_engagement += 1  # Placeholder

                avg_engagement = total_engagement / len(posts)
                threshold = avg_engagement * self.config.LOW_ENGAGEMENT_THRESHOLD

                # Find posts below threshold
                low_engagement_count = sum(1 for p in posts if True)  # Placeholder logic

                if low_engagement_count > 0:
                    issues.append({
                        "priority": "low",
                        "title": f"{low_engagement_count} posts with low engagement",
                        "description": "Social media posts performing below average",
                        "action_required": "Review content strategy",
                        "created_at": datetime.now().isoformat() + "Z"
                    })

        except Exception as e:
            logger.warning(f"Failed to detect low engagement: {e}")

        return issues

    def _priority_order(self, priority: str) -> int:
        """Get sort order for priority."""
        order = {"high": 0, "medium": 1, "low": 2}
        return order.get(priority, 3)
