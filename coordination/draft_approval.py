"""
Draft Approval Entity for Platinum Tier

Represents a draft awaiting user approval (email reply, social post, accounting entry).
Created by cloud agent, approved by local agent.

Based on data-model.md Entity 3: Draft Approval
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional

from coordination.logical_clock import LamportTimestamp


class DraftType(Enum):
    """Types of drafts that can be created."""
    EMAIL_REPLY = "email_reply"
    SOCIAL_POST = "social_post"
    ACCOUNTING_ENTRY = "accounting_entry"


class ApprovalStatus(Enum):
    """Approval status states."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass
class DraftApproval:
    """
    Draft approval entity for work-zone specialization.

    Attributes:
        approval_id: Unique identifier (UUID)
        draft_type: Type of draft (email_reply, social_post, accounting_entry)
        draft_content_path: Path to markdown file with draft content
        created_by: Agent ID that created the draft (always "cloud")
        created_at: Logical timestamp when draft was created
        approval_status: Current approval status
        approved_by: User ID who approved (None if not approved)
        approved_at: Logical timestamp when approved (None if not approved)
        executed_at: Logical timestamp when action was executed (None if not executed)
        metadata: Additional metadata as dict
    """
    approval_id: str
    draft_type: DraftType
    draft_content_path: Path
    created_by: str
    created_at: LamportTimestamp
    approval_status: ApprovalStatus
    approved_by: Optional[str] = None
    approved_at: Optional[LamportTimestamp] = None
    executed_at: Optional[LamportTimestamp] = None
    metadata: dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> dict:
        """Serialize to dictionary for JSON storage."""
        return {
            "approval_id": self.approval_id,
            "draft_type": self.draft_type.value,
            "draft_content_path": str(self.draft_content_path),
            "created_by": self.created_by,
            "created_at": self.created_at.to_dict(),
            "approval_status": self.approval_status.value,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at.to_dict() if self.approved_at else None,
            "executed_at": self.executed_at.to_dict() if self.executed_at else None,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'DraftApproval':
        """Deserialize from dictionary."""
        return cls(
            approval_id=data["approval_id"],
            draft_type=DraftType(data["draft_type"]),
            draft_content_path=Path(data["draft_content_path"]),
            created_by=data["created_by"],
            created_at=LamportTimestamp.from_dict(data["created_at"]),
            approval_status=ApprovalStatus(data["approval_status"]),
            approved_by=data.get("approved_by"),
            approved_at=LamportTimestamp.from_dict(data["approved_at"]) if data.get("approved_at") else None,
            executed_at=LamportTimestamp.from_dict(data["executed_at"]) if data.get("executed_at") else None,
            metadata=data.get("metadata", {})
        )

    def approve(self, user_id: str, timestamp: LamportTimestamp) -> None:
        """
        Mark draft as approved.

        Args:
            user_id: ID of user who approved
            timestamp: Logical timestamp of approval
        """
        self.approval_status = ApprovalStatus.APPROVED
        self.approved_by = user_id
        self.approved_at = timestamp

    def reject(self, user_id: str, timestamp: LamportTimestamp) -> None:
        """
        Mark draft as rejected.

        Args:
            user_id: ID of user who rejected
            timestamp: Logical timestamp of rejection
        """
        self.approval_status = ApprovalStatus.REJECTED
        self.approved_by = user_id
        self.approved_at = timestamp

    def mark_executed(self, timestamp: LamportTimestamp) -> None:
        """
        Mark draft as executed (action completed).

        Args:
            timestamp: Logical timestamp of execution
        """
        if self.approval_status != ApprovalStatus.APPROVED:
            raise ValueError("Cannot execute draft that is not approved")
        self.executed_at = timestamp

    def is_pending(self) -> bool:
        """Check if draft is pending approval."""
        return self.approval_status == ApprovalStatus.PENDING

    def is_approved(self) -> bool:
        """Check if draft is approved."""
        return self.approval_status == ApprovalStatus.APPROVED

    def is_executed(self) -> bool:
        """Check if draft has been executed."""
        return self.executed_at is not None
