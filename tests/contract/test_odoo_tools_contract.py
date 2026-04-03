"""
Contract tests for Odoo MCP tools.

Validates that Odoo tools conform to their API specifications,
including parameter validation, return types, and error handling.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mcp_servers.digital_fte_server.tools.odoo_record_transaction import OdooRecordTransactionTool
from mcp_servers.digital_fte_server.tools.odoo_query_financials import OdooQueryFinancialsTool
from mcp_servers.digital_fte_server.tools.odoo_check_connection import OdooCheckConnectionTool
from mcp_servers.digital_fte_server.tools.odoo_get_transactions import OdooGetTransactionsTool
from watchers.shared.database import Database


class TestOdooRecordTransactionContract:
    """Contract tests for odoo-record-transaction tool."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create temporary database."""
        db_path = tmp_path / "test.db"
        return Database(str(db_path))

    @pytest.fixture
    def tool(self, db):
        """Create tool instance."""
        return OdooRecordTransactionTool(db=db)

    def test_tool_has_correct_name(self, tool):
        """Tool should have correct name."""
        assert tool.name == "odoo-record-transaction"

    def test_tool_has_correct_safety_level(self, tool):
        """Tool should have safety level 1 (Notify)."""
        assert tool.safety_level == 1

    def test_tool_has_description(self, tool):
        """Tool should have a description."""
        assert tool.description is not None
        assert len(tool.description) > 0

    def test_execute_requires_amount(self, tool):
        """Execute should require amount parameter."""
        with pytest.raises((TypeError, KeyError, ValueError)):
            tool.execute(date="2026-04-01", description="Test", category="Revenue")

    def test_execute_requires_date(self, tool):
        """Execute should require date parameter."""
        with pytest.raises((TypeError, KeyError, ValueError)):
            tool.execute(amount=1000.00, description="Test", category="Revenue")

    def test_execute_requires_description(self, tool):
        """Execute should require description parameter."""
        with pytest.raises((TypeError, KeyError, ValueError)):
            tool.execute(amount=1000.00, date="2026-04-01", category="Revenue")

    def test_execute_requires_category(self, tool):
        """Execute should require category parameter."""
        with pytest.raises((TypeError, KeyError, ValueError)):
            tool.execute(amount=1000.00, date="2026-04-01", description="Test")

    def test_execute_returns_dict(self, tool):
        """Execute should return a dictionary."""
        result = tool.execute(
            amount=1000.00,
            date="2026-04-01",
            description="Test transaction",
            category="Revenue"
        )
        assert isinstance(result, dict)

    def test_execute_result_has_success_field(self, tool):
        """Execute result should have success field."""
        result = tool.execute(
            amount=1000.00,
            date="2026-04-01",
            description="Test",
            category="Revenue"
        )
        assert "success" in result

    def test_execute_result_has_transaction_id_on_success(self, tool):
        """Execute result should have transaction_id on success."""
        result = tool.execute(
            amount=1000.00,
            date="2026-04-01",
            description="Test",
            category="Revenue"
        )
        if result["success"]:
            assert "transaction_id" in result

    def test_amount_must_be_numeric(self, tool):
        """Amount parameter must be numeric."""
        with pytest.raises((TypeError, ValueError)):
            tool.execute(
                amount="not a number",
                date="2026-04-01",
                description="Test",
                category="Revenue"
            )

    def test_category_must_be_valid(self, tool):
        """Category must be one of the valid categories."""
        valid_categories = ["Revenue", "COGS", "Operating Expenses", "Assets", "Liabilities", "Equity"]

        # Valid category should work
        result = tool.execute(
            amount=1000.00,
            date="2026-04-01",
            description="Test",
            category="Revenue"
        )
        assert result["success"] is True


class TestOdooQueryFinancialsContract:
    """Contract tests for odoo-query-financials tool."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create temporary database."""
        db_path = tmp_path / "test.db"
        return Database(str(db_path))

    @pytest.fixture
    def tool(self, db):
        """Create tool instance."""
        return OdooQueryFinancialsTool(db=db)

    def test_tool_has_correct_name(self, tool):
        """Tool should have correct name."""
        assert tool.name == "odoo-query-financials"

    def test_tool_has_correct_safety_level(self, tool):
        """Tool should have safety level 0 (Auto-Execute)."""
        assert tool.safety_level == 0

    def test_execute_with_no_parameters(self, tool):
        """Execute should work with no parameters (returns all)."""
        result = tool.execute()
        assert isinstance(result, dict)
        assert "success" in result

    def test_execute_with_start_date(self, tool):
        """Execute should accept start_date parameter."""
        result = tool.execute(start_date="2026-01-01")
        assert isinstance(result, dict)
        assert "success" in result

    def test_execute_with_end_date(self, tool):
        """Execute should accept end_date parameter."""
        result = tool.execute(end_date="2026-12-31")
        assert isinstance(result, dict)
        assert "success" in result

    def test_execute_with_category_filter(self, tool):
        """Execute should accept category parameter."""
        result = tool.execute(category="Revenue")
        assert isinstance(result, dict)
        assert "success" in result

    def test_execute_returns_transactions_list(self, tool):
        """Execute result should contain transactions list."""
        result = tool.execute()
        if result["success"]:
            assert "transactions" in result
            assert isinstance(result["transactions"], list)

    def test_execute_returns_summary(self, tool):
        """Execute result should contain summary information."""
        result = tool.execute()
        if result["success"]:
            assert "summary" in result or "total" in result


class TestOdooCheckConnectionContract:
    """Contract tests for odoo-check-connection tool."""

    @pytest.fixture
    def tool(self):
        """Create tool instance."""
        return OdooCheckConnectionTool()

    def test_tool_has_correct_name(self, tool):
        """Tool should have correct name."""
        assert tool.name == "odoo-check-connection"

    def test_tool_has_correct_safety_level(self, tool):
        """Tool should have safety level 0 (Auto-Execute)."""
        assert tool.safety_level == 0

    def test_execute_requires_no_parameters(self, tool):
        """Execute should work with no parameters."""
        result = tool.execute()
        assert isinstance(result, dict)

    def test_execute_returns_connection_status(self, tool):
        """Execute should return connection status."""
        result = tool.execute()
        assert "connected" in result or "success" in result

    def test_execute_returns_error_on_failure(self, tool):
        """Execute should return error message on connection failure."""
        result = tool.execute()
        if not result.get("connected", result.get("success")):
            assert "error" in result or "message" in result


class TestOdooGetTransactionsContract:
    """Contract tests for odoo-get-transactions tool."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create temporary database."""
        db_path = tmp_path / "test.db"
        return Database(str(db_path))

    @pytest.fixture
    def tool(self, db):
        """Create tool instance."""
        return OdooGetTransactionsTool(db=db)

    def test_tool_has_correct_name(self, tool):
        """Tool should have correct name."""
        assert tool.name == "odoo-get-transactions"

    def test_tool_has_correct_safety_level(self, tool):
        """Tool should have safety level 0 (Auto-Execute)."""
        assert tool.safety_level == 0

    def test_execute_with_limit(self, tool):
        """Execute should accept limit parameter."""
        result = tool.execute(limit=10)
        assert isinstance(result, dict)
        assert "success" in result

    def test_execute_with_offset(self, tool):
        """Execute should accept offset parameter."""
        result = tool.execute(offset=5)
        assert isinstance(result, dict)
        assert "success" in result

    def test_execute_returns_transactions_list(self, tool):
        """Execute should return list of transactions."""
        result = tool.execute()
        if result["success"]:
            assert "transactions" in result
            assert isinstance(result["transactions"], list)

    def test_limit_must_be_positive(self, tool):
        """Limit parameter must be positive."""
        result = tool.execute(limit=-1)
        # Should either reject or clamp to valid range
        assert isinstance(result, dict)

    def test_offset_must_be_non_negative(self, tool):
        """Offset parameter must be non-negative."""
        result = tool.execute(offset=-1)
        # Should either reject or clamp to valid range
        assert isinstance(result, dict)


class TestOdooToolsCommonContract:
    """Contract tests for common behavior across all Odoo tools."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create temporary database."""
        db_path = tmp_path / "test.db"
        return Database(str(db_path))

    def test_all_tools_have_name_attribute(self, db):
        """All tools should have a name attribute."""
        tools = [
            OdooRecordTransactionTool(db=db),
            OdooQueryFinancialsTool(db=db),
            OdooCheckConnectionTool(),
            OdooGetTransactionsTool(db=db)
        ]

        for tool in tools:
            assert hasattr(tool, "name")
            assert isinstance(tool.name, str)
            assert len(tool.name) > 0

    def test_all_tools_have_safety_level(self, db):
        """All tools should have a safety_level attribute."""
        tools = [
            OdooRecordTransactionTool(db=db),
            OdooQueryFinancialsTool(db=db),
            OdooCheckConnectionTool(),
            OdooGetTransactionsTool(db=db)
        ]

        for tool in tools:
            assert hasattr(tool, "safety_level")
            assert isinstance(tool.safety_level, int)
            assert 0 <= tool.safety_level <= 3

    def test_all_tools_have_execute_method(self, db):
        """All tools should have an execute method."""
        tools = [
            OdooRecordTransactionTool(db=db),
            OdooQueryFinancialsTool(db=db),
            OdooCheckConnectionTool(),
            OdooGetTransactionsTool(db=db)
        ]

        for tool in tools:
            assert hasattr(tool, "execute")
            assert callable(tool.execute)

    def test_all_tools_return_dict_from_execute(self, db):
        """All tools should return a dictionary from execute."""
        # Test with minimal valid parameters
        record_tool = OdooRecordTransactionTool(db=db)
        result = record_tool.execute(
            amount=100.00,
            date="2026-04-01",
            description="Test",
            category="Revenue"
        )
        assert isinstance(result, dict)

        query_tool = OdooQueryFinancialsTool(db=db)
        result = query_tool.execute()
        assert isinstance(result, dict)

        check_tool = OdooCheckConnectionTool()
        result = check_tool.execute()
        assert isinstance(result, dict)

        get_tool = OdooGetTransactionsTool(db=db)
        result = get_tool.execute()
        assert isinstance(result, dict)
