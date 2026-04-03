"""
Sync Status Entity for Platinum Tier

Persistent sync status tracking for monitoring and alerting.
Stored in .sync-status/{agent_id}.json

Based on data-model.md Entity 4: Sync Status
"""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from sync.atomic_writer import AtomicWriter


@dataclass
class SyncStatusEntity:
    """
    Sync status entity for vault synchronization monitoring.

    Attributes:
        agent_id: Agent identifier (cloud or local)
        last_sync_at: Timestamp of last successful sync
        sync_lag_seconds: Time since last sync
        sync_method: Synchronization method (git)
        conflict_count: Total conflicts encountered
        last_conflict_at: Timestamp of last conflict
        sync_health: Current health status (healthy, degraded, failed)
        consecutive_failures: Number of consecutive sync failures
        queued_operations: Operations queued during sync failure
    """
    agent_id: str
    last_sync_at: datetime
    sync_lag_seconds: int
    sync_method: str
    conflict_count: int
    last_conflict_at: Optional[datetime]
    sync_health: str
    consecutive_failures: int
    queued_operations: int

    def to_dict(self) -> dict:
        """Serialize to dictionary for JSON storage."""
        return {
            "agent_id": self.agent_id,
            "last_sync_at": self.last_sync_at.isoformat(),
            "sync_lag_seconds": self.sync_lag_seconds,
            "sync_method": self.sync_method,
            "conflict_count": self.conflict_count,
            "last_conflict_at": self.last_conflict_at.isoformat() if self.last_conflict_at else None,
            "sync_health": self.sync_health,
            "consecutive_failures": self.consecutive_failures,
            "queued_operations": self.queued_operations
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'SyncStatusEntity':
        """Deserialize from dictionary."""
        return cls(
            agent_id=data["agent_id"],
            last_sync_at=datetime.fromisoformat(data["last_sync_at"]),
            sync_lag_seconds=data["sync_lag_seconds"],
            sync_method=data["sync_method"],
            conflict_count=data["conflict_count"],
            last_conflict_at=datetime.fromisoformat(data["last_conflict_at"]) if data.get("last_conflict_at") else None,
            sync_health=data["sync_health"],
            consecutive_failures=data["consecutive_failures"],
            queued_operations=data["queued_operations"]
        )

    @classmethod
    def load(cls, vault_path: Path, agent_id: str) -> 'SyncStatusEntity':
        """
        Load sync status from file.

        Args:
            vault_path: Path to Obsidian vault
            agent_id: Agent identifier

        Returns:
            SyncStatusEntity instance
        """
        status_file = vault_path / ".sync-status" / f"{agent_id}.json"

        if status_file.exists():
            with open(status_file, 'r') as f:
                data = json.load(f)
            return cls.from_dict(data)

        # Return default status
        return cls(
            agent_id=agent_id,
            last_sync_at=datetime.now(),
            sync_lag_seconds=0,
            sync_method="git",
            conflict_count=0,
            last_conflict_at=None,
            sync_health="healthy",
            consecutive_failures=0,
            queued_operations=0
        )

    def save(self, vault_path: Path) -> None:
        """
        Save sync status to file.

        Args:
            vault_path: Path to Obsidian vault
        """
        status_file = vault_path / ".sync-status" / f"{self.agent_id}.json"
        status_file.parent.mkdir(exist_ok=True)

        AtomicWriter.write(
            status_file,
            json.dumps(self.to_dict(), indent=2)
        )
