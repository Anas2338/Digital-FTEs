"""
Sync Monitor for Platinum Tier

Tracks vault sync status, detects failures, and triggers alerts.
Monitors sync lag and health per FR-017.

Based on spec.md FR-017 and data-model.md Entity 4: Sync Status.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict

from sync.atomic_writer import AtomicWriter


class SyncHealth:
    """Sync health status enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"


class SyncStatus:
    """
    Sync status entity for monitoring.

    Attributes:
        agent_id: Agent identifier (cloud or local)
        last_sync_at: Timestamp of last successful sync
        sync_lag_seconds: Time since last sync
        sync_method: Synchronization method (git)
        conflict_count: Number of conflicts encountered
        last_conflict_at: Timestamp of last conflict
        sync_health: Current health status
        consecutive_failures: Number of consecutive sync failures
        queued_operations: Number of operations queued during sync failure
    """

    def __init__(
        self,
        agent_id: str,
        last_sync_at: Optional[datetime] = None,
        sync_lag_seconds: int = 0,
        sync_method: str = "git",
        conflict_count: int = 0,
        last_conflict_at: Optional[datetime] = None,
        sync_health: str = SyncHealth.HEALTHY,
        consecutive_failures: int = 0,
        queued_operations: int = 0
    ):
        self.agent_id = agent_id
        self.last_sync_at = last_sync_at or datetime.now()
        self.sync_lag_seconds = sync_lag_seconds
        self.sync_method = sync_method
        self.conflict_count = conflict_count
        self.last_conflict_at = last_conflict_at
        self.sync_health = sync_health
        self.consecutive_failures = consecutive_failures
        self.queued_operations = queued_operations

    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        return {
            "agent_id": self.agent_id,
            "last_sync_at": self.last_sync_at.isoformat() if self.last_sync_at else None,
            "sync_lag_seconds": self.sync_lag_seconds,
            "sync_method": self.sync_method,
            "conflict_count": self.conflict_count,
            "last_conflict_at": self.last_conflict_at.isoformat() if self.last_conflict_at else None,
            "sync_health": self.sync_health,
            "consecutive_failures": self.consecutive_failures,
            "queued_operations": self.queued_operations
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'SyncStatus':
        """Deserialize from dictionary."""
        return cls(
            agent_id=data["agent_id"],
            last_sync_at=datetime.fromisoformat(data["last_sync_at"]) if data.get("last_sync_at") else None,
            sync_lag_seconds=data.get("sync_lag_seconds", 0),
            sync_method=data.get("sync_method", "git"),
            conflict_count=data.get("conflict_count", 0),
            last_conflict_at=datetime.fromisoformat(data["last_conflict_at"]) if data.get("last_conflict_at") else None,
            sync_health=data.get("sync_health", SyncHealth.HEALTHY),
            consecutive_failures=data.get("consecutive_failures", 0),
            queued_operations=data.get("queued_operations", 0)
        )


class SyncMonitor:
    """
    Monitors vault synchronization status and health.

    Responsibilities:
    - Track last_sync_at and sync_lag
    - Detect sync failures (lag >5 minutes per FR-017)
    - Alert on extended failures (>1 hour per FR-017)
    - Update sync health status
    """

    def __init__(self, vault_path: Path, agent_id: str):
        """
        Initialize sync monitor.

        Args:
            vault_path: Path to Obsidian vault
            agent_id: Agent identifier (cloud or local)
        """
        self.vault_path = Path(vault_path)
        self.agent_id = agent_id
        self.logger = logging.getLogger(f"sync_monitor_{agent_id}")
        self.status_file = vault_path / ".sync-status" / f"{agent_id}.json"
        self.status_file.parent.mkdir(exist_ok=True)

        self.status = self._load_status()

    def _load_status(self) -> SyncStatus:
        """
        Load sync status from file.

        Returns:
            SyncStatus object
        """
        if self.status_file.exists():
            try:
                with open(self.status_file, 'r') as f:
                    data = json.load(f)
                return SyncStatus.from_dict(data)
            except Exception as e:
                self.logger.error(f"Error loading sync status: {e}")

        # Return new status if file doesn't exist
        return SyncStatus(agent_id=self.agent_id)

    def _save_status(self) -> None:
        """Save sync status to file."""
        try:
            AtomicWriter.write(
                self.status_file,
                json.dumps(self.status.to_dict(), indent=2)
            )
        except Exception as e:
            self.logger.error(f"Error saving sync status: {e}")

    def record_sync_success(self, sync_time: Optional[datetime] = None) -> None:
        """
        Record successful sync.

        Args:
            sync_time: Sync timestamp (default: now)
        """
        self.status.last_sync_at = sync_time or datetime.now()
        self.status.sync_lag_seconds = 0
        self.status.consecutive_failures = 0
        self.status.sync_health = SyncHealth.HEALTHY

        self._save_status()
        self.logger.debug("Recorded successful sync")

    def record_sync_failure(self, error_message: str) -> None:
        """
        Record sync failure.

        Args:
            error_message: Error description
        """
        self.status.consecutive_failures += 1

        # Update sync lag
        if self.status.last_sync_at:
            lag = (datetime.now() - self.status.last_sync_at).total_seconds()
            self.status.sync_lag_seconds = int(lag)

        # Update health status based on lag (FR-017)
        if self.status.sync_lag_seconds > 3600:  # >1 hour
            self.status.sync_health = SyncHealth.FAILED
            self.logger.error(f"Sync FAILED: lag {self.status.sync_lag_seconds}s")
        elif self.status.sync_lag_seconds > 300:  # >5 minutes
            self.status.sync_health = SyncHealth.DEGRADED
            self.logger.warning(f"Sync DEGRADED: lag {self.status.sync_lag_seconds}s")

        self._save_status()
        self.logger.warning(f"Recorded sync failure: {error_message}")

    def record_conflict(self) -> None:
        """Record merge conflict occurrence."""
        self.status.conflict_count += 1
        self.status.last_conflict_at = datetime.now()
        self._save_status()
        self.logger.info("Recorded conflict")

    def update_sync_lag(self) -> int:
        """
        Update and return current sync lag.

        Returns:
            Sync lag in seconds
        """
        if self.status.last_sync_at:
            lag = (datetime.now() - self.status.last_sync_at).total_seconds()
            self.status.sync_lag_seconds = int(lag)
            self._save_status()
            return self.status.sync_lag_seconds
        return 0

    def should_alert(self) -> bool:
        """
        Check if alert should be triggered.

        Returns:
            True if sync lag exceeds 5 minutes (FR-017)
        """
        return self.status.sync_lag_seconds > 300

    def should_halt_coordination(self) -> bool:
        """
        Check if cross-agent coordination should halt.

        Returns:
            True if sync lag exceeds 1 hour (FR-017)
        """
        return self.status.sync_lag_seconds > 3600

    def get_health_status(self) -> str:
        """
        Get current sync health status.

        Returns:
            Health status string (healthy, degraded, failed)
        """
        return self.status.sync_health

    def get_status_summary(self) -> Dict:
        """
        Get sync status summary for monitoring.

        Returns:
            Dict with status information
        """
        return {
            "agent_id": self.status.agent_id,
            "sync_health": self.status.sync_health,
            "sync_lag_seconds": self.status.sync_lag_seconds,
            "last_sync_at": self.status.last_sync_at.isoformat() if self.status.last_sync_at else None,
            "consecutive_failures": self.status.consecutive_failures,
            "conflict_count": self.status.conflict_count,
            "should_alert": self.should_alert(),
            "should_halt": self.should_halt_coordination()
        }

    def queue_operation(self) -> None:
        """Queue an operation during sync failure."""
        self.status.queued_operations += 1
        self._save_status()

    def clear_queue(self) -> int:
        """
        Clear queued operations after sync recovery.

        Returns:
            Number of operations that were queued
        """
        count = self.status.queued_operations
        self.status.queued_operations = 0
        self._save_status()
        return count
