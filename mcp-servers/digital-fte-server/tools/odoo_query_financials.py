"""
MCP Tool: Query Financial Data

Queries and aggregates financial data from business transactions.
Safety Level: 0 (Auto-Execute) - Read-only operation.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from watchers.shared.database import Database

logger = logging.getLogger(__name__)


def odoo_query_financials(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    group_by: str = "category"
) -> Dict[str, Any]:
    """
    Query and aggregate financial data from business transactions.

    Args:
        start_date: Start date filter (ISO format, optional, defaults to 30 days ago)
        end_date: End date filter (ISO format, optional, defaults to today)
        group_by: Grouping field (category, move_type, or month)

    Returns:
        Result dictionary with aggregated financial data
    """
    try:
        db = Database()
        cursor = db.conn.cursor()

        # Default date range: last 30 days
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).isoformat()
        if not end_date:
            end_date = datetime.now().isoformat()

        # Query transactions in date range
        cursor.execute("""
            SELECT * FROM business_transactions
            WHERE date >= ? AND date <= ?
            ORDER BY date ASC
        """, (start_date, end_date))

        rows = cursor.fetchall()
        transactions = [dict(row) for row in rows]

        if not transactions:
            return {
                "success": True,
                "total_transactions": 0,
                "total_amount": 0.0,
                "aggregated_data": {},
                "message": "No transactions found in date range"
            }

        # Aggregate data
        total_amount = 0.0
        aggregated = {}

        for transaction in transactions:
            total_amount += transaction["amount"]

            # Group by specified field
            if group_by == "category":
                key = transaction["category"]
            elif group_by == "move_type":
                key = transaction["move_type"]
            elif group_by == "month":
                transaction_date = datetime.fromisoformat(transaction["date"].replace('Z', '+00:00'))
                key = transaction_date.strftime("%Y-%m")
            else:
                key = "all"

            if key not in aggregated:
                aggregated[key] = {
                    "count": 0,
                    "total_amount": 0.0,
                    "transactions": []
                }

            aggregated[key]["count"] += 1
            aggregated[key]["total_amount"] += transaction["amount"]
            aggregated[key]["transactions"].append({
                "id": transaction["id"],
                "date": transaction["date"],
                "description": transaction["description"],
                "amount": transaction["amount"],
                "category": transaction["category"]
            })

        logger.info(f"Queried {len(transactions)} transactions, total: ${total_amount:,.2f}")

        return {
            "success": True,
            "total_transactions": len(transactions),
            "total_amount": total_amount,
            "start_date": start_date,
            "end_date": end_date,
            "group_by": group_by,
            "aggregated_data": aggregated,
            "message": f"Retrieved {len(transactions)} transactions totaling ${total_amount:,.2f}"
        }

    except Exception as e:
        logger.error(f"Error querying financials: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "total_transactions": 0,
            "total_amount": 0.0,
            "aggregated_data": {},
            "message": f"Error querying financials: {str(e)}"
        }
