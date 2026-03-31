"""Vault writer for creating Obsidian notes from watcher events.

Handles creation of Markdown notes with YAML frontmatter in the Obsidian vault.
"""

import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional


class VaultWriter:
    """Writer for creating Obsidian vault notes."""

    def __init__(self, vault_path: str = "obsidian-vault"):
        """Initialize vault writer.

        Args:
            vault_path: Path to Obsidian vault directory
        """
        self.vault_path = Path(vault_path)
        self._ensure_folders()

    def _ensure_folders(self):
        """Ensure all required vault folders exist."""
        folders = [
            "Inbox",
            "Needs_Action",
            "Done",
            "Approvals",
            "Rejected",
            "Expired",
            "Content_Queue",
            "Schedules",
            "Reports"
        ]

        for folder in folders:
            (self.vault_path / folder).mkdir(parents=True, exist_ok=True)

    def create_note(self, folder: str, title: str, content: str,
                   frontmatter: Optional[Dict[str, Any]] = None) -> str:
        """Create a note in the vault.

        Args:
            folder: Folder name (Inbox, Needs_Action, etc.)
            title: Note title (used for filename)
            content: Note body content
            frontmatter: Optional YAML frontmatter dict

        Returns:
            Path to created note (relative to vault)
        """
        # Sanitize title for filename
        safe_title = self._sanitize_filename(title)
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        filename = f"{timestamp}-{safe_title}.md"

        folder_path = self.vault_path / folder
        note_path = folder_path / filename

        # Build note content
        note_lines = []

        # Add frontmatter if provided
        if frontmatter:
            note_lines.append("---")
            note_lines.append(yaml.dump(frontmatter, default_flow_style=False, sort_keys=False))
            note_lines.append("---")
            note_lines.append("")

        # Add content
        note_lines.append(content)

        # Write note
        note_path.write_text("\n".join(note_lines), encoding="utf-8")

        # Return relative path
        return f"{folder}/{filename}"

    def create_event_note(self, source_channel: str, event_type: str,
                         event_data: Dict[str, Any]) -> str:
        """Create a note from a watcher event.

        Args:
            source_channel: Source channel (gmail, whatsapp, linkedin)
            event_type: Event type (email, message, notification)
            event_data: Event data dict

        Returns:
            Path to created note
        """
        # Build frontmatter
        frontmatter = {
            "source": source_channel,
            "type": event_type,
            "timestamp": event_data.get("timestamp", datetime.utcnow().isoformat() + "Z"),
            "status": "unread"
        }

        # Build title and content based on channel
        if source_channel == "gmail":
            title = event_data.get("subject", "Untitled Email")
            content = self._format_gmail_content(event_data)
            frontmatter["sender"] = event_data.get("sender")
            frontmatter["message_id"] = event_data.get("message_id")

        elif source_channel == "whatsapp":
            sender_name = event_data.get("sender_name", "Unknown")
            title = f"WhatsApp from {sender_name}"
            content = self._format_whatsapp_content(event_data)
            frontmatter["sender_name"] = sender_name
            frontmatter["sender_phone"] = event_data.get("sender_phone")
            frontmatter["message_id"] = event_data.get("message_id")

        elif source_channel == "linkedin":
            sender_name = event_data.get("sender_name", "Unknown")
            notification_type = event_data.get("notification_type", "notification")
            title = f"LinkedIn {notification_type} from {sender_name}"
            content = self._format_linkedin_content(event_data)
            frontmatter["sender_profile_url"] = event_data.get("sender_profile_url")
            frontmatter["notification_type"] = notification_type
            frontmatter["notification_id"] = event_data.get("notification_id")

        else:
            title = f"{source_channel} event"
            content = f"**Event Type**: {event_type}\n\n{yaml.dump(event_data)}"

        return self.create_note("Inbox", title, content, frontmatter)

    def create_approval_note(self, action_id: str, action_type: str,
                            parameters: Dict[str, Any], safety_level: int) -> str:
        """Create an approval request note.

        Args:
            action_id: Action identifier
            action_type: Action type (send-email, linkedin-post, etc.)
            parameters: Action parameters
            safety_level: Safety level (0-3)

        Returns:
            Path to created note
        """
        title = f"Approval: {action_type}"

        frontmatter = {
            "action_id": action_id,
            "action_type": action_type,
            "safety_level": safety_level,
            "status": "pending",
            "created": datetime.utcnow().isoformat() + "Z"
        }

        content_lines = [
            f"# Approval Request: {action_type}",
            "",
            f"**Action ID**: `{action_id}`",
            f"**Safety Level**: {safety_level}",
            f"**Status**: Pending",
            "",
            "## Parameters",
            "",
            "```yaml",
            yaml.dump(parameters, default_flow_style=False),
            "```",
            "",
            "## Actions",
            "",
            "To approve: `claude-code 'Approve action {action_id}'`",
            f"To reject: `claude-code 'Reject action {action_id} with reason: <reason>'`"
        ]

        content = "\n".join(content_lines)
        return self.create_note("Approvals", title, content, frontmatter)

    def move_note(self, current_path: str, target_folder: str) -> str:
        """Move a note to a different folder.

        Args:
            current_path: Current note path (relative to vault)
            target_folder: Target folder name

        Returns:
            New note path
        """
        current_full_path = self.vault_path / current_path
        filename = Path(current_path).name
        new_path = self.vault_path / target_folder / filename

        current_full_path.rename(new_path)

        return f"{target_folder}/{filename}"

    def _sanitize_filename(self, title: str) -> str:
        """Sanitize title for use as filename.

        Args:
            title: Note title

        Returns:
            Sanitized filename
        """
        # Remove invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            title = title.replace(char, "")

        # Limit length
        if len(title) > 100:
            title = title[:100]

        # Replace spaces with hyphens
        title = title.replace(" ", "-")

        return title.lower()

    def _format_gmail_content(self, event_data: Dict[str, Any]) -> str:
        """Format Gmail event as note content."""
        lines = [
            f"# {event_data.get('subject', 'Untitled')}",
            "",
            f"**From**: {event_data.get('sender')}",
            f"**Date**: {event_data.get('timestamp')}",
            "",
            "---",
            "",
            event_data.get("body", "")
        ]
        return "\n".join(lines)

    def _format_whatsapp_content(self, event_data: Dict[str, Any]) -> str:
        """Format WhatsApp event as note content."""
        lines = [
            f"# WhatsApp Message",
            "",
            f"**From**: {event_data.get('sender_name')} ({event_data.get('sender_phone')})",
            f"**Date**: {event_data.get('timestamp')}",
            ""
        ]

        if event_data.get("is_group"):
            lines.append(f"**Group**: {event_data.get('group_name')}")
            lines.append("")

        lines.extend([
            "---",
            "",
            event_data.get("message_text", "")
        ])

        return "\n".join(lines)

    def _format_linkedin_content(self, event_data: Dict[str, Any]) -> str:
        """Format LinkedIn event as note content."""
        notification_type = event_data.get("notification_type", "notification")
        lines = [
            f"# LinkedIn {notification_type.replace('_', ' ').title()}",
            "",
            f"**From**: [{event_data.get('sender_name')}]({event_data.get('sender_profile_url')})",
            f"**Date**: {event_data.get('timestamp')}",
            f"**Type**: {notification_type}",
            ""
        ]

        if event_data.get("post_url"):
            lines.append(f"**Post**: {event_data.get('post_url')}")
            lines.append("")

        lines.extend([
            "---",
            "",
            event_data.get("content", "")
        ])

        return "\n".join(lines)
