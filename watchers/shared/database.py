"""SQLite database schema and operations for Digital FTE watchers.

This module provides the database schema for storing watcher state, events,
and action audit trails. All timestamps use ISO 8601 format.
"""

import sqlite3
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime


class Database:
    """SQLite database manager for Digital FTE watchers."""

    def __init__(self, db_path: str = "watchers/shared/digital_fte.db"):
        """Initialize database connection and create schema if needed.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_schema()

    def _create_schema(self):
        """Create database schema if tables don't exist."""
        cursor = self.conn.cursor()

        # Watchers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS watchers (
                watcher_name TEXT PRIMARY KEY,
                health_status TEXT NOT NULL,
                last_check_timestamp TEXT NOT NULL,
                error_count INTEGER NOT NULL DEFAULT 0,
                config TEXT NOT NULL
            )
        """)

        # Events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                event_id TEXT PRIMARY KEY,
                source_channel TEXT NOT NULL,
                event_type TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                processing_status TEXT NOT NULL,
                vault_note_path TEXT,
                error_message TEXT
            )
        """)

        # Actions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS actions (
                action_id TEXT PRIMARY KEY,
                action_type TEXT NOT NULL,
                parameters TEXT NOT NULL,
                safety_level INTEGER NOT NULL,
                status TEXT NOT NULL,
                created_timestamp TEXT NOT NULL,
                approved_timestamp TEXT,
                executed_timestamp TEXT,
                approver TEXT,
                rejection_reason TEXT,
                execution_result TEXT,
                audit_trail TEXT NOT NULL
            )
        """)

        # Integration Status table (for circuit breaker state)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS integration_status (
                integration_name TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                circuit_breaker_state TEXT NOT NULL,
                error_count INTEGER NOT NULL DEFAULT 0,
                success_count INTEGER NOT NULL DEFAULT 0,
                error_rate REAL NOT NULL DEFAULT 0.0,
                last_success_at TEXT,
                last_failure_at TEXT,
                recovery_attempt INTEGER NOT NULL DEFAULT 0,
                next_recovery_at TEXT,
                updated_at TEXT NOT NULL
            )
        """)

        # Action Queue table (for degraded mode operations)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS action_queue (
                id TEXT PRIMARY KEY,
                action_type TEXT NOT NULL,
                parameters TEXT NOT NULL,
                integration_name TEXT NOT NULL,
                priority INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                scheduled_for TEXT,
                attempts INTEGER NOT NULL DEFAULT 0,
                last_attempt_at TEXT,
                last_error TEXT,
                status TEXT NOT NULL
            )
        """)

        # Audit Log table (for comprehensive audit trail with hash chain)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id TEXT PRIMARY KEY,
                sequence_number INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                action_type TEXT NOT NULL,
                action_name TEXT NOT NULL,
                parameters TEXT NOT NULL,
                result TEXT,
                error_message TEXT,
                reasoning TEXT,
                user_approval TEXT,
                safety_level INTEGER NOT NULL,
                previous_entry_hash TEXT,
                entry_hash TEXT NOT NULL,
                UNIQUE(sequence_number)
            )
        """)

        # Domain Context table (for cross-domain integration)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS domain_context (
                id TEXT PRIMARY KEY,
                domain_type TEXT NOT NULL,
                privacy_level TEXT NOT NULL,
                data_classification TEXT NOT NULL,
                created_at TEXT NOT NULL,
                metadata TEXT
            )
        """)

        # Business Transactions table (for Odoo accounting integration)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS business_transactions (
                id TEXT PRIMARY KEY,
                external_id TEXT NOT NULL UNIQUE,
                amount REAL NOT NULL,
                currency TEXT NOT NULL DEFAULT 'USD',
                date TEXT NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT,
                description TEXT NOT NULL,
                partner_name TEXT,
                partner_id TEXT,
                account_code TEXT NOT NULL,
                move_type TEXT NOT NULL,
                state TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                duplicate_check_hash TEXT NOT NULL,
                CHECK (amount > 0),
                CHECK (category IN ('Revenue', 'COGS', 'Operating Expenses', 'Assets', 'Liabilities', 'Equity')),
                CHECK (move_type IN ('invoice', 'payment', 'expense', 'refund')),
                CHECK (state IN ('draft', 'posted', 'cancelled'))
            )
        """)

        # CEO Briefings table (for weekly executive summaries)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ceo_briefings (
                id TEXT PRIMARY KEY,
                week_number INTEGER NOT NULL,
                year INTEGER NOT NULL,
                period_start TEXT NOT NULL,
                period_end TEXT NOT NULL,
                generated_at TEXT NOT NULL,
                financial_summary TEXT NOT NULL,
                social_media_summary TEXT NOT NULL,
                tasks_completed INTEGER NOT NULL DEFAULT 0,
                tasks_pending INTEGER NOT NULL DEFAULT 0,
                critical_issues TEXT NOT NULL,
                status TEXT NOT NULL,
                markdown_path TEXT NOT NULL,
                CHECK (week_number >= 1 AND week_number <= 53),
                CHECK (status IN ('generating', 'complete', 'failed')),
                UNIQUE(year, week_number)
            )
        """)

        # Social Media Posts table (for social media management)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS social_media_posts (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                media_urls TEXT,
                platforms TEXT NOT NULL,
                scheduled_time TEXT NOT NULL,
                published_time TEXT,
                status TEXT NOT NULL,
                platform_ids TEXT,
                engagement_metrics TEXT,
                approval_status TEXT NOT NULL,
                approval_timestamp TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                CHECK (status IN ('draft', 'scheduled', 'published', 'failed')),
                CHECK (approval_status IN ('pending', 'approved', 'rejected'))
            )
        """)

        # Multi-Step Tasks table (for autonomous task completion)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS multi_step_tasks (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                assigned_to TEXT NOT NULL,
                priority TEXT NOT NULL,
                status TEXT NOT NULL,
                steps TEXT NOT NULL,
                current_step_index INTEGER NOT NULL DEFAULT 0,
                completion_criteria TEXT NOT NULL,
                parent_task_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                completed_at TEXT,
                summary_path TEXT,
                CHECK (priority IN ('low', 'medium', 'high', 'critical')),
                CHECK (status IN ('pending', 'in_progress', 'blocked', 'completed', 'failed', 'cancelled')),
                CHECK (current_step_index >= 0),
                FOREIGN KEY (parent_task_id) REFERENCES multi_step_tasks(id)
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_actions_status ON actions(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_actions_created ON actions(created_timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_status ON events(processing_status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_integration_status ON integration_status(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_integration_circuit_state ON integration_status(circuit_breaker_state)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_action_queue_status ON action_queue(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_action_queue_integration ON action_queue(integration_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_action_queue_scheduled ON action_queue(scheduled_for)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_log_action_type ON audit_log(action_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_log_sequence ON audit_log(sequence_number)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_domain_context_type ON domain_context(domain_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_date ON business_transactions(date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_category ON business_transactions(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_duplicate_hash ON business_transactions(duplicate_check_hash)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_external_id ON business_transactions(external_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_briefings_year_week ON ceo_briefings(year, week_number)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_briefings_status ON ceo_briefings(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_briefings_generated_at ON ceo_briefings(generated_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_social_posts_status ON social_media_posts(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_social_posts_scheduled_time ON social_media_posts(scheduled_time)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_social_posts_published_time ON social_media_posts(published_time)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_social_posts_approval_status ON social_media_posts(approval_status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_multi_step_tasks_status ON multi_step_tasks(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_multi_step_tasks_priority ON multi_step_tasks(priority)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_multi_step_tasks_assigned_to ON multi_step_tasks(assigned_to)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_multi_step_tasks_parent ON multi_step_tasks(parent_task_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_multi_step_tasks_created_at ON multi_step_tasks(created_at)")

        self.conn.commit()

    def update_watcher_health(self, watcher_name: str, health_status: str,
                             error_count: int = 0, config: Optional[Dict[str, Any]] = None):
        """Update watcher health status.

        Args:
            watcher_name: Name of the watcher (gmail, whatsapp, linkedin)
            health_status: Health status (healthy, degraded, unhealthy)
            error_count: Number of consecutive errors
            config: Watcher configuration as dict
        """
        cursor = self.conn.cursor()
        timestamp = datetime.utcnow().isoformat() + "Z"
        config_json = json.dumps(config or {})

        cursor.execute("""
            INSERT OR REPLACE INTO watchers
            (watcher_name, health_status, last_check_timestamp, error_count, config)
            VALUES (?, ?, ?, ?, ?)
        """, (watcher_name, health_status, timestamp, error_count, config_json))

        self.conn.commit()

    def log_event(self, event_id: str, source_channel: str, event_type: str,
                  content: Dict[str, Any], processing_status: str = "pending",
                  vault_note_path: Optional[str] = None, error_message: Optional[str] = None):
        """Log a watcher event.

        Args:
            event_id: Unique event identifier (UUID)
            source_channel: Source channel (gmail, whatsapp, linkedin)
            event_type: Event type (email, message, notification)
            content: Event content as dict
            processing_status: Processing status (pending, processed, failed)
            vault_note_path: Path to created vault note
            error_message: Error message if processing failed
        """
        cursor = self.conn.cursor()
        timestamp = datetime.utcnow().isoformat() + "Z"
        content_json = json.dumps(content)

        cursor.execute("""
            INSERT INTO events
            (event_id, source_channel, event_type, content, timestamp,
             processing_status, vault_note_path, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (event_id, source_channel, event_type, content_json, timestamp,
              processing_status, vault_note_path, error_message))

        self.conn.commit()

    def update_event_status(self, event_id: str, processing_status: str,
                           vault_note_path: Optional[str] = None,
                           error_message: Optional[str] = None):
        """Update event processing status.

        Args:
            event_id: Event identifier
            processing_status: New status (processed, failed)
            vault_note_path: Path to created vault note
            error_message: Error message if failed
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE events
            SET processing_status = ?, vault_note_path = ?, error_message = ?
            WHERE event_id = ?
        """, (processing_status, vault_note_path, error_message, event_id))

        self.conn.commit()

    def log_action(self, action_id: str, action_type: str, parameters: Dict[str, Any],
                   safety_level: int, status: str = "pending"):
        """Log an action for audit trail.

        Args:
            action_id: Unique action identifier (UUID)
            action_type: Action type (send-email, linkedin-post, whatsapp-send)
            parameters: Action parameters as dict
            safety_level: Safety level (0-3)
            status: Action status (pending, approved, rejected, executed)
        """
        cursor = self.conn.cursor()
        timestamp = datetime.utcnow().isoformat() + "Z"
        parameters_json = json.dumps(parameters)
        audit_trail = json.dumps([{
            "timestamp": timestamp,
            "status": status,
            "event": "action_created"
        }])

        cursor.execute("""
            INSERT INTO actions
            (action_id, action_type, parameters, safety_level, status,
             created_timestamp, audit_trail)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (action_id, action_type, parameters_json, safety_level, status,
              timestamp, audit_trail))

        self.conn.commit()

    def update_action_status(self, action_id: str, status: str,
                            approver: Optional[str] = None,
                            rejection_reason: Optional[str] = None,
                            execution_result: Optional[Dict[str, Any]] = None):
        """Update action status and audit trail.

        Args:
            action_id: Action identifier
            status: New status (approved, rejected, executed, failed)
            approver: Username who approved/rejected
            rejection_reason: Reason for rejection
            execution_result: Execution result as dict
        """
        cursor = self.conn.cursor()
        timestamp = datetime.utcnow().isoformat() + "Z"

        # Get current audit trail
        cursor.execute("SELECT audit_trail FROM actions WHERE action_id = ?", (action_id,))
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Action {action_id} not found")

        audit_trail = json.loads(row["audit_trail"])
        audit_trail.append({
            "timestamp": timestamp,
            "status": status,
            "event": f"status_changed_to_{status}",
            "approver": approver,
            "rejection_reason": rejection_reason
        })

        # Update action
        update_fields = {
            "status": status,
            "audit_trail": json.dumps(audit_trail)
        }

        if status == "approved":
            update_fields["approved_timestamp"] = timestamp
            update_fields["approver"] = approver
        elif status == "rejected":
            update_fields["rejection_reason"] = rejection_reason
            update_fields["approver"] = approver
        elif status in ("executed", "failed"):
            update_fields["executed_timestamp"] = timestamp
            if execution_result:
                update_fields["execution_result"] = json.dumps(execution_result)

        set_clause = ", ".join(f"{k} = ?" for k in update_fields.keys())
        values = list(update_fields.values()) + [action_id]

        cursor.execute(f"UPDATE actions SET {set_clause} WHERE action_id = ?", values)
        self.conn.commit()

    def get_watcher_health(self, watcher_name: str) -> Optional[Dict[str, Any]]:
        """Get watcher health status.

        Args:
            watcher_name: Name of the watcher

        Returns:
            Dict with health status or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM watchers WHERE watcher_name = ?", (watcher_name,))
        row = cursor.fetchone()

        if row:
            return {
                "watcher_name": row["watcher_name"],
                "health_status": row["health_status"],
                "last_check_timestamp": row["last_check_timestamp"],
                "error_count": row["error_count"],
                "config": json.loads(row["config"])
            }
        return None

    def get_pending_actions(self) -> List[Dict[str, Any]]:
        """Get all pending actions awaiting approval.

        Returns:
            List of pending actions
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM actions
            WHERE status = 'pending'
            ORDER BY created_timestamp ASC
        """)

        actions = []
        for row in cursor.fetchall():
            actions.append({
                "action_id": row["action_id"],
                "action_type": row["action_type"],
                "parameters": json.loads(row["parameters"]),
                "safety_level": row["safety_level"],
                "status": row["status"],
                "created_timestamp": row["created_timestamp"],
                "audit_trail": json.loads(row["audit_trail"])
            })

        return actions

    def update_integration_status(self, integration_name: str, status: str,
                                  circuit_breaker_state: str, error_count: int = 0,
                                  success_count: int = 0, error_rate: float = 0.0,
                                  last_success_at: Optional[str] = None,
                                  last_failure_at: Optional[str] = None,
                                  recovery_attempt: int = 0,
                                  next_recovery_at: Optional[str] = None):
        """Update integration status for circuit breaker tracking.

        Args:
            integration_name: Name of the integration (odoo, facebook, instagram, twitter)
            status: Integration status (healthy, degraded, unhealthy)
            circuit_breaker_state: Circuit breaker state (closed, open, half_open)
            error_count: Total error count
            success_count: Total success count
            error_rate: Current error rate (0.0-1.0)
            last_success_at: ISO timestamp of last successful call
            last_failure_at: ISO timestamp of last failed call
            recovery_attempt: Current recovery attempt number
            next_recovery_at: ISO timestamp of next recovery attempt
        """
        cursor = self.conn.cursor()
        timestamp = datetime.utcnow().isoformat() + "Z"

        cursor.execute("""
            INSERT OR REPLACE INTO integration_status
            (integration_name, status, circuit_breaker_state, error_count, success_count,
             error_rate, last_success_at, last_failure_at, recovery_attempt,
             next_recovery_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (integration_name, status, circuit_breaker_state, error_count, success_count,
              error_rate, last_success_at, last_failure_at, recovery_attempt,
              next_recovery_at, timestamp))

        self.conn.commit()

    def get_integration_status(self, integration_name: str) -> Optional[Dict[str, Any]]:
        """Get integration status.

        Args:
            integration_name: Name of the integration

        Returns:
            Dict with integration status or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM integration_status WHERE integration_name = ?",
                      (integration_name,))
        row = cursor.fetchone()

        if row:
            return {
                "integration_name": row["integration_name"],
                "status": row["status"],
                "circuit_breaker_state": row["circuit_breaker_state"],
                "error_count": row["error_count"],
                "success_count": row["success_count"],
                "error_rate": row["error_rate"],
                "last_success_at": row["last_success_at"],
                "last_failure_at": row["last_failure_at"],
                "recovery_attempt": row["recovery_attempt"],
                "next_recovery_at": row["next_recovery_at"],
                "updated_at": row["updated_at"]
            }
        return None

    def get_all_integration_statuses(self) -> List[Dict[str, Any]]:
        """Get all integration statuses.

        Returns:
            List of all integration statuses
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM integration_status ORDER BY integration_name")

        statuses = []
        for row in cursor.fetchall():
            statuses.append({
                "integration_name": row["integration_name"],
                "status": row["status"],
                "circuit_breaker_state": row["circuit_breaker_state"],
                "error_count": row["error_count"],
                "success_count": row["success_count"],
                "error_rate": row["error_rate"],
                "last_success_at": row["last_success_at"],
                "last_failure_at": row["last_failure_at"],
                "recovery_attempt": row["recovery_attempt"],
                "next_recovery_at": row["next_recovery_at"],
                "updated_at": row["updated_at"]
            })

        return statuses

    def enqueue_action(self, action_id: str, action_type: str, parameters: Dict[str, Any],
                      integration_name: str, priority: int = 0,
                      scheduled_for: Optional[str] = None) -> None:
        """Enqueue an action for later execution when integration recovers.

        Args:
            action_id: Unique action identifier (UUID)
            action_type: Action type (e.g., odoo_record_transaction, social_post)
            parameters: Action parameters as dict
            integration_name: Name of the integration (odoo, facebook, instagram, twitter)
            priority: Priority level (higher = more urgent)
            scheduled_for: ISO timestamp for when to execute (None = ASAP)
        """
        cursor = self.conn.cursor()
        timestamp = datetime.utcnow().isoformat() + "Z"
        parameters_json = json.dumps(parameters)

        cursor.execute("""
            INSERT INTO action_queue
            (id, action_type, parameters, integration_name, priority, created_at,
             scheduled_for, attempts, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0, 'queued')
        """, (action_id, action_type, parameters_json, integration_name, priority,
              timestamp, scheduled_for))

        self.conn.commit()

    def get_queued_actions(self, integration_name: Optional[str] = None,
                          limit: int = 100) -> List[Dict[str, Any]]:
        """Get queued actions ready for execution.

        Args:
            integration_name: Filter by integration name (None = all)
            limit: Maximum number of actions to return

        Returns:
            List of queued actions sorted by priority and creation time
        """
        cursor = self.conn.cursor()
        now = datetime.utcnow().isoformat() + "Z"

        if integration_name:
            cursor.execute("""
                SELECT * FROM action_queue
                WHERE status = 'queued'
                  AND integration_name = ?
                  AND (scheduled_for IS NULL OR scheduled_for <= ?)
                ORDER BY priority DESC, created_at ASC
                LIMIT ?
            """, (integration_name, now, limit))
        else:
            cursor.execute("""
                SELECT * FROM action_queue
                WHERE status = 'queued'
                  AND (scheduled_for IS NULL OR scheduled_for <= ?)
                ORDER BY priority DESC, created_at ASC
                LIMIT ?
            """, (now, limit))

        actions = []
        for row in cursor.fetchall():
            actions.append({
                "id": row["id"],
                "action_type": row["action_type"],
                "parameters": json.loads(row["parameters"]),
                "integration_name": row["integration_name"],
                "priority": row["priority"],
                "created_at": row["created_at"],
                "scheduled_for": row["scheduled_for"],
                "attempts": row["attempts"],
                "last_attempt_at": row["last_attempt_at"],
                "last_error": row["last_error"],
                "status": row["status"]
            })

        return actions

    def update_queued_action(self, action_id: str, status: str,
                            last_error: Optional[str] = None) -> None:
        """Update queued action status after execution attempt.

        Args:
            action_id: Action identifier
            status: New status (queued, executing, completed, failed)
            last_error: Error message if execution failed
        """
        cursor = self.conn.cursor()
        timestamp = datetime.utcnow().isoformat() + "Z"

        # Increment attempts counter
        cursor.execute("""
            UPDATE action_queue
            SET status = ?,
                attempts = attempts + 1,
                last_attempt_at = ?,
                last_error = ?
            WHERE id = ?
        """, (status, timestamp, last_error, action_id))

        self.conn.commit()

    def remove_queued_action(self, action_id: str) -> None:
        """Remove a completed or failed action from the queue.

        Args:
            action_id: Action identifier
        """
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM action_queue WHERE id = ?", (action_id,))
        self.conn.commit()

    def get_queue_stats(self) -> Dict[str, Any]:
        """Get action queue statistics.

        Returns:
            Dict with queue statistics
        """
        cursor = self.conn.cursor()

        # Total queued actions
        cursor.execute("SELECT COUNT(*) as count FROM action_queue WHERE status = 'queued'")
        queued_count = cursor.fetchone()["count"]

        # Actions by integration
        cursor.execute("""
            SELECT integration_name, COUNT(*) as count
            FROM action_queue
            WHERE status = 'queued'
            GROUP BY integration_name
        """)
        by_integration = {row["integration_name"]: row["count"] for row in cursor.fetchall()}

        # Failed actions (attempts > 3)
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM action_queue
            WHERE status = 'queued' AND attempts >= 3
        """)
        failed_count = cursor.fetchone()["count"]

        return {
            "total_queued": queued_count,
            "by_integration": by_integration,
            "failed_attempts": failed_count,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

    def close(self):
        """Close database connection."""
        self.conn.close()
