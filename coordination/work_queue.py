"""
Work Queue Management for Platinum Tier

Provides base coordination utilities for dual-agent task management.
Implements work queue item entity and status transitions.

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
            content_path=Path(data["content_path"]) if data.get("content_path") else None,
            metadata=data.get("metadata", {})
        )


class WorkQueuePathHelper:
    """
    Helper for constructing vault coordination directory paths.

    Based on plan.md vault structure:
    - /Needs_Action/<domain>/
    - /In_Progress/<agent>/
    - /Pending_Approval/<domain>/
    - /Done/
    - /Updates/
    """

    def __init__(self, vault_path: Path):
        """
        Initialize path helper.

        Args:
            vault_path: Root path to Obsidian vault
        """
        self.vault_path = Path(vault_path)

    def needs_action_dir(self, domain: WorkQueueDomain) -> Path:
        """Get Needs_Action directory for domain."""
        return self.vault_path / "Needs_Action" / domain.value

    def in_progress_dir(self, agent_id: str) -> Path:
        """Get In_Progress directory for agent."""
        return self.vault_path / "In_Progress" / agent_id

    def pending_approval_dir(self, domain: WorkQueueDomain) -> Path:
        """Get Pending_Approval directory for domain."""
        return self.vault_path / "Pending_Approval" / domain.value

    def done_dir(self) -> Path:
        """Get Done directory."""
        return self.vault_path / "Done"

    def updates_dir(self) -> Path:
        """Get Updates directory (cloud agent status updates)."""
        return self.vault_path / "Updates"

    def item_filename(self, item: WorkQueueItem) -> str:
        """
        Generate filename for work queue item.

        Format: {item_id}_{domain}_{type}.md
        """
        return f"{item.item_id}_{item.domain.value}_{item.item_type.value}.md"
