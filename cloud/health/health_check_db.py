"""
Health Check Database for Platinum Tier

SQLite database for storing health check history.
Tracks check results, manual interventions, and recovery actions.

Based on spec.md FR-031 through FR-034, SC-008 and User Story 5.
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

from cloud.health.health_status import HealthCheck, ServiceType, HealthStatus


class HealthCheckDatabase:
    """
    SQLite database for health check history.

    Stores:
    - Health check results (90-day retention per FR-034)
    - Manual interventions (for SC-008 metric)
    - Automatic recovery actions
    - Alert history
    """

    def __init__(self, db_path: Path):
        """
        Initialize health check database.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger("health_check_db")

        self._init_schema()

    def _init_schema(self) -> None:
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Health checks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS health_checks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    checked_at TIMESTAMP NOT NULL,
                    response_time_seconds REAL,
                    error_message TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Index for efficient queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_health_checks_service_time
                ON health_checks(service_type, checked_at DESC)
            """)

            # Manual interventions table (for SC-008 metric)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS manual_interventions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service_type TEXT NOT NULL,
                    intervention_type TEXT NOT NULL,
                    reason TEXT,
                    performed_by TEXT,
                    performed_at TIMESTAMP NOT NULL,
                    resolution_notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Automatic recovery actions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS recovery_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service_type TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    triggered_by TEXT,
                    success BOOLEAN NOT NULL,
                    error_message TEXT,
                    performed_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Alerts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service_type TEXT NOT NULL,
                    alert_priority TEXT NOT NULL,
                    alert_channels TEXT,
                    message TEXT,
                    sent_at TIMESTAMP NOT NULL,
                    success BOOLEAN NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.commit()
            self.logger.info("Health check database schema initialized")

    def record_health_check(self, check: HealthCheck) -> int:
        """
        Record a health check result.

        Args:
            check: Health check result

        Returns:
            ID of inserted record
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO health_checks (
                    service_type, status, checked_at,
                    response_time_seconds, error_message, metadata
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                check.service_type.value,
                check.status.value,
                check.checked_at.isoformat(),
                check.response_time_seconds,
                check.error_message,
                str(check.metadata) if check.metadata else None
            ))

            conn.commit()
            return cursor.lastrowid

    def record_manual_intervention(
        self,
        service_type: ServiceType,
        intervention_type: str,
        reason: str,
        performed_by: str,
        resolution_notes: Optional[str] = None
    ) -> int:
        """
        Record a manual intervention (for SC-008 metric).

        Args:
            service_type: Service that required intervention
            intervention_type: Type of intervention (restart, config_change, etc)
            reason: Why intervention was needed
            performed_by: Who performed the intervention
            resolution_notes: Notes about the resolution

        Returns:
            ID of inserted record
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO manual_interventions (
                    service_type, intervention_type, reason,
                    performed_by, performed_at, resolution_notes
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                service_type.value,
                intervention_type,
                reason,
                performed_by,
                datetime.now().isoformat(),
                resolution_notes
            ))

            conn.commit()
            self.logger.info(
                f"Recorded manual intervention for {service_type.value}: "
                f"{intervention_type}"
            )
            return cursor.lastrowid

    def record_recovery_action(
        self,
        service_type: ServiceType,
        action_type: str,
        success: bool,
        triggered_by: str,
        error_message: Optional[str] = None
    ) -> int:
        """
        Record an automatic recovery action.

        Args:
            service_type: Service being recovered
            action_type: Type of recovery (restart, sync, etc)
            success: Whether recovery succeeded
            triggered_by: What triggered the recovery
            error_message: Error message if recovery failed

        Returns:
            ID of inserted record
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO recovery_actions (
                    service_type, action_type, triggered_by,
                    success, error_message, performed_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                service_type.value,
                action_type,
                triggered_by,
                success,
                error_message,
                datetime.now().isoformat()
            ))

            conn.commit()
            return cursor.lastrowid

    def record_alert(
        self,
        service_type: ServiceType,
        alert_priority: str,
        alert_channels: str,
        message: str,
        success: bool
    ) -> int:
        """
        Record an alert that was sent.

        Args:
            service_type: Service that triggered alert
            alert_priority: Alert priority level
            alert_channels: Channels used (comma-separated)
            message: Alert message
            success: Whether alert was sent successfully

        Returns:
            ID of inserted record
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO alerts (
                    service_type, alert_priority, alert_channels,
                    message, sent_at, success
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                service_type.value,
                alert_priority,
                alert_channels,
                message,
                datetime.now().isoformat(),
                success
            ))

            conn.commit()
            return cursor.lastrowid

    def get_recent_checks(
        self,
        service_type: ServiceType,
        hours: int = 24
    ) -> List[Dict]:
        """
        Get recent health checks for a service.

        Args:
            service_type: Service to query
            hours: Number of hours to look back

        Returns:
            List of health check records
        """
        cutoff = datetime.now() - timedelta(hours=hours)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM health_checks
                WHERE service_type = ? AND checked_at >= ?
                ORDER BY checked_at DESC
            """, (service_type.value, cutoff.isoformat()))

            return [dict(row) for row in cursor.fetchall()]

    def get_manual_intervention_count(
        self,
        days: int = 30
    ) -> int:
        """
        Get count of manual interventions in last N days.

        Used for SC-008 metric: <5 manual interventions per month.

        Args:
            days: Number of days to look back

        Returns:
            Count of manual interventions
        """
        cutoff = datetime.now() - timedelta(days=days)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT COUNT(*) FROM manual_interventions
                WHERE performed_at >= ?
            """, (cutoff.isoformat(),))

            return cursor.fetchone()[0]

    def get_service_uptime_percentage(
        self,
        service_type: ServiceType,
        hours: int = 24
    ) -> float:
        """
        Calculate service uptime percentage.

        Args:
            service_type: Service to calculate uptime for
            hours: Number of hours to look back

        Returns:
            Uptime percentage (0-100)
        """
        cutoff = datetime.now() - timedelta(hours=hours)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Total checks
            cursor.execute("""
                SELECT COUNT(*) FROM health_checks
                WHERE service_type = ? AND checked_at >= ?
            """, (service_type.value, cutoff.isoformat()))
            total_checks = cursor.fetchone()[0]

            if total_checks == 0:
                return 100.0

            # Healthy checks
            cursor.execute("""
                SELECT COUNT(*) FROM health_checks
                WHERE service_type = ? AND checked_at >= ? AND status = ?
            """, (service_type.value, cutoff.isoformat(), HealthStatus.HEALTHY.value))
            healthy_checks = cursor.fetchone()[0]

            return (healthy_checks / total_checks) * 100.0

    def cleanup_old_records(self, days: int = 90) -> int:
        """
        Delete health check records older than N days.

        Args:
            days: Retention period in days (default 90 per FR-034)

        Returns:
            Number of records deleted
        """
        cutoff = datetime.now() - timedelta(days=days)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                DELETE FROM health_checks
                WHERE checked_at < ?
            """, (cutoff.isoformat(),))

            deleted = cursor.rowcount
            conn.commit()

            if deleted > 0:
                self.logger.info(f"Cleaned up {deleted} old health check records")

            return deleted
