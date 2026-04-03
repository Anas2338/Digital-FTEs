"""
Comprehensive Audit Logger for Digital FTE

Implements tamper-evident audit logging with hash chain integrity
and PII redaction for compliance and security.

Features:
- Hash chain integrity (each entry references previous entry's hash)
- PII redaction (passwords, API keys, tokens, emails, phone numbers)
- Structured logging with reasoning and approval tracking
- Safety level tracking (0-3)
"""

import hashlib
import json
import re
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from watchers.shared.database import Database


logger = logging.getLogger(__name__)


class AuditLogger:
    """
    Comprehensive audit logger with hash chain integrity and PII redaction.
    """

    # PII patterns for redaction
    PII_PATTERNS = {
        "password": re.compile(r'("password"\s*:\s*")[^"]*(")', re.IGNORECASE),
        "api_key": re.compile(r'("api[_-]?key"\s*:\s*")[^"]*(")', re.IGNORECASE),
        "token": re.compile(r'("(?:access_)?token"\s*:\s*")[^"]*(")', re.IGNORECASE),
        "secret": re.compile(r'("(?:api_)?secret"\s*:\s*")[^"]*(")', re.IGNORECASE),
        "email": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
        "phone": re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'),
        "ssn": re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
        "credit_card": re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'),
    }

    def __init__(self, db: Optional[Database] = None):
        """
        Initialize audit logger.

        Args:
            db: Database instance (creates new if None)
        """
        self.db = db or Database()
        self.current_domain_context: Optional[str] = None

    def set_domain_context(self, domain_context: str):
        """
        Set the current domain context for audit logging.

        Args:
            domain_context: Domain context (personal, business, shared)
        """
        self.current_domain_context = domain_context
        logger.info(f"Set audit logger domain context to: {domain_context}")

    def clear_domain_context(self):
        """Clear the current domain context."""
        self.current_domain_context = None
        logger.info("Cleared audit logger domain context")

    def log_action(
        self,
        action_type: str,
        action_name: str,
        parameters: Dict[str, Any],
        result: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        reasoning: Optional[str] = None,
        user_approval: Optional[str] = None,
        safety_level: int = 0,
        domain_context: Optional[str] = None
    ) -> str:
        """
        Log an action to the audit trail with hash chain integrity and domain context.

        Args:
            action_type: Type of action (read, write, delete, execute)
            action_name: Specific action name (e.g., "odoo_record_transaction")
            parameters: Action parameters (will be redacted)
            result: Action result (will be redacted)
            error_message: Error message if action failed
            reasoning: Agent reasoning for taking this action
            user_approval: User approval information (username, timestamp)
            safety_level: Action safety level (0-3)
            domain_context: Domain context override (uses current if None)

        Returns:
            Audit log entry ID
        """
        # Use provided domain context or current context
        effective_domain = domain_context or self.current_domain_context

        # Add domain context to parameters for logging
        if effective_domain:
            parameters = {**parameters, "_domain_context": effective_domain}

        # Generate entry ID
        entry_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat() + "Z"

        # Get previous entry hash for chain integrity
        previous_hash = self._get_last_entry_hash()

        # Get next sequence number
        sequence_number = self._get_next_sequence_number()

        # Redact PII from parameters and result
        redacted_parameters = self._redact_pii(json.dumps(parameters))
        redacted_result = self._redact_pii(json.dumps(result)) if result else None

        # Calculate entry hash
        entry_hash = self._calculate_entry_hash(
            sequence_number=sequence_number,
            timestamp=timestamp,
            action_type=action_type,
            action_name=action_name,
            parameters=redacted_parameters,
            result=redacted_result,
            previous_hash=previous_hash
        )

        # Insert audit log entry
        cursor = self.db.conn.cursor()
        cursor.execute("""
            INSERT INTO audit_log
            (id, sequence_number, timestamp, action_type, action_name, parameters,
             result, error_message, reasoning, user_approval, safety_level,
             previous_entry_hash, entry_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entry_id, sequence_number, timestamp, action_type, action_name,
            redacted_parameters, redacted_result, error_message, reasoning,
            user_approval, safety_level, previous_hash, entry_hash
        ))

        self.db.conn.commit()

        logger.info(
            f"Audit log entry created: {entry_id} (seq={sequence_number}, "
            f"action={action_name}, safety_level={safety_level}, domain={effective_domain})"
        )

        return entry_id

    def _redact_pii(self, text: str) -> str:
        """
        Redact PII from text using pattern matching.

        Args:
            text: Text to redact

        Returns:
            Redacted text with [REDACTED] placeholders
        """
        if not text:
            return text

        redacted = text

        # Redact JSON field values (passwords, keys, tokens, secrets)
        for pattern_name, pattern in self.PII_PATTERNS.items():
            if pattern_name in ["password", "api_key", "token", "secret"]:
                # For JSON fields, keep the key but redact the value
                redacted = pattern.sub(r'\1[REDACTED]\2', redacted)
            else:
                # For other patterns, replace entire match
                redacted = pattern.sub('[REDACTED]', redacted)

        return redacted

    def _get_last_entry_hash(self) -> Optional[str]:
        """
        Get the hash of the last audit log entry.

        Returns:
            Last entry hash or None if no entries exist
        """
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT entry_hash FROM audit_log
            ORDER BY sequence_number DESC
            LIMIT 1
        """)

        row = cursor.fetchone()
        return row["entry_hash"] if row else None

    def _get_next_sequence_number(self) -> int:
        """
        Get the next sequence number for audit log entries.

        Returns:
            Next sequence number (1 if no entries exist)
        """
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT MAX(sequence_number) as max_seq FROM audit_log")

        row = cursor.fetchone()
        max_seq = row["max_seq"] if row and row["max_seq"] is not None else 0

        return max_seq + 1

    def _calculate_entry_hash(
        self,
        sequence_number: int,
        timestamp: str,
        action_type: str,
        action_name: str,
        parameters: str,
        result: Optional[str],
        previous_hash: Optional[str]
    ) -> str:
        """
        Calculate SHA-256 hash for audit log entry.

        Args:
            sequence_number: Entry sequence number
            timestamp: Entry timestamp
            action_type: Action type
            action_name: Action name
            parameters: Redacted parameters JSON
            result: Redacted result JSON
            previous_hash: Hash of previous entry

        Returns:
            SHA-256 hash of entry
        """
        # Concatenate all fields for hashing
        hash_input = (
            f"{sequence_number}|"
            f"{timestamp}|"
            f"{action_type}|"
            f"{action_name}|"
            f"{parameters}|"
            f"{result or ''}|"
            f"{previous_hash or ''}"
        )

        # Calculate SHA-256 hash
        return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()

    def verify_chain_integrity(self) -> Dict[str, Any]:
        """
        Verify the integrity of the audit log hash chain.

        Returns:
            Verification result with any broken links
        """
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT * FROM audit_log
            ORDER BY sequence_number ASC
        """)

        entries = cursor.fetchall()

        if not entries:
            return {
                "valid": True,
                "total_entries": 0,
                "broken_links": []
            }

        broken_links = []
        previous_hash = None

        for entry in entries:
            # Verify previous hash matches
            if entry["previous_entry_hash"] != previous_hash:
                broken_links.append({
                    "sequence_number": entry["sequence_number"],
                    "expected_previous_hash": previous_hash,
                    "actual_previous_hash": entry["previous_entry_hash"]
                })

            # Recalculate entry hash
            calculated_hash = self._calculate_entry_hash(
                sequence_number=entry["sequence_number"],
                timestamp=entry["timestamp"],
                action_type=entry["action_type"],
                action_name=entry["action_name"],
                parameters=entry["parameters"],
                result=entry["result"],
                previous_hash=entry["previous_entry_hash"]
            )

            # Verify entry hash matches
            if calculated_hash != entry["entry_hash"]:
                broken_links.append({
                    "sequence_number": entry["sequence_number"],
                    "reason": "hash_mismatch",
                    "expected_hash": calculated_hash,
                    "actual_hash": entry["entry_hash"]
                })

            previous_hash = entry["entry_hash"]

        return {
            "valid": len(broken_links) == 0,
            "total_entries": len(entries),
            "broken_links": broken_links,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

    def get_audit_logs(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        action_type: Optional[str] = None,
        safety_level: Optional[int] = None,
        limit: int = 1000
    ) -> list:
        """
        Query audit logs with filters.

        Args:
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            action_type: Filter by action type
            safety_level: Filter by safety level
            limit: Maximum number of entries to return

        Returns:
            List of audit log entries
        """
        cursor = self.db.conn.cursor()

        query = "SELECT * FROM audit_log WHERE 1=1"
        params = []

        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)

        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date)

        if action_type:
            query += " AND action_type = ?"
            params.append(action_type)

        if safety_level is not None:
            query += " AND safety_level = ?"
            params.append(safety_level)

        query += " ORDER BY sequence_number DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)

        entries = []
        for row in cursor.fetchall():
            entries.append({
                "id": row["id"],
                "sequence_number": row["sequence_number"],
                "timestamp": row["timestamp"],
                "action_type": row["action_type"],
                "action_name": row["action_name"],
                "parameters": row["parameters"],
                "result": row["result"],
                "error_message": row["error_message"],
                "reasoning": row["reasoning"],
                "user_approval": row["user_approval"],
                "safety_level": row["safety_level"],
                "entry_hash": row["entry_hash"]
            })

        return entries
