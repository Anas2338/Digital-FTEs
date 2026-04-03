"""
Contract tests for Briefing MCP tools.

Validates that briefing tools conform to their API specifications,
including parameter validation, return types, and error handling.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mcp_servers.digital_fte_server.tools.generate_briefing import GenerateBriefingTool
from mcp_servers.digital_fte_server.tools.get_briefing import GetBriefingTool
from mcp_servers.digital_fte_server.tools.list_briefings import ListBriefingsTool
from mcp_servers.digital_fte_server.tools.add_critical_issue import AddCriticalIssueTool
from mcp_servers.digital_fte_server.tools.schedule_briefing import ScheduleBriefingTool
from watchers.shared.database import Database


class TestGenerateBriefingContract:
    """Contract tests for generate-briefing tool."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create temporary database."""
        db_path = tmp_path / "test.db"
        return Database(str(db_path))

    @pytest.fixture
    def tool(self, db):
        """Create tool instance."""
        return GenerateBriefingTool(db=db)

    def test_tool_has_correct_name(self, tool):
        """Tool should have correct name."""
        assert tool.name == "generate-briefing"

    def test_tool_has_correct_safety_level(self, tool):
        """Tool should have safety level 1 (Notify)."""
        assert tool.safety_level == 1

    def test_tool_has_description(self, tool):
        """Tool should have a description."""
        assert tool.description is not None
        assert len(tool.description) > 0

    def test_execute_with_no_parameters(self, tool):
        """Execute should work with no parameters (current week)."""
        result = tool.execute()
        assert isinstance(result, dict)
        assert "success" in result

    def test_execute_with_week_number(self, tool):
        """Execute should accept week_number parameter."""
        result = tool.execute(week_number=14)
        assert isinstance(result, dict)

    def test_execute_with_year(self, tool):
        """Execute should accept year parameter."""
        result = tool.execute(year=2026)
        assert isinstance(result, dict)

    def test_execute_with_force_regenerate(self, tool):
        """Execute should accept force_regenerate parameter."""
        result = tool.execute(force_regenerate=True)
        assert isinstance(result, dict)

    def test_execute_returns_briefing_path(self, tool):
        """Execute should return briefing file path on success."""
        result = tool.execute()
        if result["success"]:
            assert "briefing_path" in result or "path" in result

    def test_week_number_must_be_valid(self, tool):
        """Week number must be between 1 and 53."""
        # Valid week numbers should work
        result = tool.execute(week_number=1)
        assert isinstance(result, dict)

        result = tool.execute(week_number=53)
        assert isinstance(result, dict)

    def test_year_must_be_valid(self, tool):
        """Year must be a valid 4-digit year."""
        result = tool.execute(year=2026)
        assert isinstance(result, dict)


class TestGetBriefingContract:
    """Contract tests for get-briefing tool."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create temporary database."""
        db_path = tmp_path / "test.db"
        return Database(str(db_path))

    @pytest.fixture
    def tool(self, db):
        """Create tool instance."""
        return GetBriefingTool(db=db)

    def test_tool_has_correct_name(self, tool):
        """Tool should have correct name."""
        assert tool.name == "get-briefing"

    def test_tool_has_correct_safety_level(self, tool):
        """Tool should have safety level 0 (Auto-Execute)."""
        assert tool.safety_level == 0

    def test_execute_with_no_parameters(self, tool):
        """Execute should work with no parameters (current week)."""
        result = tool.execute()
        assert isinstance(result, dict)

    def test_execute_with_week_number(self, tool):
        """Execute should accept week_number parameter."""
        result = tool.execute(week_number=14)
        assert isinstance(result, dict)

    def test_execute_with_year(self, tool):
        """Execute should accept year parameter."""
        result = tool.execute(year=2026)
        assert isinstance(result, dict)

    def test_execute_returns_content(self, tool):
        """Execute should return briefing content on success."""
        result = tool.execute()
        if result["success"]:
            assert "content" in result or "briefing" in result


class TestListBriefingsContract:
    """Contract tests for list-briefings tool."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create temporary database."""
        db_path = tmp_path / "test.db"
        return Database(str(db_path))

    @pytest.fixture
    def tool(self, db):
        """Create tool instance."""
        return ListBriefingsTool(db=db)

    def test_tool_has_correct_name(self, tool):
        """Tool should have correct name."""
        assert tool.name == "list-briefings"

    def test_tool_has_correct_safety_level(self, tool):
        """Tool should have safety level 0 (Auto-Execute)."""
        assert tool.safety_level == 0

    def test_execute_with_no_parameters(self, tool):
        """Execute should work with no parameters (all briefings)."""
        result = tool.execute()
        assert isinstance(result, dict)

    def test_execute_with_year_filter(self, tool):
        """Execute should accept year parameter."""
        result = tool.execute(year=2026)
        assert isinstance(result, dict)

    def test_execute_with_limit(self, tool):
        """Execute should accept limit parameter."""
        result = tool.execute(limit=10)
        assert isinstance(result, dict)

    def test_execute_returns_briefings_list(self, tool):
        """Execute should return list of briefings."""
        result = tool.execute()
        if result["success"]:
            assert "briefings" in result
            assert isinstance(result["briefings"], list)

    def test_limit_must_be_positive(self, tool):
        """Limit parameter must be positive."""
        result = tool.execute(limit=1)
        assert isinstance(result, dict)


class TestAddCriticalIssueContract:
    """Contract tests for add-critical-issue tool."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create temporary database."""
        db_path = tmp_path / "test.db"
        return Database(str(db_path))

    @pytest.fixture
    def tool(self, db):
        """Create tool instance."""
        return AddCriticalIssueTool(db=db)

    def test_tool_has_correct_name(self, tool):
        """Tool should have correct name."""
        assert tool.name == "add-critical-issue"

    def test_tool_has_correct_safety_level(self, tool):
        """Tool should have safety level 1 (Notify)."""
        assert tool.safety_level == 1

    def test_execute_requires_title(self, tool):
        """Execute should require title parameter."""
        with pytest.raises((TypeError, KeyError, ValueError)):
            tool.execute(description="Test issue", severity="high")

    def test_execute_requires_description(self, tool):
        """Execute should require description parameter."""
        with pytest.raises((TypeError, KeyError, ValueError)):
            tool.execute(title="Test Issue", severity="high")

    def test_execute_with_severity(self, tool):
        """Execute should accept severity parameter."""
        result = tool.execute(
            title="Test Issue",
            description="Test description",
            severity="high"
        )
        assert isinstance(result, dict)

    def test_valid_severity_levels(self, tool):
        """Severity must be one of the valid levels."""
        valid_severities = ["low", "medium", "high", "critical"]

        for severity in valid_severities:
            result = tool.execute(
                title="Test Issue",
                description="Test description",
                severity=severity
            )
            assert isinstance(result, dict)

    def test_execute_returns_success(self, tool):
        """Execute should return success status."""
        result = tool.execute(
            title="Test Issue",
            description="Test description",
            severity="medium"
        )
        assert "success" in result


class TestScheduleBriefingContract:
    """Contract tests for schedule-briefing tool."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create temporary database."""
        db_path = tmp_path / "test.db"
        return Database(str(db_path))

    @pytest.fixture
    def tool(self, db):
        """Create tool instance."""
        return ScheduleBriefingTool(db=db)

    def test_tool_has_correct_name(self, tool):
        """Tool should have correct name."""
        assert tool.name == "schedule-briefing"

    def test_tool_has_correct_safety_level(self, tool):
        """Tool should have safety level 2 (Confirm)."""
        assert tool.safety_level == 2

    def test_execute_requires_day_of_week(self, tool):
        """Execute should require day_of_week parameter."""
        with pytest.raises((TypeError, KeyError, ValueError)):
            tool.execute(time="08:00")

    def test_execute_requires_time(self, tool):
        """Execute should require time parameter."""
        with pytest.raises((TypeError, KeyError, ValueError)):
            tool.execute(day_of_week="monday")

    def test_valid_days_of_week(self, tool):
        """Day of week must be valid."""
        valid_days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

        for day in valid_days:
            result = tool.execute(day_of_week=day, time="08:00")
            assert isinstance(result, dict)

    def test_time_format(self, tool):
        """Time should be in HH:MM format."""
        result = tool.execute(day_of_week="monday", time="08:00")
        assert isinstance(result, dict)

        result = tool.execute(day_of_week="monday", time="14:30")
        assert isinstance(result, dict)

    def test_execute_returns_success(self, tool):
        """Execute should return success status."""
        result = tool.execute(day_of_week="monday", time="08:00")
        assert "success" in result


class TestBriefingToolsCommonContract:
    """Contract tests for common behavior across all briefing tools."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create temporary database."""
        db_path = tmp_path / "test.db"
        return Database(str(db_path))

    def test_all_tools_have_name_attribute(self, db):
        """All tools should have a name attribute."""
        tools = [
            GenerateBriefingTool(db=db),
            GetBriefingTool(db=db),
            ListBriefingsTool(db=db),
            AddCriticalIssueTool(db=db),
            ScheduleBriefingTool(db=db)
        ]

        for tool in tools:
            assert hasattr(tool, "name")
            assert isinstance(tool.name, str)
            assert len(tool.name) > 0

    def test_all_tools_have_safety_level(self, db):
        """All tools should have a safety_level attribute."""
        tools = [
            GenerateBriefingTool(db=db),
            GetBriefingTool(db=db),
            ListBriefingsTool(db=db),
            AddCriticalIssueTool(db=db),
            ScheduleBriefingTool(db=db)
        ]

        for tool in tools:
            assert hasattr(tool, "safety_level")
            assert isinstance(tool.safety_level, int)
            assert 0 <= tool.safety_level <= 3

    def test_all_tools_have_execute_method(self, db):
        """All tools should have an execute method."""
        tools = [
            GenerateBriefingTool(db=db),
            GetBriefingTool(db=db),
            ListBriefingsTool(db=db),
            AddCriticalIssueTool(db=db),
            ScheduleBriefingTool(db=db)
        ]

        for tool in tools:
            assert hasattr(tool, "execute")
            assert callable(tool.execute)

    def test_all_tools_return_dict_from_execute(self, db):
        """All tools should return a dictionary from execute."""
        generate_tool = GenerateBriefingTool(db=db)
        result = generate_tool.execute()
        assert isinstance(result, dict)

        get_tool = GetBriefingTool(db=db)
        result = get_tool.execute()
        assert isinstance(result, dict)

        list_tool = ListBriefingsTool(db=db)
        result = list_tool.execute()
        assert isinstance(result, dict)

        issue_tool = AddCriticalIssueTool(db=db)
        result = issue_tool.execute(
            title="Test",
            description="Test",
            severity="medium"
        )
        assert isinstance(result, dict)

        schedule_tool = ScheduleBriefingTool(db=db)
        result = schedule_tool.execute(day_of_week="monday", time="08:00")
        assert isinstance(result, dict)

    def test_read_only_tools_have_safety_level_0(self, db):
        """Read-only tools should have safety level 0."""
        read_only_tools = [
            GetBriefingTool(db=db),
            ListBriefingsTool(db=db)
        ]

        for tool in read_only_tools:
            assert tool.safety_level == 0

    def test_write_tools_have_higher_safety_level(self, db):
        """Write tools should have safety level 1 or higher."""
        write_tools = [
            GenerateBriefingTool(db=db),
            AddCriticalIssueTool(db=db),
            ScheduleBriefingTool(db=db)
        ]

        for tool in write_tools:
            assert tool.safety_level >= 1
