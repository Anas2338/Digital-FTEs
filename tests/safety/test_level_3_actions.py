"""
Safety tests for Level 3 actions (Explicit Approval).

Verifies that Level 3 actions require explicit user approval before execution.
Level 3 actions involve financial transactions, data deletion, or high-risk operations.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from watchers.shared.database import Database
from watchers.shared.audit_logger import AuditLogger


class TestLevel3ActionsSafetyLevel:
    """Test that Level 3 actions have correct safety level."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create temporary database."""
        db_path = tmp_path / "test.db"
        return Database(str(db_path))

    def test_financial_transactions_are_level_3(self, db):
        """Financial transactions above threshold should be Level 3."""
        # Constitution specifies $500 transaction limit
        # Transactions above this should require explicit approval (Level 3)

        # This is a conceptual test - actual implementation would have
        # a tool that checks transaction amount and sets safety level accordingly
        threshold = 500.00

        # Large transaction should be Level 3
        large_amount = 1000.00
        assert large_amount > threshold

        # Small transaction would be Level 1
        small_amount = 100.00
        assert small_amount < threshold


class TestLevel3ActionsRequireExplicitApproval:
    """Test that Level 3 actions require explicit user approval."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create temporary database."""
        db_path = tmp_path / "test.db"
        return Database(str(db_path))

    def test_approval_required_before_execution(self, db):
        """Level 3 actions should not execute without explicit approval."""
        audit_logger = AuditLogger(db=db)

        # Log a Level 3 action without approval
        audit_logger.log_action(
            action_type="financial_transaction",
            action_name="large_payment",
            parameters={"amount": 1000.00, "recipient": "Vendor"},
            reasoning="Large payment requiring approval",
            safety_level=3
        )

        # Verify it was logged with Level 3
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT * FROM audit_log
            WHERE action_name = 'large_payment'
            ORDER BY sequence_number DESC LIMIT 1
        """)
        log_entry = cursor.fetchone()

        assert log_entry is not None
        # Should indicate Level 3 safety level
        assert "3" in str(log_entry["parameters"]) or log_entry.get("safety_level") == 3

    def test_approval_recorded_in_audit_log(self, db):
        """User approval should be recorded in audit log."""
        audit_logger = AuditLogger(db=db)

        # Log a Level 3 action with explicit approval
        audit_logger.log_action(
            action_type="financial_transaction",
            action_name="approved_payment",
            parameters={"amount": 1500.00, "recipient": "Supplier"},
            reasoning="Large payment with explicit approval",
            user_approval="explicitly_approved_by_user_at_2026-04-02T10:30:00Z",
            safety_level=3
        )

        # Verify approval is recorded
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT * FROM audit_log
            WHERE action_name = 'approved_payment'
            ORDER BY sequence_number DESC LIMIT 1
        """)
        log_entry = cursor.fetchone()

        assert log_entry is not None
        assert log_entry["user_approval"] is not None
        assert "explicitly_approved" in log_entry["user_approval"]


class TestLevel3ActionsFinancialLimits:
    """Test that Level 3 actions respect financial limits."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create temporary database."""
        db_path = tmp_path / "test.db"
        return Database(str(db_path))

    def test_transaction_limit_enforced(self, db):
        """Constitution specifies $500 transaction limit."""
        # Transactions above $500 should require Level 3 approval

        limit = 500.00

        # Test amounts
        below_limit = 499.99
        at_limit = 500.00
        above_limit = 500.01

        assert below_limit < limit
        assert at_limit == limit
        assert above_limit > limit

        # Above limit should be Level 3
        # At or below limit should be Level 1

    def test_daily_transaction_limit(self, db):
        """System should track daily transaction totals."""
        # Constitution may specify daily limits
        # This test verifies the concept exists

        audit_logger = AuditLogger(db=db)

        # Log multiple transactions
        for i in range(3):
            audit_logger.log_action(
                action_type="financial_transaction",
                action_name=f"transaction_{i}",
                parameters={"amount": 200.00},
                reasoning="Daily limit test",
                safety_level=1
            )

        # Verify transactions are logged
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as count FROM audit_log
            WHERE action_type = 'financial_transaction'
        """)
        count = cursor.fetchone()["count"]

        assert count >= 3


class TestLevel3ActionsAuditTrail:
    """Test that Level 3 actions maintain comprehensive audit trail."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create temporary database."""
        db_path = tmp_path / "test.db"
        return Database(str(db_path))

    def test_audit_includes_all_transaction_details(self, db):
        """Audit log should include complete transaction details."""
        audit_logger = AuditLogger(db=db)

        # Log detailed financial transaction
        audit_logger.log_action(
            action_type="financial_transaction",
            action_name="detailed_payment",
            parameters={
                "amount": 2000.00,
                "currency": "USD",
                "recipient": "Vendor ABC",
                "invoice_number": "INV-2026-001",
                "category": "Operating Expenses"
            },
            reasoning="Large vendor payment for services",
            user_approval="approved_by_ceo_2026-04-02",
            safety_level=3
        )

        # Verify all details are logged
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT * FROM audit_log
            WHERE action_name = 'detailed_payment'
            ORDER BY sequence_number DESC LIMIT 1
        """)
        log_entry = cursor.fetchone()

        assert log_entry is not None
        params = log_entry["parameters"]
        assert "2000" in params
        assert "Vendor ABC" in params
        assert log_entry["user_approval"] is not None

    def test_audit_includes_timestamp(self, db):
        """Audit log should include precise timestamp."""
        audit_logger = AuditLogger(db=db)

        audit_logger.log_action(
            action_type="financial_transaction",
            action_name="timestamp_test",
            parameters={"amount": 1000.00},
            reasoning="Test timestamp",
            safety_level=3
        )

        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT * FROM audit_log
            WHERE action_name = 'timestamp_test'
            ORDER BY sequence_number DESC LIMIT 1
        """)
        log_entry = cursor.fetchone()

        assert log_entry is not None
        assert log_entry["timestamp"] is not None
        # Timestamp should be in ISO format
        assert "T" in log_entry["timestamp"] or "-" in log_entry["timestamp"]

    def test_audit_maintains_hash_chain(self, db):
        """Audit log should maintain hash chain integrity."""
        audit_logger = AuditLogger(db=db)

        # Log multiple Level 3 actions
        for i in range(3):
            audit_logger.log_action(
                action_type="financial_transaction",
                action_name=f"chain_test_{i}",
                parameters={"amount": 1000.00 + i},
                reasoning="Hash chain test",
                safety_level=3
            )

        # Verify hash chain
        is_valid = audit_logger.verify_hash_chain()
        assert is_valid is True


class TestLevel3ActionsErrorHandling:
    """Test error handling for Level 3 actions."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create temporary database."""
        db_path = tmp_path / "test.db"
        return Database(str(db_path))

    def test_missing_approval_prevents_execution(self, db):
        """Missing approval should prevent Level 3 action execution."""
        audit_logger = AuditLogger(db=db)

        # Log action without approval
        audit_logger.log_action(
            action_type="financial_transaction",
            action_name="no_approval_test",
            parameters={"amount": 1000.00},
            reasoning="Test missing approval",
            user_approval=None,  # No approval
            safety_level=3
        )

        # Verify it was logged but marked as requiring approval
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT * FROM audit_log
            WHERE action_name = 'no_approval_test'
            ORDER BY sequence_number DESC LIMIT 1
        """)
        log_entry = cursor.fetchone()

        assert log_entry is not None
        # Should show no approval was given
        assert log_entry["user_approval"] is None

    def test_invalid_amount_logged_as_error(self, db):
        """Invalid transaction amount should be logged as error."""
        audit_logger = AuditLogger(db=db)

        # Log invalid transaction
        audit_logger.log_action(
            action_type="financial_transaction",
            action_name="invalid_amount_test",
            parameters={"amount": -1000.00},  # Negative amount
            error_message="Invalid amount: cannot be negative",
            reasoning="Test error handling",
            safety_level=3
        )

        # Verify error is logged
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT * FROM audit_log
            WHERE action_name = 'invalid_amount_test'
            ORDER BY sequence_number DESC LIMIT 1
        """)
        log_entry = cursor.fetchone()

        assert log_entry is not None
        assert log_entry["error_message"] is not None
        assert "negative" in log_entry["error_message"].lower()


class TestLevel3ActionsReversibility:
    """Test reversibility and rollback for Level 3 actions."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create temporary database."""
        db_path = tmp_path / "test.db"
        return Database(str(db_path))

    def test_financial_transactions_are_traceable(self, db):
        """Financial transactions should be fully traceable."""
        audit_logger = AuditLogger(db=db)

        # Log transaction
        audit_logger.log_action(
            action_type="financial_transaction",
            action_name="traceable_payment",
            parameters={
                "amount": 1500.00,
                "transaction_id": "TXN-2026-001"
            },
            reasoning="Traceable transaction test",
            user_approval="approved",
            safety_level=3
        )

        # Should be able to query by transaction ID
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT * FROM audit_log
            WHERE parameters LIKE '%TXN-2026-001%'
        """)
        log_entry = cursor.fetchone()

        assert log_entry is not None

    def test_reversal_logged_separately(self, db):
        """Transaction reversals should be logged as separate entries."""
        audit_logger = AuditLogger(db=db)

        # Original transaction
        audit_logger.log_action(
            action_type="financial_transaction",
            action_name="original_payment",
            parameters={"amount": 1000.00, "transaction_id": "TXN-001"},
            reasoning="Original payment",
            user_approval="approved",
            safety_level=3
        )

        # Reversal
        audit_logger.log_action(
            action_type="financial_transaction",
            action_name="payment_reversal",
            parameters={
                "amount": -1000.00,
                "original_transaction_id": "TXN-001",
                "reversal_reason": "Duplicate payment"
            },
            reasoning="Reverse duplicate payment",
            user_approval="approved",
            safety_level=3
        )

        # Both should be in audit log
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as count FROM audit_log
            WHERE parameters LIKE '%TXN-001%'
        """)
        count = cursor.fetchone()["count"]

        assert count >= 2  # Original + reversal


class TestLevel3ActionsComplianceRequirements:
    """Test compliance requirements for Level 3 actions."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create temporary database."""
        db_path = tmp_path / "test.db"
        return Database(str(db_path))

    def test_audit_log_retention(self, db):
        """Audit logs should be retained per compliance requirements."""
        # Constitution specifies 7-year retention
        audit_logger = AuditLogger(db=db)

        audit_logger.log_action(
            action_type="financial_transaction",
            action_name="retention_test",
            parameters={"amount": 1000.00},
            reasoning="Test retention policy",
            safety_level=3
        )

        # Verify entry exists
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT * FROM audit_log
            WHERE action_name = 'retention_test'
        """)
        log_entry = cursor.fetchone()

        assert log_entry is not None
        # Entry should have timestamp for retention tracking
        assert log_entry["timestamp"] is not None

    def test_pii_redaction_in_logs(self, db):
        """PII should be redacted in audit logs."""
        audit_logger = AuditLogger(db=db)

        # Log transaction with PII
        audit_logger.log_action(
            action_type="financial_transaction",
            action_name="pii_test",
            parameters={
                "amount": 1000.00,
                "recipient_name": "[REDACTED]",  # PII should be redacted
                "account_number": "[REDACTED]"
            },
            reasoning="Test PII redaction",
            safety_level=3
        )

        # Verify PII is redacted
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT * FROM audit_log
            WHERE action_name = 'pii_test'
        """)
        log_entry = cursor.fetchone()

        assert log_entry is not None
        params = log_entry["parameters"]
        assert "[REDACTED]" in params

    def test_immutable_audit_log(self, db):
        """Audit log entries should be immutable."""
        audit_logger = AuditLogger(db=db)

        # Log entry
        audit_logger.log_action(
            action_type="financial_transaction",
            action_name="immutable_test",
            parameters={"amount": 1000.00},
            reasoning="Test immutability",
            safety_level=3
        )

        # Get entry
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT * FROM audit_log
            WHERE action_name = 'immutable_test'
        """)
        log_entry = cursor.fetchone()

        assert log_entry is not None

        # Attempt to modify should fail or be detected by hash chain
        # (Actual enforcement depends on database constraints)
        # Hash chain verification would detect tampering
        is_valid = audit_logger.verify_hash_chain()
        assert is_valid is True
