"""
Duplicate Transaction Detector

Implements duplicate detection algorithm using SHA-256 hash of
amount + date + description with 24-hour window and 80% similarity threshold.
"""

import hashlib
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from difflib import SequenceMatcher
import logging

from watchers.shared.database import Database

logger = logging.getLogger(__name__)


class DuplicateDetector:
    """
    Detects duplicate business transactions to prevent double-recording.

    Uses three-factor matching:
    1. Amount must match exactly
    2. Date must be within 24-hour window
    3. Description similarity must be >80%
    """

    def __init__(self, db: Database):
        """
        Initialize duplicate detector.

        Args:
            db: Database instance for querying existing transactions
        """
        self.db = db
        self.similarity_threshold = 0.80  # 80% similarity
        self.time_window_hours = 24  # 24-hour window

    def generate_hash(self, amount: float, date: str, description: str) -> str:
        """
        Generate SHA-256 hash for duplicate detection.

        Args:
            amount: Transaction amount
            date: Transaction date (ISO format)
            description: Transaction description

        Returns:
            SHA-256 hash string
        """
        # Normalize inputs for consistent hashing
        normalized_amount = f"{float(amount):.2f}"  # 2 decimal places
        normalized_date = date[:10]  # YYYY-MM-DD only
        normalized_desc = description.strip().lower()

        # Concatenate and hash
        hash_input = f"{normalized_amount}|{normalized_date}|{normalized_desc}"
        return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity ratio between two text strings.

        Args:
            text1: First text string
            text2: Second text string

        Returns:
            Similarity ratio between 0.0 and 1.0
        """
        # Normalize texts
        text1_norm = text1.strip().lower()
        text2_norm = text2.strip().lower()

        # Use SequenceMatcher for similarity calculation
        return SequenceMatcher(None, text1_norm, text2_norm).ratio()

    def is_duplicate(
        self,
        amount: float,
        date: str,
        description: str,
        external_id: Optional[str] = None
    ) -> tuple[bool, Optional[Dict[str, Any]]]:
        """
        Check if transaction is a duplicate of an existing transaction.

        Args:
            amount: Transaction amount
            date: Transaction date (ISO format)
            description: Transaction description
            external_id: Odoo transaction ID (optional, for exact match check)

        Returns:
            Tuple of (is_duplicate: bool, matching_transaction: dict or None)
        """
        try:
            # Step 1: Check for exact external_id match (fastest check)
            if external_id:
                cursor = self.db.conn.cursor()
                cursor.execute(
                    "SELECT * FROM business_transactions WHERE external_id = ?",
                    (external_id,)
                )
                exact_match = cursor.fetchone()
                if exact_match:
                    logger.info(f"Exact duplicate found by external_id: {external_id}")
                    return True, self._row_to_dict(exact_match, cursor)

            # Step 2: Calculate time window for date matching
            transaction_date = datetime.fromisoformat(date.replace('Z', '+00:00'))
            start_date = transaction_date - timedelta(hours=self.time_window_hours)
            end_date = transaction_date + timedelta(hours=self.time_window_hours)

            # Step 3: Query candidates with matching amount and date window
            cursor = self.db.conn.cursor()
            cursor.execute(
                """
                SELECT * FROM business_transactions
                WHERE amount = ?
                AND date BETWEEN ? AND ?
                """,
                (amount, start_date.isoformat(), end_date.isoformat())
            )
            candidates = cursor.fetchall()

            # Step 4: Check description similarity for each candidate
            for candidate in candidates:
                candidate_dict = self._row_to_dict(candidate, cursor)
                candidate_desc = candidate_dict.get('description', '')

                similarity = self.calculate_similarity(description, candidate_desc)

                if similarity >= self.similarity_threshold:
                    logger.info(
                        f"Duplicate found: amount={amount}, "
                        f"date={date}, similarity={similarity:.2%}"
                    )
                    return True, candidate_dict

            # No duplicates found
            return False, None

        except Exception as e:
            logger.error(f"Error checking for duplicates: {e}")
            # On error, assume not duplicate to avoid blocking legitimate transactions
            return False, None

    def _row_to_dict(self, row: tuple, cursor) -> Dict[str, Any]:
        """
        Convert SQLite row to dictionary.

        Args:
            row: SQLite row tuple
            cursor: Database cursor with column descriptions

        Returns:
            Dictionary with column names as keys
        """
        if not row:
            return {}

        columns = [description[0] for description in cursor.description]
        return dict(zip(columns, row))

    def get_duplicate_candidates(
        self,
        amount: float,
        date: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get potential duplicate candidates for manual review.

        Args:
            amount: Transaction amount
            date: Transaction date (ISO format)
            limit: Maximum number of candidates to return

        Returns:
            List of candidate transactions
        """
        try:
            transaction_date = datetime.fromisoformat(date.replace('Z', '+00:00'))
            start_date = transaction_date - timedelta(hours=self.time_window_hours)
            end_date = transaction_date + timedelta(hours=self.time_window_hours)

            cursor = self.db.conn.cursor()
            cursor.execute(
                """
                SELECT * FROM business_transactions
                WHERE amount = ?
                AND date BETWEEN ? AND ?
                ORDER BY date DESC
                LIMIT ?
                """,
                (amount, start_date.isoformat(), end_date.isoformat(), limit)
            )
            candidates = cursor.fetchall()

            return [self._row_to_dict(row, cursor) for row in candidates]

        except Exception as e:
            logger.error(f"Error getting duplicate candidates: {e}")
            return []
