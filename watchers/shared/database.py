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

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_actions_status ON actions(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_actions_created ON actions(created_timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_status ON events(processing_status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)")

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

    def close(self):
        """Close database connection."""
        self.conn.close()
