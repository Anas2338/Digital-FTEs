"""
MCP Tool: Get Business Transactions

Retrieves business transactions from the accounting database with filtering.
Safety Level: 0 (Auto-Execute) - Read-only operation.
"""

from typing import Dict, Any, List, Optional
import logging

from watchers.shared.database import Database

logger = logging.getLogger(__name__)


def odoo_get_transactions(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 100
) -> Dict[str, Any]:
    """
    Get business transactions with optional filtering.

    Args:
        start_date: Start date filter (ISO format, optional)
        end_date: End date filter (ISO format, optional)
        category: Category filter (optional)
        limit: Maximum number of transactions to return (default: 100)

    Returns:
        Result dictionary with transactions list
    """
    try:
        db = Database()
        cursor = db.conn.cursor()

        query = "SELECT * FROM business_transactions WHERE 1=1"
        params = []

        if start_date:
            query += " AND date >= ?"
            params.append(start_date)

        if end_date:
            query += " AND date <= ?"
            params.append(end_date)

        if category:
            query += " AND category = ?"
            params.append(category)

        query += " ORDER BY date DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        transactions = []
        for row in rows:
            transactions.append({
                "id": row["id"],
                "external_id": row["external_id"],
                "amount": row["amount"],
                "currency": row["currency"],
                "date": row["date"],
                "category": row["category"],
                "subcategory": row["subcategory"],
                "description": row["description"],
                "partner_name": row["partner_name"],
                "account_code": row["account_code"],
                "move_type": row["move_type"],
                "state": row["state"],
                "created_at": row["created_at"]
            })

        logger.info(f"Retrieved {len(transactions)} transactions")

        return {
            "success": True,
            "count": len(transactions),
            "transactions": transactions,
            "message": f"Retrieved {len(transactions)} transactions"
        }

    except Exception as e:
        logger.error(f"Error retrieving transactions: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "transactions": [],
            "message": f"Error retrieving transactions: {str(e)}"
        }
