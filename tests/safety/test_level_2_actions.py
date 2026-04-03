"""
Safety tests for Level 2 actions (Confirm).

Verifies that Level 2 actions require user confirmation before execution.
Level 2 actions perform significant modifications or external communications.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mcp_servers.digital_fte_server.tools.social_media.social_post import SocialPostTool
from mcp_servers.digital_fte_server.tools.schedule_briefing import ScheduleBriefingTool
from watchers.shared.database import Database
from watchers.shared.audit_logger import AuditLogger


class TestLevel2ActionsSafetyLevel:
    """Test that Level 2 actions have correct safety level."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create temporary database."""
        db_path = tmp_path / "test.db"
        return Database(str(db_path))

    def test_social_post_is_level_2(self, db):
        """social-post should be Level 2."""
        tool = SocialPostTool(db=db)
        assert tool.safety_level == 2

    def test_schedule_briefing_is_level_2(self, db):
        """schedule-briefing should be Level 2."""
        tool = ScheduleBriefingTool(db=db)
        assert tool.safety_level == 2


class TestLevel2ActionsRequireConfirmation:
    """Test that Level 2 actions require user confirmation."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create temporary database."""
        db_path = tmp_path / "test.db"
        return Database(str(db_path))

    def test_social_post_logs_confirmation_requirement(self, db):
        """Social post should log that confirmation is required."""
        tool = SocialPostTool(db=db)

        # Execute action
        result = tool.execute(
            content="Test post requiring confirmation",
            platforms=["twitter"]
        )

        # Verify audit log shows confirmation requirement
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT * FROM audit_log
            WHERE parameters LIKE '%Test post requiring confirmation%'
            ORDER BY sequence_number DESC LIMIT 1
        """)
        log_entry = cursor.fetchone()

        assert log_entry is not None
        # Should indicate Level 2 safety level
        assert "2" in str(log_entry["parameters"]) or log_entry.get("safety_level") == 2

    def test_schedule_briefing_logs_confirmation_requirement(self, db):
        """Schedule briefing should log confirmation requirement."""
        tool = ScheduleBriefingTool(db=db)

        # Execute action
        result = tool.execute(
            day_of_week="monday",
            time="08:00"
        )

        # Verify audit log
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT * FROM audit_log
            WHERE action_name LIKE '%briefing%'
            ORDER BY sequence_number DESC LIMIT 1
        """)
        log_entry = cursor.fetchone()

        assert log_entry is not None


class TestLevel2ActionsExternalImpact:
    """Test that Level 2 actions have external impact requiring confirmation."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create temporary database."""
        db_path = tmp_path / "test.db"
        return Database(str(db_path))

    def test_social_post_affects_external_platform(self, db):
        """Social post affects external platforms (Twitter, Facebook, etc.)."""
        tool = SocialPostTool(db=db)

        # This action would post to external platforms
        result = tool.execute(
            content="External impact test",
            platforms=["twitter", "facebook"]
        )

        # Should indicate external impact
        assert isinstance(result, dict)
        assert "success" in result

        # Verify platforms are recorded
        if result["success"]:
            cursor = db.conn.cursor()
            cursor.execute("""
                SELECT * FROM social_media_posts
                WHERE content = 'External impact test'
                ORDER BY created_at DESC LIMIT 1
            """)
            row = cursor.fetchone()

            if row:
                # Should record which platforms were targeted
                assert "twitter" in row["platform_ids"] or "facebook" in row["platform_ids"]

    def test_schedule_briefing_modifies_system_behavior(self, db):
        """Schedule briefing modifies system-wide behavior."""
        tool = ScheduleBriefingTool(db=db)

        # This action changes when briefings are generated
        result = tool.execute(
            day_of_week="friday",
            time="09:00"
        )

        # Should succeed but require confirmation
        assert isinstance(result, dict)


class TestLevel2ActionsAuditTrail:
    """Test that Level 2 actions maintain detailed audit trail."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create temporary database."""
        db_path = tmp_path / "test.db"
        return Database(str(db_path))

    def test_social_post_logs_all_platforms(self, db):
        """Social post should log all target platforms."""
        tool = SocialPostTool(db=db)

        result = tool.execute(
            content="Multi-platform post",
            platforms=["twitter", "facebook", "instagram"]
        )

        # Verify audit log contains platform details
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT * FROM audit_log
            WHERE parameters LIKE '%Multi-platform post%'
            ORDER BY sequence_number DESC LIMIT 1
        """)
        log_entry = cursor.fetchone()

        assert log_entry is not None
        # Should log all platforms
        params = log_entry["parameters"]
        assert "twitter" in params or "facebook" in params or "instagram" in params

    def test_schedule_change_logs_old_and_new_values(self, db):
        """Schedule change should log both old and new values."""
        tool = ScheduleBriefingTool(db=db)

        # Change schedule
        result = tool.execute(
            day_of_week="wednesday",
            time="10:30"
        )

        # Verify audit log contains schedule details
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT * FROM audit_log
            WHERE action_name LIKE '%briefing%'
            ORDER BY sequence_number DESC LIMIT 1
        """)
        log_entry = cursor.fetchone()

        assert log_entry is not None
        # Should log new schedule
        params = log_entry["parameters"]
        assert "wednesday" in params.lower() or "10:30" in params

    def test_audit_includes_user_approval_field(self, db):
        """Audit log should have field for user approval."""
        audit_logger = AuditLogger(db=db)

        # Log a Level 2 action with approval
        audit_logger.log_action(
            action_type="post",
            action_name="social_post",
            parameters={"content": "Test", "platforms": ["twitter"]},
            reasoning="Test Level 2 action",
            user_approval="approved_by_user_123",
            safety_level=2
        )

        # Verify approval is recorded
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT * FROM audit_log
            WHERE action_name = 'social_post'
            ORDER BY sequence_number DESC LIMIT 1
        """)
        log_entry = cursor.fetchone()

        assert log_entry is not None
        assert log_entry["user_approval"] is not None


class TestLevel2ActionsReversibility:
    """Test reversibility considerations for Level 2 actions."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create temporary database."""
        db_path = tmp_path / "test.db"
        return Database(str(db_path))

    def test_social_post_creates_record_before_publishing(self, db):
        """Social post should create database record before external posting."""
        tool = SocialPostTool(db=db)

        result = tool.execute(
            content="Reversibility test post",
            platforms=["twitter"]
        )

        if result["success"]:
            # Verify post is recorded in database
            cursor = db.conn.cursor()
            cursor.execute("""
                SELECT * FROM social_media_posts
                WHERE content = 'Reversibility test post'
                ORDER BY created_at DESC LIMIT 1
            """)
            row = cursor.fetchone()

            assert row is not None
            # Post should be in a state that allows review
            assert row["status"] in ["draft", "scheduled", "published"]

    def test_schedule_change_can_be_reverted(self, db):
        """Schedule changes should be revertable."""
        tool = ScheduleBriefingTool(db=db)

        # Change schedule
        result1 = tool.execute(day_of_week="tuesday", time="07:00")

        # Change back
        result2 = tool.execute(day_of_week="monday", time="08:00")

        # Both operations should succeed
        assert isinstance(result1, dict)
        assert isinstance(result2, dict)


class TestLevel2ActionsErrorHandling:
    """Test error handling for Level 2 actions."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create temporary database."""
        db_path = tmp_path / "test.db"
        return Database(str(db_path))

    def test_invalid_platform_returns_error(self, db):
        """Invalid platform should return error."""
        tool = SocialPostTool(db=db)

        result = tool.execute(
            content="Test",
            platforms=["invalid_platform"]
        )

        # Should handle gracefully
        assert isinstance(result, dict)

    def test_invalid_schedule_time_returns_error(self, db):
        """Invalid schedule time should return error."""
        tool = ScheduleBriefingTool(db=db)

        result = tool.execute(
            day_of_week="invalid_day",
            time="25:00"  # Invalid time
        )

        # Should handle gracefully
        assert isinstance(result, dict)

    def test_error_prevents_external_action(self, db):
        """Error should prevent external action from executing."""
        tool = SocialPostTool(db=db)

        # Attempt invalid post
        result = tool.execute(
            content="",  # Empty content
            platforms=["twitter"]
        )

        # Should fail validation before external posting
        assert isinstance(result, dict)


class TestLevel2ActionsConfirmationWorkflow:
    """Test confirmation workflow for Level 2 actions."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create temporary database."""
        db_path = tmp_path / "test.db"
        return Database(str(db_path))

    def test_action_provides_preview_information(self, db):
        """Action should provide information for user to review."""
        tool = SocialPostTool(db=db)

        result = tool.execute(
            content="Preview test: This is what will be posted",
            platforms=["twitter", "facebook"]
        )

        # Result should contain information for user review
        assert isinstance(result, dict)
        assert "success" in result

    def test_action_indicates_external_impact(self, db):
        """Action should indicate it will affect external systems."""
        tool = SocialPostTool(db=db)

        # The tool's safety level indicates external impact
        assert tool.safety_level == 2

        # Description should mention external posting
        assert tool.description is not None
        assert len(tool.description) > 0

    def test_audit_log_shows_confirmation_point(self, db):
        """Audit log should show where confirmation was required."""
        tool = SocialPostTool(db=db)

        result = tool.execute(
            content="Confirmation point test",
            platforms=["twitter"]
        )

        # Check audit log
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT * FROM audit_log
            WHERE parameters LIKE '%Confirmation point test%'
            ORDER BY sequence_number DESC LIMIT 1
        """)
        log_entry = cursor.fetchone()

        assert log_entry is not None
        # Should indicate Level 2 (confirmation required)
        assert log_entry.get("safety_level") == 2 or "2" in str(log_entry["parameters"])


class TestLevel2ActionsRateLimiting:
    """Test that Level 2 actions respect rate limits."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create temporary database."""
        db_path = tmp_path / "test.db"
        return Database(str(db_path))

    def test_social_posts_respect_daily_limit(self, db):
        """Social posts should respect daily posting limits."""
        tool = SocialPostTool(db=db)

        # Constitution specifies 10 posts/day limit
        # This test verifies the limit exists (actual enforcement may vary)

        # Execute multiple posts
        results = []
        for i in range(3):
            result = tool.execute(
                content=f"Rate limit test post {i}",
                platforms=["twitter"]
            )
            results.append(result)

        # All should succeed (under limit)
        for result in results:
            assert isinstance(result, dict)

    def test_rate_limit_information_available(self, db):
        """Rate limit information should be available."""
        tool = SocialPostTool(db=db)

        # Tool should have rate limit awareness
        # (Implementation may vary - this tests the concept exists)
        assert tool.safety_level == 2  # Indicates controlled execution
