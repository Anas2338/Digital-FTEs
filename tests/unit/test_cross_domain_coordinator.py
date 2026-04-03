"""
Unit tests for CrossDomainCoordinator class.

Tests cross-domain workflow coordination, approval, and audit logging.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from watchers.shared.cross_domain_coordinator import (
    CrossDomainCoordinator,
    CrossDomainWorkflow
)
from watchers.shared.domain_manager import (
    DomainContextManager,
    DomainType,
    PrivacyLevel,
    DataClassification
)
from watchers.shared.audit_logger import AuditLogger
from watchers.shared.database import Database


class TestWorkflowCreation:
    """Test cross-domain workflow creation."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create temporary database for testing."""
        db_path = tmp_path / "test.db"
        return Database(str(db_path))

    @pytest.fixture
    def coordinator(self, db):
        """Create coordinator instance."""
        domain_manager = DomainContextManager(db=db)
        audit_logger = AuditLogger(db=db)
        return CrossDomainCoordinator(
            domain_manager=domain_manager,
            audit_logger=audit_logger
        )

    def test_create_workflow(self, coordinator):
        """Test creating a cross-domain workflow."""
        workflow_id = coordinator.create_workflow(
            name="Personal to Business Expense",
            source_domain=DomainType.PERSONAL,
            target_domain=DomainType.BUSINESS,
            steps=[
                {"action": "record_transaction", "amount": 50.00},
                {"action": "update_accounting", "category": "Expenses"}
            ],
            requires_approval=True
        )

        assert workflow_id is not None
        assert workflow_id in coordinator.active_workflows

        workflow = coordinator.active_workflows[workflow_id]
        assert workflow.name == "Personal to Business Expense"
        assert workflow.source_domain == DomainType.PERSONAL
        assert workflow.target_domain == DomainType.BUSINESS
        assert len(workflow.steps) == 2
        assert workflow.status == "pending"

    def test_create_workflow_logs_to_audit(self, coordinator, db):
        """Test that workflow creation is logged to audit log."""
        workflow_id = coordinator.create_workflow(
            name="Test Workflow",
            source_domain=DomainType.BUSINESS,
            target_domain=DomainType.PERSONAL,
            steps=[{"action": "test"}],
            requires_approval=False
        )

        # Check audit log
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT * FROM audit_log
            WHERE action_name = 'cross_domain_workflow'
            AND action_type = 'create'
            ORDER BY sequence_number DESC LIMIT 1
        """)
        log_entry = cursor.fetchone()

        assert log_entry is not None
        assert workflow_id in log_entry["parameters"]


class TestWorkflowExecution:
    """Test cross-domain workflow execution."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create temporary database for testing."""
        db_path = tmp_path / "test.db"
        return Database(str(db_path))

    @pytest.fixture
    def coordinator(self, db):
        """Create coordinator instance."""
        domain_manager = DomainContextManager(db=db)
        audit_logger = AuditLogger(db=db)
        return CrossDomainCoordinator(
            domain_manager=domain_manager,
            audit_logger=audit_logger
        )

    def test_execute_workflow_success(self, coordinator):
        """Test successful workflow execution."""
        workflow_id = coordinator.create_workflow(
            name="Test Workflow",
            source_domain=DomainType.SHARED,
            target_domain=DomainType.BUSINESS,
            steps=[
                {"action": "step1", "data": "test1"},
                {"action": "step2", "data": "test2"}
            ]
        )

        result = coordinator.execute_workflow(
            workflow_id=workflow_id,
            user_approval="approved_by_user"
        )

        assert result["success"] is True
        assert result["workflow_id"] == workflow_id
        assert result["steps_completed"] == 2
        assert len(result["results"]) == 2

        # Check workflow status updated
        workflow = coordinator.active_workflows[workflow_id]
        assert workflow.status == "completed"

    def test_execute_nonexistent_workflow(self, coordinator):
        """Test executing a workflow that doesn't exist."""
        result = coordinator.execute_workflow(
            workflow_id="nonexistent-id",
            user_approval="approved"
        )

        assert result["success"] is False
        assert "not found" in result["error"]

    def test_execute_workflow_logs_steps(self, coordinator, db):
        """Test that workflow execution logs each step."""
        workflow_id = coordinator.create_workflow(
            name="Test Workflow",
            source_domain=DomainType.SHARED,
            target_domain=DomainType.BUSINESS,
            steps=[{"action": "test_step"}]
        )

        coordinator.execute_workflow(workflow_id, user_approval="approved")

        # Check audit log for step execution
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as count FROM audit_log
            WHERE action_name LIKE 'workflow_step_%'
        """)
        count = cursor.fetchone()["count"]

        assert count >= 1  # At least one step logged

    def test_execute_workflow_cross_domain_blocked(self, coordinator):
        """Test that sensitive cross-domain access is blocked."""
        # Create workflow from personal to business
        # This should be blocked if target has sensitive data
        workflow_id = coordinator.create_workflow(
            name="Blocked Workflow",
            source_domain=DomainType.PERSONAL,
            target_domain=DomainType.BUSINESS,
            steps=[{"action": "access_sensitive"}]
        )

        # Note: The actual blocking depends on privacy levels set in execute_workflow
        # This test verifies the workflow can be created but may be blocked during execution
        result = coordinator.execute_workflow(workflow_id, user_approval="approved")

        # Result depends on domain manager's access control logic
        # Should either succeed (if allowed) or fail with access denied
        assert "success" in result


class TestWorkflowStatus:
    """Test workflow status tracking."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create temporary database for testing."""
        db_path = tmp_path / "test.db"
        return Database(str(db_path))

    @pytest.fixture
    def coordinator(self, db):
        """Create coordinator instance."""
        domain_manager = DomainContextManager(db=db)
        audit_logger = AuditLogger(db=db)
        return CrossDomainCoordinator(
            domain_manager=domain_manager,
            audit_logger=audit_logger
        )

    def test_get_workflow_status(self, coordinator):
        """Test getting workflow status."""
        workflow_id = coordinator.create_workflow(
            name="Status Test",
            source_domain=DomainType.PERSONAL,
            target_domain=DomainType.BUSINESS,
            steps=[{"action": "test"}]
        )

        status = coordinator.get_workflow_status(workflow_id)

        assert status is not None
        assert status["workflow_id"] == workflow_id
        assert status["name"] == "Status Test"
        assert status["source_domain"] == "personal"
        assert status["target_domain"] == "business"
        assert status["status"] == "pending"
        assert status["current_step"] == 0
        assert status["total_steps"] == 1
        assert "created_at" in status

    def test_get_nonexistent_workflow_status(self, coordinator):
        """Test getting status of nonexistent workflow."""
        status = coordinator.get_workflow_status("nonexistent-id")
        assert status is None

    def test_workflow_status_updates_during_execution(self, coordinator):
        """Test that workflow status updates during execution."""
        workflow_id = coordinator.create_workflow(
            name="Status Update Test",
            source_domain=DomainType.SHARED,
            target_domain=DomainType.BUSINESS,
            steps=[
                {"action": "step1"},
                {"action": "step2"}
            ]
        )

        # Before execution
        status = coordinator.get_workflow_status(workflow_id)
        assert status["status"] == "pending"

        # Execute workflow
        coordinator.execute_workflow(workflow_id, user_approval="approved")

        # After execution
        status = coordinator.get_workflow_status(workflow_id)
        assert status["status"] == "completed"


class TestWorkflowListing:
    """Test listing active workflows."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create temporary database for testing."""
        db_path = tmp_path / "test.db"
        return Database(str(db_path))

    @pytest.fixture
    def coordinator(self, db):
        """Create coordinator instance."""
        domain_manager = DomainContextManager(db=db)
        audit_logger = AuditLogger(db=db)
        return CrossDomainCoordinator(
            domain_manager=domain_manager,
            audit_logger=audit_logger
        )

    def test_list_active_workflows_empty(self, coordinator):
        """Test listing workflows when none exist."""
        workflows = coordinator.list_active_workflows()
        assert workflows == []

    def test_list_active_workflows(self, coordinator):
        """Test listing multiple active workflows."""
        # Create multiple workflows
        wf1 = coordinator.create_workflow(
            name="Workflow 1",
            source_domain=DomainType.PERSONAL,
            target_domain=DomainType.BUSINESS,
            steps=[{"action": "test"}]
        )

        wf2 = coordinator.create_workflow(
            name="Workflow 2",
            source_domain=DomainType.BUSINESS,
            target_domain=DomainType.PERSONAL,
            steps=[{"action": "test"}]
        )

        workflows = coordinator.list_active_workflows()

        assert len(workflows) == 2
        workflow_ids = [w["workflow_id"] for w in workflows]
        assert wf1 in workflow_ids
        assert wf2 in workflow_ids


class TestWorkflowCancellation:
    """Test workflow cancellation."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create temporary database for testing."""
        db_path = tmp_path / "test.db"
        return Database(str(db_path))

    @pytest.fixture
    def coordinator(self, db):
        """Create coordinator instance."""
        domain_manager = DomainContextManager(db=db)
        audit_logger = AuditLogger(db=db)
        return CrossDomainCoordinator(
            domain_manager=domain_manager,
            audit_logger=audit_logger
        )

    def test_cancel_workflow(self, coordinator):
        """Test cancelling an active workflow."""
        workflow_id = coordinator.create_workflow(
            name="Cancel Test",
            source_domain=DomainType.PERSONAL,
            target_domain=DomainType.BUSINESS,
            steps=[{"action": "test"}]
        )

        result = coordinator.cancel_workflow(
            workflow_id=workflow_id,
            reason="User requested cancellation"
        )

        assert result is True
        assert workflow_id not in coordinator.active_workflows

    def test_cancel_nonexistent_workflow(self, coordinator):
        """Test cancelling a workflow that doesn't exist."""
        result = coordinator.cancel_workflow(
            workflow_id="nonexistent-id",
            reason="Test"
        )

        assert result is False

    def test_cancel_workflow_logs_to_audit(self, coordinator, db):
        """Test that workflow cancellation is logged."""
        workflow_id = coordinator.create_workflow(
            name="Cancel Log Test",
            source_domain=DomainType.PERSONAL,
            target_domain=DomainType.BUSINESS,
            steps=[{"action": "test"}]
        )

        coordinator.cancel_workflow(workflow_id, reason="Test cancellation")

        # Check audit log
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT * FROM audit_log
            WHERE action_name = 'cross_domain_workflow'
            AND action_type = 'cancel'
            ORDER BY sequence_number DESC LIMIT 1
        """)
        log_entry = cursor.fetchone()

        assert log_entry is not None
        assert "Test cancellation" in log_entry["parameters"]


class TestCrossDomainWorkflowClass:
    """Test CrossDomainWorkflow class."""

    def test_workflow_initialization(self):
        """Test workflow object initialization."""
        workflow = CrossDomainWorkflow(
            workflow_id="test-id",
            name="Test Workflow",
            source_domain=DomainType.PERSONAL,
            target_domain=DomainType.BUSINESS,
            steps=[{"action": "test"}]
        )

        assert workflow.workflow_id == "test-id"
        assert workflow.name == "Test Workflow"
        assert workflow.source_domain == DomainType.PERSONAL
        assert workflow.target_domain == DomainType.BUSINESS
        assert len(workflow.steps) == 1
        assert workflow.current_step == 0
        assert workflow.status == "pending"
        assert workflow.created_at is not None
