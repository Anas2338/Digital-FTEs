"""
MCP Tool: Record Business Transaction

Records a business transaction from Odoo into the accounting system.
Safety Level: 0 (Auto-Execute) - Read-only operation that stores data locally.
"""

from typing import Dict, Any
import logging

from watchers.shared.database import Database
from watchers.odoo_watcher.transaction_processor import TransactionProcessor

logger = logging.getLogger(__name__)


def odoo_record_transaction(
    external_id: str,
    amount: float,
    currency: str,
    date: str,
    description: str,
    account_code: str,
    move_type: str,
    state: str,
    partner_name: str = None,
    partner_id: str = None,
    subcategory: str = None
) -> Dict[str, Any]:
    """
    Record a business transaction from Odoo.

    Args:
        external_id: Odoo transaction ID
        amount: Transaction amount
        currency: Currency code (USD, EUR, etc.)
        date: Transaction date (ISO format)
        description: Transaction description
        account_code: Odoo account code
        move_type: Transaction type (invoice, payment, expense, refund)
        state: Transaction state (draft, posted, cancelled)
        partner_name: Partner/vendor name (optional)
        partner_id: Odoo partner ID (optional)
        subcategory: User-defined subcategory (optional)

    Returns:
        Result dictionary with success status and transaction_id
    """
    try:
        db = Database()
        processor = TransactionProcessor(db)

        transaction_data = {
            "external_id": external_id,
            "amount": amount,
            "currency": currency,
            "date": date,
            "description": description,
            "account_code": account_code,
            "move_type": move_type,
            "state": state,
            "partner_name": partner_name,
            "partner_id": partner_id,
            "subcategory": subcategory
        }

        result = processor.process_transaction(transaction_data)

        if result["success"]:
            logger.info(f"Recorded transaction {result['transaction_id']}")
            return {
                "success": True,
                "transaction_id": result["transaction_id"],
                "category": result["category"],
                "message": f"Transaction recorded successfully in category: {result['category']}"
            }
        else:
            logger.warning(f"Failed to record transaction: {result.get('reason')}")
            return {
                "success": False,
                "reason": result.get("reason"),
                "errors": result.get("errors", []),
                "message": f"Failed to record transaction: {result.get('reason')}"
            }

    except Exception as e:
        logger.error(f"Error recording transaction: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": f"Error recording transaction: {str(e)}"
        }
