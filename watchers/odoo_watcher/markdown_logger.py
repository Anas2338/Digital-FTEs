"""
Markdown Transaction Logger

Generates human-readable Markdown logs of business transactions
organized by month in the Obsidian vault.
"""

import os
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import logging

from watchers.shared.database import Database


logger = logging.getLogger(__name__)


class TransactionMarkdownLogger:
    """
    Generates Markdown logs of business transactions for Obsidian vault.
    """

    def __init__(
        self,
        vault_path: str = "obsidian-vault",
        db: Database = None
    ):
        self.vault_path = Path(vault_path)
        self.accounting_path = self.vault_path / "Accounting"
        self.db = db or Database()
        self.accounting_path.mkdir(parents=True, exist_ok=True)

    def log_transaction(self, transaction_id: str):
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT * FROM business_transactions
            WHERE id = ?
        """, (transaction_id,))

        row = cursor.fetchone()
        if not row:
            logger.warning(f"Transaction {transaction_id} not found")
            return

        transaction = dict(row)

        transaction_date = datetime.fromisoformat(transaction["date"].replace('Z', '+00:00'))
        month_dir = self.accounting_path / transaction_date.strftime("%Y-%m")
        month_dir.mkdir(parents=True, exist_ok=True)

        month_file = month_dir / "transactions.md"

        self._append_transaction_to_file(month_file, transaction)

        logger.info(f"Logged transaction {transaction_id} to {month_file}")

    def log_batch(self, transaction_ids: List[str]):
        for transaction_id in transaction_ids:
            self.log_transaction(transaction_id)

    def generate_monthly_summary(self, year: int, month: int) -> str:
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year + 1}-01-01"
        else:
            end_date = f"{year}-{month + 1:02d}-01"

        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT * FROM business_transactions
            WHERE date >= ? AND date < ?
            ORDER BY date ASC
        """, (start_date, end_date))

        transactions = [dict(row) for row in cursor.fetchall()]

        if not transactions:
            logger.info(f"No transactions found for {year}-{month:02d}")
            return None

        summary = self._calculate_summary(transactions)

        month_dir = self.accounting_path / f"{year}-{month:02d}"
        month_dir.mkdir(parents=True, exist_ok=True)
        summary_file = month_dir / "summary.md"

        self._write_summary_file(summary_file, year, month, summary, transactions)

        logger.info(f"Generated monthly summary: {summary_file}")
        return str(summary_file)

    def _append_transaction_to_file(self, file_path: Path, transaction: Dict[str, Any]):
        if not file_path.exists():
            self._write_file_header(file_path, transaction["date"])

        transaction_date = datetime.fromisoformat(transaction["date"].replace('Z', '+00:00'))
        entry = f"""
## {transaction_date.strftime('%Y-%m-%d')} - {transaction['description']}

- **Amount**: {transaction['currency']} {transaction['amount']:.2f}
- **Category**: {transaction['category']}
- **Subcategory**: {transaction.get('subcategory') or 'N/A'}
- **Partner**: {transaction.get('partner_name') or 'N/A'}
- **Account Code**: {transaction['account_code']}
- **Type**: {transaction['move_type']}
- **State**: {transaction['state']}
- **External ID**: `{transaction['external_id']}`
- **Transaction ID**: `{transaction['id']}`

---

"""

        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(entry)

    def _write_file_header(self, file_path: Path, date_str: str):
        transaction_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        month_name = transaction_date.strftime('%B %Y')

        header = f"""# Business Transactions - {month_name}

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

"""

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(header)

    def _calculate_summary(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        summary = {
            "total_transactions": len(transactions),
            "total_amount": 0.0,
            "by_category": {},
            "by_type": {},
            "by_state": {}
        }

        for transaction in transactions:
            summary["total_amount"] += transaction["amount"]

            category = transaction["category"]
            if category not in summary["by_category"]:
                summary["by_category"][category] = {"count": 0, "amount": 0.0}
            summary["by_category"][category]["count"] += 1
            summary["by_category"][category]["amount"] += transaction["amount"]

            move_type = transaction["move_type"]
            if move_type not in summary["by_type"]:
                summary["by_type"][move_type] = 0
            summary["by_type"][move_type] += 1

            state = transaction["state"]
            if state not in summary["by_state"]:
                summary["by_state"][state] = 0
            summary["by_state"][state] += 1

        return summary

    def _write_summary_file(
        self,
        file_path: Path,
        year: int,
        month: int,
        summary: Dict[str, Any],
        transactions: List[Dict[str, Any]]
    ):
        month_name = datetime(year, month, 1).strftime('%B %Y')

        content = f"""# Monthly Summary - {month_name}

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overview

- **Total Transactions**: {summary['total_transactions']}
- **Total Amount**: ${summary['total_amount']:,.2f}

## By Category

| Category | Count | Amount |
|----------|-------|--------|
"""

        for category, data in sorted(summary["by_category"].items()):
            content += f"| {category} | {data['count']} | ${data['amount']:,.2f} |\n"

        content += f"""
## By Transaction Type

| Type | Count |
|------|-------|
"""

        for move_type, count in sorted(summary["by_type"].items()):
            content += f"| {move_type} | {count} |\n"

        content += f"""
## By State

| State | Count |
|-------|-------|
"""

        for state, count in sorted(summary["by_state"].items()):
            content += f"| {state} | {count} |\n"

        content += """
## All Transactions

"""

        for transaction in transactions:
            transaction_date = datetime.fromisoformat(transaction["date"].replace('Z', '+00:00'))
            content += f"- **{transaction_date.strftime('%Y-%m-%d')}**: {transaction['description']} - ${transaction['amount']:.2f} ({transaction['category']})\n"

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
