"""Approval queue manager for Digital FTE.

Manages the approval queue by creating approval request notes in the Obsidian vault
and tracking pending actions.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from watchers.shared.vault_writer import VaultWriter
from watchers.shared.database import Database


class ApprovalQueueManager:
    """Manager for approval queue operations."""

    def __init__(self, vault_path: str = "obsidian-vault"):
        """Initialize approval queue manager.

        Args:
            vault_path: Path to Obsidian vault
        """
        self.vault_writer = VaultWriter(vault_path)
        self.db = Database()
        self.expiration_hours = 24

    def queue_for_approval(self, action_id: str, action_type: str,
                          parameters: Dict[str, Any], safety_level: int) -> str:
        """Queue an action for approval.

        Args:
            action_id: Unique action identifier
            action_type: Type of action (send-email, linkedin-post, etc.)
            parameters: Action parameters
            safety_level: Safety level (0-3)

        Returns:
            Path to created approval note
        """
        # Create approval note in vault
        vault_path = self.vault_writer.create_approval_note(
            action_id=action_id,
            action_type=action_type,
            parameters=parameters,
            safety_level=safety_level
        )

        # Log to database
        self.db.log_action(
            action_id=action_id,
            action_type=action_type,
            parameters=parameters,
            safety_level=safety_level,
            status="pending"
        )

        return vault_path

    def list_pending(self) -> List[Dict[str, Any]]:
        """List all pending approval requests.

        Returns:
            List of pending actions
        """
        return self.db.get_pending_actions()

    def approve(self, action_id: str, approver: str = "user") -> bool:
        """Approve an action.

        Args:
            action_id: Action identifier
            approver: Username who approved

        Returns:
            True if approved successfully
        """
        try:
            # Update database status
            self.db.update_action_status(
                action_id=action_id,
                status="approved",
                approver=approver
            )

            # Note will be moved to /Done after execution by executor
            return True

        except Exception as e:
            print(f"Error approving action {action_id}: {e}")
            return False

    def reject(self, action_id: str, reason: str, approver: str = "user") -> bool:
        """Reject an action.

        Args:
            action_id: Action identifier
            reason: Rejection reason
            approver: Username who rejected

        Returns:
            True if rejected successfully
        """
        try:
            # Update database status
            self.db.update_action_status(
                action_id=action_id,
                status="rejected",
                approver=approver,
                rejection_reason=reason
            )

            # Move note from /Approvals to /Rejected
            # Find the approval note
            approvals_dir = Path(self.vault_writer.vault_path) / "Approvals"
            for note_file in approvals_dir.glob("*.md"):
                # Check if this note contains the action_id
                content = note_file.read_text(encoding="utf-8")
                if action_id in content:
                    # Move to /Rejected
                    rejected_path = Path(self.vault_writer.vault_path) / "Rejected" / note_file.name
                    note_file.rename(rejected_path)

                    # Append rejection reason to note
                    with open(rejected_path, "a", encoding="utf-8") as f:
                        f.write(f"\n\n## Rejection\n\n")
                        f.write(f"**Rejected by**: {approver}\n")
                        f.write(f"**Reason**: {reason}\n")
                        f.write(f"**Timestamp**: {datetime.utcnow().isoformat()}Z\n")
                    break

            return True

        except Exception as e:
            print(f"Error rejecting action {action_id}: {e}")
            return False

    def expire_old_approvals(self) -> int:
        """Expire pending approvals older than 24 hours.

        Returns:
            Number of actions expired
        """
        expired_count = 0
        pending_actions = self.list_pending()

        for action in pending_actions:
            created_time = datetime.fromisoformat(action["created_timestamp"].replace("Z", ""))
            age_hours = (datetime.utcnow() - created_time).total_seconds() / 3600

            if age_hours >= self.expiration_hours:
                try:
                    # Update database status
                    self.db.update_action_status(
                        action_id=action["action_id"],
                        status="expired"
                    )

                    # Move note from /Approvals to /Expired
                    approvals_dir = Path(self.vault_writer.vault_path) / "Approvals"
                    for note_file in approvals_dir.glob("*.md"):
                        content = note_file.read_text(encoding="utf-8")
                        if action["action_id"] in content:
                            expired_path = Path(self.vault_writer.vault_path) / "Expired" / note_file.name
                            note_file.rename(expired_path)

                            # Append expiration notice
                            with open(expired_path, "a", encoding="utf-8") as f:
                                f.write(f"\n\n## Expiration\n\n")
                                f.write(f"**Status**: Auto-expired after {self.expiration_hours} hours\n")
                                f.write(f"**Timestamp**: {datetime.utcnow().isoformat()}Z\n")
                            break

                    expired_count += 1

                except Exception as e:
                    print(f"Error expiring action {action['action_id']}: {e}")

        return expired_count

    def get_action_details(self, action_id: str) -> Optional[Dict[str, Any]]:
        """Get details of a specific action.

        Args:
            action_id: Action identifier

        Returns:
            Action details or None if not found
        """
        pending_actions = self.list_pending()
        for action in pending_actions:
            if action["action_id"] == action_id:
                return action
        return None
