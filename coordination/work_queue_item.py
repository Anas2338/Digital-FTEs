"""
Work Queue Item Entity for Platinum Tier

Extended implementation with full entity methods.
Represents a work item in the coordination queue.

Based on data-model.md Entity 2: Work Queue Item
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

from coordination.logical_clock import LamportTimestamp


class WorkQueueStatus(Enum):
    """Work queue item status states."""
    PENDING = "pending"
    CLAIMED = "claimed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class WorkQueueDomain(Enum):
    """Work domains for agent specialization."""
    EMAIL = "email"
    SOCIAL = "social"
    ACCOUNTING = "accounting"
    BANKING = "banking"
    WHATSAPP = "whatsapp"


class WorkQueueItemType(Enum):
    """Types of work queue items."""
    DRAFT = "draft"
    ACTION_PLAN = "action_plan"
    APPROVAL_REQUEST = "approval_request"


@dataclass
class WorkQueueItem:
    """
    Work queue item for agent coordination.

    Attributes:
        item_id: Unique identifier (UUID)
        domain: Work domain (email, social, accounting, banking, whatsapp)
        item_type: Type of work (draft, action_plan, approval_request)
        status: Current status
        created_at: Logical timestamp when created
        claimed_by: Agent ID that claimed this item (None if unclaimed)
        claimed_at: Logical timestamp when claimed (None if unclaimed)
        completed_at: Logical timestamp when completed (None if not completed)
        content_path: Path to markdown file with item content
        metadata: Additional metadata as dict
    """
    item_id: str
    domain: WorkQueueDomain
    item_type: WorkQueueItemType
    status: WorkQueueStatus
    created_at: LamportTimestamp
    claimed_by: Optional[str] = None
    claimed_at: Optional[LamportTimestamp] = None
    completed_at: Optional[LamportTimestamp] = None
    content_path: Optional[Path] = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Serialize to dictionary for JSON storage."""
        return {
            "item_id": self.item_id,
            "domain": self.domain.value,
            "item_type": self.item_type.value,
            "status": self.status.value,
            "created_at": self.created_at.to_dict(),
            "claimed_by": self.claimed_by,
            "claimed_at": self.claimed_at.to_dict() if self.claimed_at else None,
            "completed_at": self.completed_at.to_dict() if self.completed_at else None,
            "content_path": str(self.content_path) if self.content_path else None,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'WorkQueueItem':
        """Deserialize from dictionary."""
        return cls(
            item_id=data["item_id"],
            domain=WorkQueueDomain(data["domain"]),
            item_type=WorkQueueItemType(data["item_type"]),
            status=WorkQueueStatus(data["status"]),
            created_at=LamportTimestamp.from_dict(data["created_at"]),
            claimed_by=data.get("claimed_by"),
            claimed_at=LamportTimestamp.from_dict(data["claimed_at"]) if data.get("claimed_at") else None,
            completed_at=LamportTimestamp.from_dict(data["completed_at"]) if data.get("completed_at") else None,
            content_path=Path(data["content_path"]) if data.get("content_path") else None,
            metadata=data.get("metadata", {})
        )

    def claim(self, agent_id: str, timestamp: LamportTimestamp) -> None:
        """
        Claim this work item.

        Args:
            agent_id: ID of agent claiming the item
            timestamp: Logical timestamp of claim

        Raises:
            ValueError: If item is already claimed
        """
        if self.status != WorkQueueStatus.PENDING:
            raise ValueError(f"Cannot claim item with status {self.status.value}")

        self.status = WorkQueueStatus.CLAIMED
        self.claimed_by = agent_id
        self.claimed_at = timestamp

    def start_work(self) -> None:
        """
        Mark item as in progress.

        Raises:
            ValueError: If item is not claimed
        """
        if self.status != WorkQueueStatus.CLAIMED:
            raise ValueError(f"Cannot start work on item with status {self.status.value}")

        self.status = WorkQueueStatus.IN_PROGRESS

    def complete(self, timestamp: LamportTimestamp) -> None:
        """
        Mark item as completed.

        Args:
            timestamp: Logical timestamp of completion

        Raises:
            ValueError: If item is not in progress
        """
        if self.status != WorkQueueStatus.IN_PROGRESS:
            raise ValueError(f"Cannot complete item with status {self.status.value}")

        self.status = WorkQueueStatus.COMPLETED
        self.completed_at = timestamp

    def fail(self, error_message: str) -> None:
        """
        Mark item as failed.

        Args:
            error_message: Description of failure
        """
        self.status = WorkQueueStatus.FAILED
        self.metadata["error"] = error_message
        self.metadata["failed_at"] = datetime.now().isoformat()

    def is_pending(self) -> bool:
        """Check if item is pending (unclaimed)."""
        return self.status == WorkQueueStatus.PENDING

    def is_claimed_by(self, agent_id: str) -> bool:
        """Check if item is claimed by specific agent."""
        return self.claimed_by == agent_id
