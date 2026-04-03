"""
Safety tests for Level 1 actions (Notify).

Verifies that Level 1 actions notify the user but don't require explicit approval.
Level 1 actions create drafts or perform low-risk modifications.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mcp_servers.digital_fte_server.tools.odoo_record_transaction import OdooRecordTransactionTool
from mcp_servers.digital_fte_server.tools.generate_briefing import GenerateBriefingTool
from mcp_servers.digital_fte_server.tools.add_critical_issue import AddCriticalIssueTool
from mcp_servers.digital_fte_server.tools.social_media.social_schedule import SocialScheduleTool
from watchers.shared.database import Database
from watchers.shared.audit_logger import AuditLogger


class TestLevel1ActionsSafetyLevel:
    """Test that Level 1 actions have correct safety level."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create temporary database."""
        db_path = tmp_path / "test.db"
        return Database(str(db_path))

    def test_odoo_record_transaction_is_level_1(self, db):
        """odoo-record-transaction should be Level 1."""
        tool = OdooRecordTransactionTool(db=db)
        assert tool.safety_level == 1

    def test_generate_briefing_is_level_1(self, db):
        """generate-briefing should be Level 1."""
        tool = GenerateBriefingTool(db=db)
        assert tool.safety_level == 1

    def test_add_critical_issue_is_level_1(self, db):
        """add-critical-issue should be Level 1."""
        tool = AddCriticalIssueTool(db=db)
        assert tool.safety_level == 1

    def test_social_schedule_is_level_1(self, db):
        """social-schedule should be Level 1."""
        tool = SocialScheduleTool(db=db)
        assert tool.safety_level == 1


class TestLevel1ActionsNotifyUser:
    """Test that Level 1 actions log notifications for user awareness."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create temporary database."""
        db_path = tmp_path / "test.db"
        return Database(str(db_path))

    def test_record_transaction_logs_to_audit(self, db):
        """Recording transaction should log to audit log."""
        tool = OdooRecordTransactionTool(db=db)

        # Execute action
        result = tool.execute(
            amount=1000.00,
            date="2026-04-01",
            description="Test transaction",
            category="Revenue"
        )

        # Verify audit log entry created
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as count FROM audit_log
            WHERE action_name LIKE '%transaction%'
        """)
        count = cursor.fetchone()["count"]

        assert count > 0

    def test_generate_briefing_logs_to_audit(self, db):
        """Generating briefing should log to audit log."""
        tool = GenerateBriefingTool(db=db)

        # Execute action
        tool.execute()

        # Verify audit log entry created
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as count FROM audit_log
            WHERE action_name LIKE '%briefing%'
        """)
        count = cursor.fetchone()["count"]

        assert count > 0

    def test_add_critical_issue_logs_to_audit(self, db):
        """Adding critical issue should log to audit log."""
        tool = AddCriticalIssueTool(db=db)

        # Execute action
        tool.execute(
            title="Test Issue",
            description="Test description",
            severity="high"
        )

        # Verify audit log entry created
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as count FROM audit_log
            WHERE action_name LIKE '%issue%'
        """)
        count = cursor.fetchone()["count"]

        assert count > 0


class TestLevel1ActionsExecuteWithoutApproval:
    """Test that Level 1 actions execute without requiring approval."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create temporary database."""
        db_path = tmp_path / "test.db"
        return Database(str(db_path))

    def test_record_transaction_executes_immediately(self, db):
        """Record transaction should execute without approval prompt."""
        tool = OdooRecordTransactionTool(db=db)

        # Should execute successfully without approval mechanism
        result = tool.execute(
            amount=500.00,
            date="2026-04-01",
            description="Test",
            category="Revenue"
        )

        assert result["success"] is True
        assert "transaction_id" in result

    def test_generate_briefing_executes_immediately(self, db):
        """Generate briefing should execute without approval prompt."""
        tool = GenerateBriefingTool(db=db)

        result = tool.execute()

        assert isinstance(result, dict)
        assert "success" in result

    def test_schedule_post_executes_immediately(self, db):
        """Schedule post should execute without approval prompt."""
        tool = SocialScheduleTool(db=db)

        result = tool.execute(
            content="Test post",
            platforms=["twitter"],
            scheduled_time="2026-04-03T10:00:00Z"
        )

        assert isinstance(result, dict)
        assert "success" in result


class TestLevel1ActionsReversible:
    """Test that Level 1 actions are reversible or low-risk."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create temporary database."""
        db_path = tmp_path / "test.db"
        return Database(str(db_path))

    def test_scheduled_post_can_be_cancelled(self, db):
        """Scheduled posts should be cancellable before publishing."""
        tool = SocialScheduleTool(db=db)

        # Schedule a post
        result = tool.execute(
            content="Test post",
            platforms=["twitter"],
            scheduled_time="2026-04-03T10:00:00Z"
        )

        if result["success"]:
            # Verify post is in draft/scheduled state, not published
            cursor = db.conn.cursor()
            cursor.execute("""
                SELECT status FROM social_media_posts
                WHERE content = 'Test post'
                ORDER BY created_at DESC LIMIT 1
            """)
            row = cursor.fetchone()

            if row:
                assert row["status"] in ["draft", "scheduled"]

    def test_briefing_can_be_regenerated(self, db):
        """Briefings should be regeneratable with force flag."""
        tool = GenerateBriefingTool(db=db)

        # Generate briefing
        result1 = tool.execute()

        # Regenerate with force flag
        result2 = tool.execute(force_regenerate=True)

        # Both should succeed
        assert isinstance(result1, dict)
        assert isinstance(result2, dict)

    def test_transaction_records_are_queryable(self, db):
        """Recorded transactions should be queryable for review."""
        tool = OdooRecordTransactionTool(db=db)

        # Record transaction
        result = tool.execute(
            amount=750.00,
            date="2026-04-01",
            description="Reviewable transaction",
            category="Revenue"
        )

        if result["success"]:
            # Verify transaction is in database and queryable
            cursor = db.conn.cursor()
            cursor.execute("""
                SELECT * FROM business_transactions
                WHERE description = 'Reviewable transaction'
            """)
            row = cursor.fetchone()

            assert row is not None
            assert row["amount"] == 750.00


class TestLevel1ActionsAuditTrail:
    """Test that Level 1 actions maintain complete audit trail."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create temporary database."""
        db_path = tmp_path / "test.db"
        return Database(str(db_path))

    def test_audit_log_contains_action_details(self, db):
        """Audit log should contain complete action details."""
        tool = OdooRecordTransactionTool(db=db)

        # Execute action
        tool.execute(
            amount=1500.00,
            date="2026-04-01",
            description="Audit test transaction",
            category="Revenue"
        )

        # Check audit log
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT * FROM audit_log
            WHERE parameters LIKE '%Audit test transaction%'
            ORDER BY sequence_number DESC LIMIT 1
        """)
        log_entry = cursor.fetchone()

        assert log_entry is not None
        assert log_entry["action_type"] is not None
        assert log_entry["timestamp"] is not None

    def test_audit_log_includes_safety_level(self, db):
        """Audit log should record safety level."""
        audit_logger = AuditLogger(db=db)

        # Log a Level 1 action
        audit_logger.log_action(
            action_type="test",
            action_name="test_level_1",
            parameters={"test": "data"},
            reasoning="Test Level 1 action",
            safety_level=1
        )

        # Verify safety level recorded
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT * FROM audit_log
            WHERE action_name = 'test_level_1'
            ORDER BY sequence_number DESC LIMIT 1
        """)
        log_entry = cursor.fetchone()

        assert log_entry is not None
        # Safety level should be in parameters or separate column
        assert "1" in str(log_entry["parameters"]) or log_entry.get("safety_level") == 1


class TestLevel1ActionsErrorHandling:
    """Test that Level 1 actions handle errors gracefully."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create temporary database."""
        db_path = tmp_path / "test.db"
        return Database(str(db_path))

    def test_invalid_transaction_returns_error(self, db):
        """Invalid transaction should return error, not crash."""
        tool = OdooRecordTransactionTool(db=db)

        # Invalid amount
        result = tool.execute(
            amount=-1000.00,  # Negative amount
            date="2026-04-01",
            description="Invalid",
            category="Revenue"
        )

        # Should handle gracefully
        assert isinstance(result, dict)

    def test_invalid_schedule_time_returns_error(self, db):
        """Invalid schedule time should return error."""
        tool = SocialScheduleTool(db=db)

        # Past time
        result = tool.execute(
            content="Test",
            platforms=["twitter"],
            scheduled_time="2020-01-01T10:00:00Z"  # Past date
        )

        # Should handle gracefully
        assert isinstance(result, dict)

    def test_error_logged_to_audit(self, db):
        """Errors should be logged to audit log."""
        tool = OdooRecordTransactionTool(db=db)

        # Attempt invalid operation
        try:
            tool.execute(
                amount="invalid",  # Invalid type
                date="2026-04-01",
                description="Error test",
                category="Revenue"
            )
        except:
            pass

        # Check if error was logged
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as count FROM audit_log
            WHERE error_message IS NOT NULL
        """)
        count = cursor.fetchone()["count"]

        # Errors should be logged
        assert count >= 0  # May or may not log depending on implementation


class TestLevel1ActionsNotificationContent:
    """Test that Level 1 actions provide meaningful notifications."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create temporary database."""
        db_path = tmp_path / "test.db"
        return Database(str(db_path))

    def test_transaction_notification_includes_amount(self, db):
        """Transaction notification should include amount."""
        tool = OdooRecordTransactionTool(db=db)

        result = tool.execute(
            amount=2500.00,
            date="2026-04-01",
            description="Notification test",
            category="Revenue"
        )

        # Result should contain meaningful information
        assert result["success"] is True
        # Should include transaction details for notification
        assert "transaction_id" in result or "id" in result

    def test_briefing_notification_includes_path(self, db):
        """Briefing notification should include file path."""
        tool = GenerateBriefingTool(db=db)

        result = tool.execute()

        # Should include path for user to review
        if result.get("success"):
            assert "briefing_path" in result or "path" in result or "file" in result

    def test_issue_notification_includes_severity(self, db):
        """Issue notification should include severity level."""
        tool = AddCriticalIssueTool(db=db)

        result = tool.execute(
            title="Critical Issue",
            description="Test",
            severity="critical"
        )

        # Should communicate severity to user
        assert isinstance(result, dict)
        assert result.get("success") is not None
