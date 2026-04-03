"""
Transaction Processor for Odoo Integration

Processes transactions from Odoo, validates them, checks for duplicates,
and stores them in the database with proper categorization.
"""

import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from watchers.shared.database import Database
from watchers.shared.audit_logger import AuditLogger
from watchers.odoo_watcher.duplicate_detector import DuplicateDetector
from watchers.odoo_watcher.config import OdooConfig


logger = logging.getLogger(__name__)


class TransactionProcessor:
    """
    Processes and stores business transactions from Odoo.
    """

    def __init__(
        self,
        db: Optional[Database] = None,
        audit_logger: Optional[AuditLogger] = None
    ):
        self.db = db or Database()
        self.audit_logger = audit_logger or AuditLogger(self.db)
        self.duplicate_detector = DuplicateDetector(self.db)

    def process_transaction(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            validation_result = self._validate_transaction(transaction_data)
            if not validation_result["valid"]:
                logger.warning(f"Invalid transaction: {validation_result['errors']}")
                return {
                    "success": False,
                    "reason": "validation_failed",
                    "errors": validation_result["errors"]
                }

            duplicate_check = self.duplicate_detector.is_duplicate(
                amount=transaction_data["amount"],
                date=transaction_data["date"],
                description=transaction_data["description"],
                external_id=transaction_data.get("external_id")
            )

            if duplicate_check["is_duplicate"]:
                logger.info(
                    f"Duplicate transaction detected: {duplicate_check['reason']} "
                    f"(matching: {duplicate_check['matching_transaction_id']})"
                )
                return {
                    "success": False,
                    "reason": "duplicate",
                    "duplicate_check": duplicate_check
                }

            account_code = transaction_data.get("account_code", "000")
            try:
                category = OdooConfig.get_category_for_account(account_code)
            except ValueError as e:
                logger.error(f"Failed to map account code {account_code}: {e}")
                category = "Operating Expenses"

            transaction_id = str(uuid.uuid4())
            duplicate_hash = self.duplicate_detector.calculate_hash(
                amount=transaction_data["amount"],
                date=transaction_data["date"],
                description=transaction_data["description"]
            )

            now = datetime.utcnow().isoformat() + "Z"
            transaction_record = {
                "id": transaction_id,
                "external_id": transaction_data.get("external_id", ""),
                "amount": transaction_data["amount"],
                "currency": transaction_data.get("currency", OdooConfig.DEFAULT_CURRENCY),
                "date": transaction_data["date"],
                "category": category,
                "subcategory": transaction_data.get("subcategory"),
                "description": transaction_data["description"],
                "partner_name": transaction_data.get("partner_name"),
                "partner_id": transaction_data.get("partner_id"),
                "account_code": account_code,
                "move_type": transaction_data.get("move_type", "entry"),
                "state": transaction_data.get("state", "posted"),
                "created_at": now,
                "updated_at": now,
                "duplicate_check_hash": duplicate_hash
            }

            self._store_transaction(transaction_record)

            self.audit_logger.log_action(
                action_type="write",
                action_name="odoo_record_transaction",
                parameters={
                    "external_id": transaction_record["external_id"],
                    "amount": transaction_record["amount"],
                    "category": transaction_record["category"],
                    "account_code": account_code
                },
                result={"transaction_id": transaction_id},
                reasoning="Recorded new business transaction from Odoo",
                safety_level=0,
                domain_context="business"
            )

            logger.info(
                f"Processed transaction {transaction_id}: "
                f"{transaction_record['amount']} {transaction_record['currency']} "
                f"({category})"
            )

            return {
                "success": True,
                "transaction_id": transaction_id,
                "category": category
            }

        except Exception as e:
            logger.error(f"Failed to process transaction: {e}", exc_info=True)
            return {
                "success": False,
                "reason": "processing_error",
                "error": str(e)
            }

    def process_batch(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        results = {
            "total": len(transactions),
            "success": 0,
            "duplicates": 0,
            "validation_errors": 0,
            "processing_errors": 0,
            "transaction_ids": []
        }

        for transaction_data in transactions:
            result = self.process_transaction(transaction_data)

            if result["success"]:
                results["success"] += 1
                results["transaction_ids"].append(result["transaction_id"])
            elif result.get("reason") == "duplicate":
                results["duplicates"] += 1
            elif result.get("reason") == "validation_failed":
                results["validation_errors"] += 1
            else:
                results["processing_errors"] += 1

        logger.info(
            f"Batch processing complete: {results['success']}/{results['total']} successful, "
            f"{results['duplicates']} duplicates, {results['validation_errors']} validation errors, "
            f"{results['processing_errors']} processing errors"
        )

        return results

    def _validate_transaction(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        errors = []

        required_fields = ["amount", "date", "description"]
        for field in required_fields:
            if field not in transaction_data or not transaction_data[field]:
                errors.append(f"Missing required field: {field}")

        if "amount" in transaction_data:
            amount = transaction_data["amount"]
            if not isinstance(amount, (int, float)) or amount <= 0:
                errors.append(f"Invalid amount: {amount}")
            elif not OdooConfig.validate_amount(amount):
                errors.append(
                    f"Amount out of range: {amount} "
                    f"(min: {OdooConfig.MIN_AMOUNT}, max: {OdooConfig.MAX_AMOUNT})"
                )

        if "date" in transaction_data:
            try:
                transaction_date = datetime.fromisoformat(
                    transaction_data["date"].replace('Z', '+00:00')
                )
                if transaction_date > datetime.now():
                    errors.append("Transaction date cannot be in the future")
            except (ValueError, AttributeError):
                errors.append(f"Invalid date format: {transaction_data['date']}")

        if "currency" in transaction_data:
            if not OdooConfig.validate_currency(transaction_data["currency"]):
                errors.append(
                    f"Unsupported currency: {transaction_data['currency']} "
                    f"(supported: {OdooConfig.SUPPORTED_CURRENCIES})"
                )

        if "description" in transaction_data:
            if len(transaction_data["description"]) > OdooConfig.MAX_DESCRIPTION_LENGTH:
                errors.append(
                    f"Description too long: {len(transaction_data["description"])} chars "
                    f"(max: {OdooConfig.MAX_DESCRIPTION_LENGTH})"
                )

        if "partner_name" in transaction_data and transaction_data["partner_name"]:
            if len(transaction_data["partner_name"]) > OdooConfig.MAX_PARTNER_NAME_LENGTH:
                errors.append(
                    f"Partner name too long: {len(transaction_data['partner_name'])} chars "
                    f"(max: {OdooConfig.MAX_PARTNER_NAME_LENGTH})"
                )

        return {
            "valid": len(errors) == 0,
            "errors": errors
        }

    def _store_transaction(self, transaction_record: Dict[str, Any]):
        cursor = self.db.conn.cursor()
        cursor.execute("""
            INSERT INTO business_transactions
            (id, external_id, amount, currency, date, category, subcategory,
             description, partner_name, partner_id, account_code, move_type,
             state, created_at, updated_at, duplicate_check_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            transaction_record["id"],
            transaction_record["external_id"],
            transaction_record["amount"],
            transaction_record["currency"],
            transaction_record["date"],
            transaction_record["category"],
            transaction_record["subcategory"],
            transaction_record["description"],
            transaction_record["partner_name"],
            transaction_record["partner_id"],
            transaction_record["account_code"],
            transaction_record["move_type"],
            transaction_record["state"],
            transaction_record["created_at"],
            transaction_record["updated_at"],
            transaction_record["duplicate_check_hash"]
        ))

        self.db.conn.commit()
