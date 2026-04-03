"""
Action Queue Processor for Digital FTE

Processes queued actions when integrations recover from failures.
Works with the circuit breaker pattern to execute actions that were
queued during degraded mode.

Usage:
    processor = QueueProcessor()
    processor.process_queue()  # Process all ready actions
    processor.process_integration_queue("odoo")  # Process specific integration
"""

import logging
import uuid
from typing import Dict, Any, Optional, Callable
from datetime import datetime

from watchers.shared.database import Database


logger = logging.getLogger(__name__)


class QueueProcessor:
    """
    Processes queued actions when integrations recover.

    Monitors integration status and executes queued actions when
    circuit breakers transition from OPEN to CLOSED state.
    """

    def __init__(self, db: Optional[Database] = None):
        """
        Initialize queue processor.

        Args:
            db: Database instance (creates new if None)
        """
        self.db = db or Database()
        self.action_handlers: Dict[str, Callable] = {}

    def register_handler(self, action_type: str, handler: Callable) -> None:
        """
        Register a handler function for an action type.

        Args:
            action_type: Action type (e.g., "odoo_record_transaction")
            handler: Callable that executes the action
        """
        self.action_handlers[action_type] = handler
        logger.info(f"Registered handler for action type: {action_type}")

    def process_queue(self, max_actions: int = 100) -> Dict[str, Any]:
        """
        Process all queued actions that are ready for execution.

        Args:
            max_actions: Maximum number of actions to process

        Returns:
            Processing statistics
        """
        logger.info("Starting queue processing")

        # Get all integration statuses
        integration_statuses = self.db.get_all_integration_statuses()

        # Filter for healthy integrations (circuit breaker CLOSED)
        healthy_integrations = [
            status["integration_name"]
            for status in integration_statuses
            if status["circuit_breaker_state"] == "closed"
        ]

        if not healthy_integrations:
            logger.info("No healthy integrations available for queue processing")
            return {
                "processed": 0,
                "succeeded": 0,
                "failed": 0,
                "skipped": 0,
                "healthy_integrations": []
            }

        logger.info(f"Healthy integrations: {healthy_integrations}")

        # Process queued actions for healthy integrations
        total_processed = 0
        total_succeeded = 0
        total_failed = 0
        total_skipped = 0

        for integration_name in healthy_integrations:
            stats = self.process_integration_queue(integration_name, max_actions)
            total_processed += stats["processed"]
            total_succeeded += stats["succeeded"]
            total_failed += stats["failed"]
            total_skipped += stats["skipped"]

        logger.info(
            f"Queue processing complete: {total_processed} processed, "
            f"{total_succeeded} succeeded, {total_failed} failed, {total_skipped} skipped"
        )

        return {
            "processed": total_processed,
            "succeeded": total_succeeded,
            "failed": total_failed,
            "skipped": total_skipped,
            "healthy_integrations": healthy_integrations,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

    def process_integration_queue(self, integration_name: str,
                                  max_actions: int = 100) -> Dict[str, Any]:
        """
        Process queued actions for a specific integration.

        Args:
            integration_name: Name of the integration
            max_actions: Maximum number of actions to process

        Returns:
            Processing statistics for this integration
        """
        logger.info(f"Processing queue for integration: {integration_name}")

        # Check integration status
        status = self.db.get_integration_status(integration_name)
        if not status or status["circuit_breaker_state"] != "closed":
            logger.warning(
                f"Integration {integration_name} not healthy, skipping queue processing"
            )
            return {
                "integration": integration_name,
                "processed": 0,
                "succeeded": 0,
                "failed": 0,
                "skipped": 0,
                "reason": "integration_not_healthy"
            }

        # Get queued actions for this integration
        queued_actions = self.db.get_queued_actions(
            integration_name=integration_name,
            limit=max_actions
        )

        if not queued_actions:
            logger.info(f"No queued actions for {integration_name}")
            return {
                "integration": integration_name,
                "processed": 0,
                "succeeded": 0,
                "failed": 0,
                "skipped": 0
            }

        logger.info(f"Found {len(queued_actions)} queued actions for {integration_name}")

        processed = 0
        succeeded = 0
        failed = 0
        skipped = 0

        for action in queued_actions:
            try:
                result = self._execute_action(action)

                if result["success"]:
                    succeeded += 1
                    self.db.remove_queued_action(action["id"])
                    logger.info(f"Successfully executed queued action {action['id']}")
                else:
                    failed += 1
                    # Update action with error, keep in queue for retry
                    self.db.update_queued_action(
                        action["id"],
                        status="queued",
                        last_error=result.get("error", "Unknown error")
                    )
                    logger.error(
                        f"Failed to execute queued action {action['id']}: "
                        f"{result.get('error')}"
                    )

                processed += 1

            except Exception as e:
                logger.exception(f"Error processing queued action {action['id']}: {e}")
                failed += 1
                self.db.update_queued_action(
                    action["id"],
                    status="queued",
                    last_error=str(e)
                )

        return {
            "integration": integration_name,
            "processed": processed,
            "succeeded": succeeded,
            "failed": failed,
            "skipped": skipped
        }

    def _execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a queued action.

        Args:
            action: Action dict from database

        Returns:
            Execution result dict with success flag and optional error
        """
        action_type = action["action_type"]
        parameters = action["parameters"]

        # Check if handler is registered
        if action_type not in self.action_handlers:
            logger.warning(f"No handler registered for action type: {action_type}")
            return {
                "success": False,
                "error": f"No handler registered for action type: {action_type}"
            }

        # Execute handler
        try:
            handler = self.action_handlers[action_type]
            result = handler(**parameters)

            return {
                "success": True,
                "result": result
            }

        except Exception as e:
            logger.exception(f"Handler execution failed for {action_type}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_queue_status(self) -> Dict[str, Any]:
        """
        Get current queue status.

        Returns:
            Queue status dict
        """
        stats = self.db.get_queue_stats()

        # Get integration statuses
        integration_statuses = self.db.get_all_integration_statuses()

        # Count healthy vs unhealthy integrations
        healthy_count = sum(
            1 for status in integration_statuses
            if status["circuit_breaker_state"] == "closed"
        )
        unhealthy_count = len(integration_statuses) - healthy_count

        return {
            "queue_stats": stats,
            "integrations": {
                "total": len(integration_statuses),
                "healthy": healthy_count,
                "unhealthy": unhealthy_count
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

    def cleanup_old_actions(self, max_age_days: int = 7,
                           max_attempts: int = 10) -> int:
        """
        Clean up old or repeatedly failed actions from the queue.

        Args:
            max_age_days: Remove actions older than this many days
            max_attempts: Remove actions with more than this many attempts

        Returns:
            Number of actions removed
        """
        logger.info(
            f"Cleaning up actions older than {max_age_days} days "
            f"or with more than {max_attempts} attempts"
        )

        cursor = self.db.conn.cursor()

        # Calculate cutoff date
        from datetime import timedelta
        cutoff_date = (datetime.utcnow() - timedelta(days=max_age_days)).isoformat() + "Z"

        # Delete old or repeatedly failed actions
        cursor.execute("""
            DELETE FROM action_queue
            WHERE created_at < ? OR attempts > ?
        """, (cutoff_date, max_attempts))

        removed_count = cursor.rowcount
        self.db.conn.commit()

        logger.info(f"Removed {removed_count} old/failed actions from queue")
        return removed_count
