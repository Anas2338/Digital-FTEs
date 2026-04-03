"""Unit tests for ActionQueue model and queue operations.

Tests action queueing, priority handling, and queue processing.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta
import json

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from watchers.shared.database import Database


class TestActionQueue:
    """Test suite for ActionQueue operations."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create temporary database for testing."""
        db_path = tmp_path / "test_queue.db"
        return Database(str(db_path))

    def test_enqueue_action(self, db):
        """Test enqueuing an action."""
        db.enqueue_action(
            action_id="test-123",
            action_type="odoo_record_transaction",
            parameters={"amount": 100.0, "description": "Test"},
            integration_name="odoo_integration",
            priority=1
        )

        # Verify action was queued
        cursor = db.conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM action_queue")
        count = cursor.fetchone()[0]
        assert count == 1

    def test_get_queued_actions_returns_ready_actions(self, db):
        """Test that get_queued_actions returns only ready actions."""
        # Queue action for now
        db.enqueue_action(
            action_id="ready-1",
            action_type="test_action",
            parameters={},
            integration_name="test",
            priority=0,
            scheduled_for=None
        )

        # Queue action for future
        future_time = (datetime.utcnow() + timedelta(hours=1)).isoformat() + "Z"
        db.enqueue_action(
            action_id="future-1",
            action_type="test_action",
            parameters={},
            integration_name="test",
            priority=0,
            scheduled_for=future_time
        )

        # Should only return ready action
        actions = db.get_queued_actions()
        assert len(actions) == 1
        assert actions[0]["id"] == "ready-1"

    def test_priority_ordering(self, db):
        """Test that actions are returned in priority order."""
        # Queue actions with different priorities
        db.enqueue_action(
            action_id="low-priority",
            action_type="test",
            parameters={},
            integration_name="test",
            priority=1
        )

        db.enqueue_action(
            action_id="high-priority",
            action_type="test",
            parameters={},
            integration_name="test",
            priority=10
        )

        db.enqueue_action(
            action_id="medium-priority",
            action_type="test",
            parameters={},
            integration_name="test",
            priority=5
        )

        # Should return in priority order (high to low)
        actions = db.get_queued_actions()
        assert len(actions) == 3
        assert actions[0]["id"] == "high-priority"
        assert actions[1]["id"] == "medium-priority"
        assert actions[2]["id"] == "low-priority"

    def test_filter_by_integration(self, db):
        """Test filtering queued actions by integration."""
        db.enqueue_action(
            action_id="odoo-1",
            action_type="test",
            parameters={},
            integration_name="odoo_integration",
            priority=0
        )

        db.enqueue_action(
            action_id="facebook-1",
            action_type="test",
            parameters={},
            integration_name="facebook_integration",
            priority=0
        )

        # Filter by integration
        odoo_actions = db.get_queued_actions(integration_name="odoo_integration")
        assert len(odoo_actions) == 1
        assert odoo_actions[0]["id"] == "odoo-1"

    def test_update_queued_action_increments_attempts(self, db):
        """Test that updating action increments attempt counter."""
        db.enqueue_action(
            action_id="test-123",
            action_type="test",
            parameters={},
            integration_name="test",
            priority=0
        )

        # Update action (simulate execution attempt)
        db.update_queued_action(
            action_id="test-123",
            status="queued",
            last_error="Connection timeout"
        )

        # Check attempts incremented
        cursor = db.conn.cursor()
        cursor.execute("SELECT attempts FROM action_queue WHERE id = ?", ("test-123",))
        attempts = cursor.fetchone()[0]
        assert attempts == 1

    def test_update_queued_action_records_error(self, db):
        """Test that errors are recorded when updating action."""
        db.enqueue_action(
            action_id="test-123",
            action_type="test",
            parameters={},
            integration_name="test",
            priority=0
        )

        db.update_queued_action(
            action_id="test-123",
            status="failed",
            last_error="API rate limit exceeded"
        )

        # Check error recorded
        cursor = db.conn.cursor()
        cursor.execute("SELECT last_error FROM action_queue WHERE id = ?", ("test-123",))
        error = cursor.fetchone()[0]
        assert error == "API rate limit exceeded"

    def test_remove_queued_action(self, db):
        """Test removing completed action from queue."""
        db.enqueue_action(
            action_id="test-123",
            action_type="test",
            parameters={},
            integration_name="test",
            priority=0
        )

        db.remove_queued_action("test-123")

        # Verify action removed
        cursor = db.conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM action_queue WHERE id = ?", ("test-123",))
        count = cursor.fetchone()[0]
        assert count == 0

    def test_queue_stats_total_count(self, db):
        """Test queue statistics total count."""
        # Queue multiple actions
        for i in range(5):
            db.enqueue_action(
                action_id=f"test-{i}",
                action_type="test",
                parameters={},
                integration_name="test",
                priority=0
            )

        stats = db.get_queue_stats()
        assert stats["total_queued"] == 5

    def test_queue_stats_by_integration(self, db):
        """Test queue statistics grouped by integration."""
        db.enqueue_action(
            action_id="odoo-1",
            action_type="test",
            parameters={},
            integration_name="odoo_integration",
            priority=0
        )

        db.enqueue_action(
            action_id="odoo-2",
            action_type="test",
            parameters={},
            integration_name="odoo_integration",
            priority=0
        )

        db.enqueue_action(
            action_id="facebook-1",
            action_type="test",
            parameters={},
            integration_name="facebook_integration",
            priority=0
        )

        stats = db.get_queue_stats()
        assert stats["by_integration"]["odoo_integration"] == 2
        assert stats["by_integration"]["facebook_integration"] == 1

    def test_queue_stats_failed_attempts(self, db):
        """Test queue statistics for failed attempts."""
        # Queue action and fail it multiple times
        db.enqueue_action(
            action_id="test-123",
            action_type="test",
            parameters={},
            integration_name="test",
            priority=0
        )

        # Simulate 3 failed attempts
        for _ in range(3):
            db.update_queued_action(
                action_id="test-123",
                status="queued",
                last_error="Failed"
            )

        stats = db.get_queue_stats()
        assert stats["failed_attempts"] == 1

    def test_parameters_serialization(self, db):
        """Test that complex parameters are serialized correctly."""
        complex_params = {
            "amount": 1000.50,
            "items": ["item1", "item2"],
            "metadata": {"key": "value"}
        }

        db.enqueue_action(
            action_id="test-123",
            action_type="test",
            parameters=complex_params,
            integration_name="test",
            priority=0
        )

        actions = db.get_queued_actions()
        assert len(actions) == 1
        assert actions[0]["parameters"] == complex_params

    def test_scheduled_time_handling(self, db):
        """Test that scheduled_for is handled correctly."""
        scheduled_time = (datetime.utcnow() + timedelta(hours=2)).isoformat() + "Z"

        db.enqueue_action(
            action_id="test-123",
            action_type="test",
            parameters={},
            integration_name="test",
            priority=0,
            scheduled_for=scheduled_time
        )

        # Should not be returned yet
        actions = db.get_queued_actions()
        assert len(actions) == 0

        # Update scheduled time to past
        cursor = db.conn.cursor()
        past_time = (datetime.utcnow() - timedelta(hours=1)).isoformat() + "Z"
        cursor.execute(
            "UPDATE action_queue SET scheduled_for = ? WHERE id = ?",
            (past_time, "test-123")
        )
        db.conn.commit()

        # Should now be returned
        actions = db.get_queued_actions()
        assert len(actions) == 1

    def test_limit_parameter(self, db):
        """Test that limit parameter works correctly."""
        # Queue 10 actions
        for i in range(10):
            db.enqueue_action(
                action_id=f"test-{i}",
                action_type="test",
                parameters={},
                integration_name="test",
                priority=0
            )

        # Request only 5
        actions = db.get_queued_actions(limit=5)
        assert len(actions) == 5
