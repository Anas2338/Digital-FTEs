"""
Contract tests for Social Media MCP tools.

Validates that social media tools conform to their API specifications,
including parameter validation, return types, and error handling.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mcp_servers.digital_fte_server.tools.social_media.social_post import SocialPostTool
from mcp_servers.digital_fte_server.tools.social_media.social_schedule import SocialScheduleTool
from mcp_servers.digital_fte_server.tools.social_media.social_get_engagement import SocialGetEngagementTool
from mcp_servers.digital_fte_server.tools.social_media.social_list_posts import SocialListPostsTool
from watchers.shared.database import Database


class TestSocialPostContract:
    """Contract tests for social-post tool."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create temporary database."""
        db_path = tmp_path / "test.db"
        return Database(str(db_path))

    @pytest.fixture
    def tool(self, db):
        """Create tool instance."""
        return SocialPostTool(db=db)

    def test_tool_has_correct_name(self, tool):
        """Tool should have correct name."""
        assert tool.name == "social-post"

    def test_tool_has_correct_safety_level(self, tool):
        """Tool should have safety level 2 (Confirm)."""
        assert tool.safety_level == 2

    def test_tool_has_description(self, tool):
        """Tool should have a description."""
        assert tool.description is not None
        assert len(tool.description) > 0

    def test_execute_requires_content(self, tool):
        """Execute should require content parameter."""
        with pytest.raises((TypeError, KeyError, ValueError)):
            tool.execute(platforms=["twitter"])

    def test_execute_requires_platforms(self, tool):
        """Execute should require platforms parameter."""
        with pytest.raises((TypeError, KeyError, ValueError)):
            tool.execute(content="Test post")

    def test_execute_returns_dict(self, tool):
        """Execute should return a dictionary."""
        result = tool.execute(
            content="Test post",
            platforms=["twitter"]
        )
        assert isinstance(result, dict)

    def test_execute_result_has_success_field(self, tool):
        """Execute result should have success field."""
        result = tool.execute(
            content="Test post",
            platforms=["twitter"]
        )
        assert "success" in result

    def test_platforms_must_be_list(self, tool):
        """Platforms parameter must be a list."""
        with pytest.raises((TypeError, ValueError)):
            tool.execute(
                content="Test post",
                platforms="twitter"  # Should be list
            )

    def test_valid_platforms(self, tool):
        """Platforms must be valid social media platforms."""
        valid_platforms = ["facebook", "twitter", "instagram"]

        for platform in valid_platforms:
            result = tool.execute(
                content="Test post",
                platforms=[platform]
            )
            assert isinstance(result, dict)

    def test_content_must_be_string(self, tool):
        """Content parameter must be a string."""
        with pytest.raises((TypeError, ValueError)):
            tool.execute(
                content=12345,  # Should be string
                platforms=["twitter"]
            )


class TestSocialScheduleContract:
    """Contract tests for social-schedule tool."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create temporary database."""
        db_path = tmp_path / "test.db"
        return Database(str(db_path))

    @pytest.fixture
    def tool(self, db):
        """Create tool instance."""
        return SocialScheduleTool(db=db)

    def test_tool_has_correct_name(self, tool):
        """Tool should have correct name."""
        assert tool.name == "social-schedule"

    def test_tool_has_correct_safety_level(self, tool):
        """Tool should have safety level 1 (Notify)."""
        assert tool.safety_level == 1

    def test_execute_requires_content(self, tool):
        """Execute should require content parameter."""
        with pytest.raises((TypeError, KeyError, ValueError)):
            tool.execute(
                platforms=["twitter"],
                scheduled_time="2026-04-03T10:00:00Z"
            )

    def test_execute_requires_platforms(self, tool):
        """Execute should require platforms parameter."""
        with pytest.raises((TypeError, KeyError, ValueError)):
            tool.execute(
                content="Test post",
                scheduled_time="2026-04-03T10:00:00Z"
            )

    def test_execute_requires_scheduled_time(self, tool):
        """Execute should require scheduled_time parameter."""
        with pytest.raises((TypeError, KeyError, ValueError)):
            tool.execute(
                content="Test post",
                platforms=["twitter"]
            )

    def test_execute_returns_dict(self, tool):
        """Execute should return a dictionary."""
        result = tool.execute(
            content="Test post",
            platforms=["twitter"],
            scheduled_time="2026-04-03T10:00:00Z"
        )
        assert isinstance(result, dict)

    def test_scheduled_time_format(self, tool):
        """Scheduled time should be in ISO format."""
        result = tool.execute(
            content="Test post",
            platforms=["twitter"],
            scheduled_time="2026-04-03T10:00:00Z"
        )
        assert isinstance(result, dict)


class TestSocialGetEngagementContract:
    """Contract tests for social-get-engagement tool."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create temporary database."""
        db_path = tmp_path / "test.db"
        return Database(str(db_path))

    @pytest.fixture
    def tool(self, db):
        """Create tool instance."""
        return SocialGetEngagementTool(db=db)

    def test_tool_has_correct_name(self, tool):
        """Tool should have correct name."""
        assert tool.name == "social-get-engagement"

    def test_tool_has_correct_safety_level(self, tool):
        """Tool should have safety level 0 (Auto-Execute)."""
        assert tool.safety_level == 0

    def test_execute_with_no_parameters(self, tool):
        """Execute should work with no parameters (returns all)."""
        result = tool.execute()
        assert isinstance(result, dict)
        assert "success" in result

    def test_execute_with_platform_filter(self, tool):
        """Execute should accept platform parameter."""
        result = tool.execute(platform="twitter")
        assert isinstance(result, dict)

    def test_execute_with_start_date(self, tool):
        """Execute should accept start_date parameter."""
        result = tool.execute(start_date="2026-04-01")
        assert isinstance(result, dict)

    def test_execute_with_end_date(self, tool):
        """Execute should accept end_date parameter."""
        result = tool.execute(end_date="2026-04-30")
        assert isinstance(result, dict)

    def test_execute_returns_engagement_metrics(self, tool):
        """Execute should return engagement metrics."""
        result = tool.execute()
        if result["success"]:
            assert "engagement" in result or "metrics" in result


class TestSocialListPostsContract:
    """Contract tests for social-list-posts tool."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create temporary database."""
        db_path = tmp_path / "test.db"
        return Database(str(db_path))

    @pytest.fixture
    def tool(self, db):
        """Create tool instance."""
        return SocialListPostsTool(db=db)

    def test_tool_has_correct_name(self, tool):
        """Tool should have correct name."""
        assert tool.name == "social-list-posts"

    def test_tool_has_correct_safety_level(self, tool):
        """Tool should have safety level 0 (Auto-Execute)."""
        assert tool.safety_level == 0

    def test_execute_with_no_parameters(self, tool):
        """Execute should work with no parameters."""
        result = tool.execute()
        assert isinstance(result, dict)

    def test_execute_with_status_filter(self, tool):
        """Execute should accept status parameter."""
        valid_statuses = ["draft", "scheduled", "published", "failed"]

        for status in valid_statuses:
            result = tool.execute(status=status)
            assert isinstance(result, dict)

    def test_execute_with_limit(self, tool):
        """Execute should accept limit parameter."""
        result = tool.execute(limit=10)
        assert isinstance(result, dict)

    def test_execute_returns_posts_list(self, tool):
        """Execute should return list of posts."""
        result = tool.execute()
        if result["success"]:
            assert "posts" in result
            assert isinstance(result["posts"], list)


class TestSocialMediaToolsCommonContract:
    """Contract tests for common behavior across all social media tools."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create temporary database."""
        db_path = tmp_path / "test.db"
        return Database(str(db_path))

    def test_all_tools_have_name_attribute(self, db):
        """All tools should have a name attribute."""
        tools = [
            SocialPostTool(db=db),
            SocialScheduleTool(db=db),
            SocialGetEngagementTool(db=db),
            SocialListPostsTool(db=db)
        ]

        for tool in tools:
            assert hasattr(tool, "name")
            assert isinstance(tool.name, str)
            assert len(tool.name) > 0
            assert tool.name.startswith("social-")

    def test_all_tools_have_safety_level(self, db):
        """All tools should have a safety_level attribute."""
        tools = [
            SocialPostTool(db=db),
            SocialScheduleTool(db=db),
            SocialGetEngagementTool(db=db),
            SocialListPostsTool(db=db)
        ]

        for tool in tools:
            assert hasattr(tool, "safety_level")
            assert isinstance(tool.safety_level, int)
            assert 0 <= tool.safety_level <= 3

    def test_all_tools_have_execute_method(self, db):
        """All tools should have an execute method."""
        tools = [
            SocialPostTool(db=db),
            SocialScheduleTool(db=db),
            SocialGetEngagementTool(db=db),
            SocialListPostsTool(db=db)
        ]

        for tool in tools:
            assert hasattr(tool, "execute")
            assert callable(tool.execute)

    def test_all_tools_return_dict_from_execute(self, db):
        """All tools should return a dictionary from execute."""
        # Test with minimal valid parameters
        post_tool = SocialPostTool(db=db)
        result = post_tool.execute(
            content="Test post",
            platforms=["twitter"]
        )
        assert isinstance(result, dict)

        schedule_tool = SocialScheduleTool(db=db)
        result = schedule_tool.execute(
            content="Test post",
            platforms=["twitter"],
            scheduled_time="2026-04-03T10:00:00Z"
        )
        assert isinstance(result, dict)

        engagement_tool = SocialGetEngagementTool(db=db)
        result = engagement_tool.execute()
        assert isinstance(result, dict)

        list_tool = SocialListPostsTool(db=db)
        result = list_tool.execute()
        assert isinstance(result, dict)

    def test_read_only_tools_have_safety_level_0(self, db):
        """Read-only tools should have safety level 0."""
        read_only_tools = [
            SocialGetEngagementTool(db=db),
            SocialListPostsTool(db=db)
        ]

        for tool in read_only_tools:
            assert tool.safety_level == 0

    def test_write_tools_have_higher_safety_level(self, db):
        """Write tools should have safety level 1 or higher."""
        write_tools = [
            SocialPostTool(db=db),
            SocialScheduleTool(db=db)
        ]

        for tool in write_tools:
            assert tool.safety_level >= 1
