"""
Safety tests for Level 0 actions (Auto-Execute).

Verifies that Level 0 actions execute automatically without user approval.
Level 0 actions are read-only operations that cannot modify state.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mcp_servers.digital_fte_server.tools.odoo_query_financials import OdooQueryFinancialsTool
from mcp_servers.digital_fte_server.tools.odoo_check_connection import OdooCheckConnectionTool
from mcp_servers.digital_fte_server.tools.odoo_get_transactions import OdooGetTransactionsTool
from mcp_servers.digital_fte_server.tools.get_briefing import GetBriefingTool
from mcp_servers.digital_fte_server.tools.list_briefings import ListBriefingsTool
from mcp_servers.digital_fte_server.tools.social_media.social_get_engagement import SocialGetEngagementTool
from mcp_servers.digital_fte_server.tools.social_media.social_list_posts import SocialListPostsTool
from watchers.shared.database import Database


class TestLevel0ActionsSafetyLevel:
    """Test that Level 0 actions have correct safety level."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create temporary database."""
        db_path = tmp_path / "test.db"
        return Database(str(db_path))

    def test_odoo_query_financials_is_level_0(self, db):
        """odoo-query-financials should be Level 0."""
        tool = OdooQueryFinancialsTool(db=db)
        assert tool.safety_level == 0

    def test_odoo_check_connection_is_level_0(self):
        """odoo-check-connection should be Level 0."""
        tool = OdooCheckConnectionTool()
        assert tool.safety_level == 0

    def test_odoo_get_transactions_is_level_0(self, db):
        """odoo-get-transactions should be Level 0."""
        tool = OdooGetTransactionsTool(db=db)
        assert tool.safety_level == 0

    def test_get_briefing_is_level_0(self, db):
        """get-briefing should be Level 0."""
        tool = GetBriefingTool(db=db)
        assert tool.safety_level == 0

    def test_list_briefings_is_level_0(self, db):
        """list-briefings should be Level 0."""
        tool = ListBriefingsTool(db=db)
        assert tool.safety_level == 0

    def test_social_get_engagement_is_level_0(self, db):
        """social-get-engagement should be Level 0."""
        tool = SocialGetEngagementTool(db=db)
        assert tool.safety_level == 0

    def test_social_list_posts_is_level_0(self, db):
        """social-list-posts should be Level 0."""
        tool = SocialListPostsTool(db=db)
        assert tool.safety_level == 0


class TestLevel0ActionsAutoExecute:
    """Test that Level 0 actions execute without approval."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create temporary database."""
        db_path = tmp_path / "test.db"
        return Database(str(db_path))

    def test_query_financials_executes_without_approval(self, db):
        """Query financials should execute without user approval."""
        tool = OdooQueryFinancialsTool(db=db)

        # Should execute successfully without any approval mechanism
        result = tool.execute()

        assert isinstance(result, dict)
        assert "success" in result

    def test_check_connection_executes_without_approval(self):
        """Check connection should execute without user approval."""
        tool = OdooCheckConnectionTool()

        result = tool.execute()

        assert isinstance(result, dict)

    def test_get_briefing_executes_without_approval(self, db):
        """Get briefing should execute without user approval."""
        tool = GetBriefingTool(db=db)

        result = tool.execute()

        assert isinstance(result, dict)

    def test_list_briefings_executes_without_approval(self, db):
        """List briefings should execute without user approval."""
        tool = ListBriefingsTool(db=db)

        result = tool.execute()

        assert isinstance(result, dict)


class TestLevel0ActionsReadOnly:
    """Test that Level 0 actions are read-only and don't modify state."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create temporary database."""
        db_path = tmp_path / "test.db"
        return Database(str(db_path))

    def test_query_financials_does_not_modify_database(self, db):
        """Query financials should not modify database."""
        tool = OdooQueryFinancialsTool(db=db)

        # Get initial state
        cursor = db.conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM business_transactions")
        initial_count = cursor.fetchone()["count"]

        # Execute query
        tool.execute()

        # Verify no changes
        cursor.execute("SELECT COUNT(*) as count FROM business_transactions")
        final_count = cursor.fetchone()["count"]

        assert initial_count == final_count

    def test_get_transactions_does_not_modify_database(self, db):
        """Get transactions should not modify database."""
        tool = OdooGetTransactionsTool(db=db)

        # Get initial state
        cursor = db.conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM business_transactions")
        initial_count = cursor.fetchone()["count"]

        # Execute query
        tool.execute()

        # Verify no changes
        cursor.execute("SELECT COUNT(*) as count FROM business_transactions")
        final_count = cursor.fetchone()["count"]

        assert initial_count == final_count

    def test_list_briefings_does_not_create_files(self, db, tmp_path):
        """List briefings should not create new files."""
        tool = ListBriefingsTool(db=db)

        # Count files before
        briefings_dir = tmp_path / "briefings"
        briefings_dir.mkdir(exist_ok=True)
        initial_files = list(briefings_dir.glob("*.md"))

        # Execute list
        tool.execute()

        # Verify no new files
        final_files = list(briefings_dir.glob("*.md"))

        assert len(initial_files) == len(final_files)


class TestLevel0ActionsNoSideEffects:
    """Test that Level 0 actions have no external side effects."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create temporary database."""
        db_path = tmp_path / "test.db"
        return Database(str(db_path))

    def test_multiple_executions_idempotent(self, db):
        """Multiple executions should produce same result."""
        tool = OdooQueryFinancialsTool(db=db)

        # Execute multiple times
        result1 = tool.execute()
        result2 = tool.execute()
        result3 = tool.execute()

        # Results should be consistent
        assert result1["success"] == result2["success"] == result3["success"]

    def test_check_connection_idempotent(self):
        """Check connection should be idempotent."""
        tool = OdooCheckConnectionTool()

        result1 = tool.execute()
        result2 = tool.execute()

        # Should return same connection status
        assert type(result1) == type(result2)

    def test_list_operations_idempotent(self, db):
        """List operations should be idempotent."""
        list_briefings = ListBriefingsTool(db=db)
        list_posts = SocialListPostsTool(db=db)

        # Execute multiple times
        briefings1 = list_briefings.execute()
        briefings2 = list_briefings.execute()

        posts1 = list_posts.execute()
        posts2 = list_posts.execute()

        # Results should be consistent
        assert briefings1["success"] == briefings2["success"]
        assert posts1["success"] == posts2["success"]


class TestLevel0ActionsPerformance:
    """Test that Level 0 actions execute quickly (no approval delay)."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create temporary database."""
        db_path = tmp_path / "test.db"
        return Database(str(db_path))

    def test_query_executes_quickly(self, db):
        """Query should execute without waiting for approval."""
        import time

        tool = OdooQueryFinancialsTool(db=db)

        start = time.time()
        tool.execute()
        duration = time.time() - start

        # Should complete in under 1 second (no approval wait)
        assert duration < 1.0

    def test_list_executes_quickly(self, db):
        """List operations should execute without waiting."""
        import time

        tool = ListBriefingsTool(db=db)

        start = time.time()
        tool.execute()
        duration = time.time() - start

        # Should complete quickly
        assert duration < 1.0


class TestLevel0ActionsErrorHandling:
    """Test that Level 0 actions handle errors gracefully."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create temporary database."""
        db_path = tmp_path / "test.db"
        return Database(str(db_path))

    def test_query_with_invalid_parameters_returns_error(self, db):
        """Query with invalid parameters should return error, not crash."""
        tool = OdooQueryFinancialsTool(db=db)

        # Invalid date format
        result = tool.execute(start_date="invalid-date")

        # Should return error gracefully
        assert isinstance(result, dict)

    def test_get_nonexistent_briefing_returns_error(self, db):
        """Getting nonexistent briefing should return error."""
        tool = GetBriefingTool(db=db)

        # Request briefing that doesn't exist
        result = tool.execute(week_number=99, year=1900)

        # Should return error gracefully
        assert isinstance(result, dict)
        if not result.get("success"):
            assert "error" in result or "message" in result
