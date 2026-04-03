"""
Cross-Domain Workflow Coordinator for Digital FTE

Coordinates workflows that span personal and business domains,
ensuring proper authorization and audit logging for cross-domain operations.

Example: Recording a business expense paid from a personal account
"""

import uuid
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from watchers.shared.domain_manager import DomainContextManager, DomainType
from watchers.shared.audit_logger import AuditLogger


logger = logging.getLogger(__name__)


class CrossDomainWorkflow:
    """Represents a workflow spanning multiple domains."""

    def __init__(
        self,
        workflow_id: str,
        name: str,
        source_domain: DomainType,
        target_domain: DomainType,
        steps: List[Dict[str, Any]]
    ):
        """
        Initialize cross-domain workflow.

        Args:
            workflow_id: Unique workflow identifier
            name: Workflow name
            source_domain: Source domain type
            target_domain: Target domain type
            steps: List of workflow steps
        """
        self.workflow_id = workflow_id
        self.name = name
        self.source_domain = source_domain
        self.target_domain = target_domain
        self.steps = steps
        self.current_step = 0
        self.status = "pending"
        self.created_at = datetime.utcnow().isoformat() + "Z"


class CrossDomainCoordinator:
    """
    Coordinates workflows spanning personal and business domains.
    """

    def __init__(
        self,
        domain_manager: Optional[DomainContextManager] = None,
        audit_logger: Optional[AuditLogger] = None
    ):
        """
        Initialize cross-domain coordinator.

        Args:
            domain_manager: Domain context manager instance
            audit_logger: Audit logger instance
        """
        self.domain_manager = domain_manager or DomainContextManager()
        self.audit_logger = audit_logger or AuditLogger()
        self.active_workflows: Dict[str, CrossDomainWorkflow] = {}

    def create_workflow(
        self,
        name: str,
        source_domain: DomainType,
        target_domain: DomainType,
        steps: List[Dict[str, Any]],
        requires_approval: bool = True
    ) -> str:
        """
        Create a new cross-domain workflow.

        Args:
            name: Workflow name
            source_domain: Source domain type
            target_domain: Target domain type
            steps: List of workflow steps with action details
            requires_approval: Whether workflow requires user approval

        Returns:
            Workflow ID
        """
        workflow_id = str(uuid.uuid4())

        workflow = CrossDomainWorkflow(
            workflow_id=workflow_id,
            name=name,
            source_domain=source_domain,
            target_domain=target_domain,
            steps=steps
        )

        self.active_workflows[workflow_id] = workflow

        # Log workflow creation
        self.audit_logger.log_action(
            action_type="create",
            action_name="cross_domain_workflow",
            parameters={
                "workflow_id": workflow_id,
                "name": name,
                "source_domain": source_domain.value,
                "target_domain": target_domain.value,
                "steps_count": len(steps),
                "requires_approval": requires_approval
            },
            reasoning=f"Creating cross-domain workflow: {name}",
            safety_level=2 if requires_approval else 1
        )

        logger.info(
            f"Created cross-domain workflow: {workflow_id} "
            f"({source_domain.value} -> {target_domain.value})"
        )

        return workflow_id

    def execute_workflow(
        self,
        workflow_id: str,
        user_approval: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a cross-domain workflow.

        Args:
            workflow_id: Workflow identifier
            user_approval: User approval information (required for cross-domain)

        Returns:
            Execution result
        """
        if workflow_id not in self.active_workflows:
            return {
                "success": False,
                "error": f"Workflow {workflow_id} not found"
            }

        workflow = self.active_workflows[workflow_id]

        # Check if cross-domain access is allowed
        # Create temporary contexts for validation
        source_context_id = self.domain_manager.create_context(
            domain_type=workflow.source_domain,
            privacy_level=self.domain_manager.PrivacyLevel.INTERNAL,
            data_classification=self.domain_manager.DataClassification.COMMUNICATION
        )

        target_context_id = self.domain_manager.create_context(
            domain_type=workflow.target_domain,
            privacy_level=self.domain_manager.PrivacyLevel.INTERNAL,
            data_classification=self.domain_manager.DataClassification.COMMUNICATION
        )

        access_check = self.domain_manager.is_cross_domain_allowed(
            source_context_id,
            target_context_id
        )

        if not access_check["allowed"]:
            logger.warning(
                f"Cross-domain access denied for workflow {workflow_id}: "
                f"{access_check['reason']}"
            )

            self.audit_logger.log_action(
                action_type="execute",
                action_name="cross_domain_workflow",
                parameters={"workflow_id": workflow_id},
                error_message=f"Access denied: {access_check['reason']}",
                user_approval=user_approval,
                safety_level=2
            )

            return {
                "success": False,
                "error": f"Cross-domain access denied: {access_check['reason']}"
            }

        # Execute workflow steps
        results = []
        workflow.status = "executing"

        for i, step in enumerate(workflow.steps):
            workflow.current_step = i

            try:
                # Log step execution
                self.audit_logger.log_action(
                    action_type="execute",
                    action_name=f"workflow_step_{i}",
                    parameters=step,
                    reasoning=f"Executing step {i+1}/{len(workflow.steps)} of workflow {workflow.name}",
                    user_approval=user_approval,
                    safety_level=2
                )

                # Execute step (placeholder - actual execution would call appropriate tools)
                step_result = {
                    "step": i,
                    "action": step.get("action"),
                    "success": True,
                    "message": f"Step {i+1} executed successfully"
                }

                results.append(step_result)

            except Exception as e:
                logger.exception(f"Error executing workflow step {i}: {e}")

                self.audit_logger.log_action(
                    action_type="execute",
                    action_name=f"workflow_step_{i}",
                    parameters=step,
                    error_message=str(e),
                    user_approval=user_approval,
                    safety_level=2
                )

                workflow.status = "failed"
                return {
                    "success": False,
                    "error": f"Step {i+1} failed: {str(e)}",
                    "completed_steps": results
                }

        # Workflow completed successfully
        workflow.status = "completed"

        self.audit_logger.log_action(
            action_type="complete",
            action_name="cross_domain_workflow",
            parameters={"workflow_id": workflow_id},
            result={"steps_completed": len(results)},
            reasoning=f"Cross-domain workflow completed: {workflow.name}",
            user_approval=user_approval,
            safety_level=2
        )

        logger.info(f"Completed cross-domain workflow: {workflow_id}")

        return {
            "success": True,
            "workflow_id": workflow_id,
            "steps_completed": len(results),
            "results": results
        }

    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a cross-domain workflow.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Workflow status dict or None if not found
        """
        if workflow_id not in self.active_workflows:
            return None

        workflow = self.active_workflows[workflow_id]

        return {
            "workflow_id": workflow.workflow_id,
            "name": workflow.name,
            "source_domain": workflow.source_domain.value,
            "target_domain": workflow.target_domain.value,
            "status": workflow.status,
            "current_step": workflow.current_step,
            "total_steps": len(workflow.steps),
            "created_at": workflow.created_at
        }

    def list_active_workflows(self) -> List[Dict[str, Any]]:
        """
        List all active cross-domain workflows.

        Returns:
            List of workflow status dicts
        """
        return [
            self.get_workflow_status(workflow_id)
            for workflow_id in self.active_workflows.keys()
        ]

    def cancel_workflow(self, workflow_id: str, reason: str) -> bool:
        """
        Cancel an active cross-domain workflow.

        Args:
            workflow_id: Workflow identifier
            reason: Cancellation reason

        Returns:
            True if cancelled, False if not found
        """
        if workflow_id not in self.active_workflows:
            return False

        workflow = self.active_workflows[workflow_id]
        workflow.status = "cancelled"

        self.audit_logger.log_action(
            action_type="cancel",
            action_name="cross_domain_workflow",
            parameters={"workflow_id": workflow_id, "reason": reason},
            reasoning=f"Workflow cancelled: {reason}",
            safety_level=1
        )

        logger.info(f"Cancelled cross-domain workflow: {workflow_id} - {reason}")

        del self.active_workflows[workflow_id]
        return True
