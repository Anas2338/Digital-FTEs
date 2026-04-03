"""Unit tests for AuditLogger and hash chain integrity.

Tests audit logging, PII redaction, and hash chain verification.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from watchers.shared.audit_logger import AuditLogger
from watchers.shared.database import Database


class TestAuditLogger:
    """Test suite for AuditLogger class."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create temporary database for testing."""
        db_path = tmp_path / "test_audit.db"
        return Database(str(db_path))

    @pytest.fixture
    def audit_logger(self, db):
        """Create audit logger instance."""
        return AuditLogger(db=db)

    def test_log_action_creates_entry(self, audit_logger):
        """Test that logging an action creates an audit entry."""
        audit_logger.log_action(
            action_type="test_action",
            component="test_component",
            details={"key": "value"}
        )

        # Verify entry was created
        cursor = audit_logger.db.conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM audit_log")
        count = cursor.fetchone()[0]
        assert count == 1

    def test_sequence_numbers_increment(self, audit_logger):
        """Test that sequence numbers increment correctly."""
        audit_logger.log_action(
            action_type="action1",
            component="test",
            details={}
        )
        audit_logger.log_action(
            action_type="action2",
            component="test",
            details={}
        )

        cursor = audit_logger.db.conn.cursor()
        cursor.execute("SELECT sequence_number FROM audit_log ORDER BY sequence_number")
        sequences = [row[0] for row in cursor.fetchall()]

        assert sequences == [1, 2]

    def test_hash_chain_integrity(self, audit_logger):
        """Test that hash chain maintains integrity."""
        # Log multiple actions
        for i in range(5):
            audit_logger.log_action(
                action_type=f"action_{i}",
                component="test",
                details={"index": i}
            )

        # Verify hash chain
        assert audit_logger.verify_hash_chain() is True

    def test_hash_chain_detects_tampering(self, audit_logger):
        """Test that hash chain detects tampering."""
        # Log some actions
        for i in range(3):
            audit_logger.log_action(
                action_type=f"action_{i}",
                component="test",
                details={}
            )

        # Tamper with middle entry
        cursor = audit_logger.db.conn.cursor()
        cursor.execute("""
            UPDATE audit_log
            SET action_type = 'tampered'
            WHERE sequence_number = 2
        """)
        audit_logger.db.conn.commit()

        # Hash chain should be broken
        assert audit_logger.verify_hash_chain() is False

    def test_pii_redaction_in_parameters(self, audit_logger):
        """Test that PII is redacted from parameters."""
        audit_logger.log_action(
            action_type="send_email",
            component="email_tool",
            details={
                "recipient": "user@example.com",
                "subject": "Test",
                "body": "Hello John Doe, your SSN is 123-45-6789"
            }
        )

        cursor = audit_logger.db.conn.cursor()
        cursor.execute("SELECT parameters FROM audit_log WHERE sequence_number = 1")
        parameters = cursor.fetchone()[0]

        # Email should be redacted
        assert "user@example.com" not in parameters
        assert "[EMAIL_REDACTED]" in parameters

    def test_pii_redaction_phone_numbers(self, audit_logger):
        """Test that phone numbers are redacted."""
        audit_logger.log_action(
            action_type="send_sms",
            component="sms_tool",
            details={
                "phone": "+1234567890",
                "message": "Call me at +1-555-123-4567"
            }
        )

        cursor = audit_logger.db.conn.cursor()
        cursor.execute("SELECT parameters FROM audit_log WHERE sequence_number = 1")
        parameters = cursor.fetchone()[0]

        # Phone numbers should be redacted
        assert "+1234567890" not in parameters
        assert "+1-555-123-4567" not in parameters
        assert "[PHONE_REDACTED]" in parameters

    def test_safety_level_recorded(self, audit_logger):
        """Test that safety level is recorded correctly."""
        audit_logger.log_action(
            action_type="send_email",
            component="email_tool",
            details={},
            safety_level=2
        )

        cursor = audit_logger.db.conn.cursor()
        cursor.execute("SELECT safety_level FROM audit_log WHERE sequence_number = 1")
        safety_level = cursor.fetchone()[0]

        assert safety_level == 2

    def test_user_approval_recorded(self, audit_logger):
        """Test that user approval is recorded."""
        audit_logger.log_action(
            action_type="financial_transaction",
            component="banking_tool",
            details={"amount": 1000},
            safety_level=3,
            user_approval="approved_by_user"
        )

        cursor = audit_logger.db.conn.cursor()
        cursor.execute("SELECT user_approval FROM audit_log WHERE sequence_number = 1")
        approval = cursor.fetchone()[0]

        assert approval == "approved_by_user"

    def test_error_logging(self, audit_logger):
        """Test that errors are logged correctly."""
        audit_logger.log_action(
            action_type="api_call",
            component="external_api",
            details={},
            error_message="Connection timeout"
        )

        cursor = audit_logger.db.conn.cursor()
        cursor.execute("SELECT error_message FROM audit_log WHERE sequence_number = 1")
        error = cursor.fetchone()[0]

        assert error == "Connection timeout"

    def test_reasoning_recorded(self, audit_logger):
        """Test that reasoning is recorded."""
        audit_logger.log_action(
            action_type="autonomous_decision",
            component="ralph_loop",
            details={},
            reasoning="User requested financial report, querying transactions from last month"
        )

        cursor = audit_logger.db.conn.cursor()
        cursor.execute("SELECT reasoning FROM audit_log WHERE sequence_number = 1")
        reasoning = cursor.fetchone()[0]

        assert "financial report" in reasoning

    def test_get_recent_entries(self, audit_logger):
        """Test retrieving recent audit entries."""
        # Log multiple actions
        for i in range(10):
            audit_logger.log_action(
                action_type=f"action_{i}",
                component="test",
                details={}
            )

        # Get last 5 entries
        recent = audit_logger.get_recent_entries(limit=5)

        assert len(recent) == 5
        assert recent[0]["sequence_number"] == 10
        assert recent[4]["sequence_number"] == 6

    def test_get_entries_by_action_type(self, audit_logger):
        """Test filtering entries by action type."""
        audit_logger.log_action(action_type="email_sent", component="test", details={})
        audit_logger.log_action(action_type="post_created", component="test", details={})
        audit_logger.log_action(action_type="email_sent", component="test", details={})

        entries = audit_logger.get_entries_by_action_type("email_sent")

        assert len(entries) == 2
        assert all(e["action_type"] == "email_sent" for e in entries)

    def test_timestamp_format(self, audit_logger):
        """Test that timestamps are in ISO 8601 format."""
        audit_logger.log_action(
            action_type="test",
            component="test",
            details={}
        )

        cursor = audit_logger.db.conn.cursor()
        cursor.execute("SELECT timestamp FROM audit_log WHERE sequence_number = 1")
        timestamp = cursor.fetchone()[0]

        # Should be parseable as ISO 8601
        parsed = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        assert isinstance(parsed, datetime)
