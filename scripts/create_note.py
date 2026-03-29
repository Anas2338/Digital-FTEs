"""
Note Creation Script

Creates new notes in the Obsidian vault with proper frontmatter and structure.
Automatically updates dashboard after note creation.
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, List
import argparse

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from watchers.vault_utils import generate_frontmatter
from watchers.utils import sanitize_filename, format_timestamp_filename, format_iso8601


def generate_note_filename(title: str) -> str:
    """
    Generate filename for note using timestamp and sanitized title.

    Args:
        title: Note title

    Returns:
        Filename in format YYYYMMDD-HHMMSS-sanitized-title.md
    """
    timestamp = format_timestamp_filename()
    sanitized_title = sanitize_filename(title, max_length=50)
    return f"{timestamp}-{sanitized_title}.md"


def create_note(
    vault_path: Path,
    folder: str,
    title: str,
    content: str,
    source: str = "manual",
    sender: Optional[str] = None,
    email_date: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> Optional[Path]:
    """
    Create a new note in the vault with proper frontmatter.

    Args:
        vault_path: Path to vault root
        folder: Target folder (Inbox, Needs_Action, Done)
        title: Note title
        content: Note body content
        source: Source of note (default: "manual")
        sender: Email sender (optional)
        email_date: Original email date (optional)
        tags: List of tags (optional)

    Returns:
        Path to created note, or None if creation failed
    """
    try:
        # Validate folder
        valid_folders = ['Inbox', 'Needs_Action', 'Done']
        if folder not in valid_folders:
            print(f"[ERROR] Invalid folder: {folder}. Must be one of {valid_folders}")
            return None

        # Ensure folder exists
        folder_path = vault_path / folder
        folder_path.mkdir(parents=True, exist_ok=True)

        # Generate filename
        filename = generate_note_filename(title)
        note_path = folder_path / filename

        # Check if file already exists (unlikely with timestamp, but check anyway)
        if note_path.exists():
            print(f"[WARN] Note already exists: {note_path}")
            return note_path

        # Determine status based on folder
        status_map = {
            'Inbox': 'inbox',
            'Needs_Action': 'needs-action',
            'Done': 'done'
        }
        status = status_map[folder]

        # Generate frontmatter
        created = format_iso8601()
        frontmatter = generate_frontmatter(
            title=title,
            created=created,
            source=source,
            sender=sender,
            email_date=email_date,
            status=status,
            tags=tags
        )

        # Format note body
        note_content = f"{frontmatter}\n{content}\n"

        # Write note
        with open(note_path, 'w', encoding='utf-8') as f:
            f.write(note_content)

        print(f"[OK] Created note: {note_path}")
        return note_path

    except Exception as e:
        print(f"[ERROR] Failed to create note: {e}")
        return None


def update_dashboard_after_creation(vault_path: Path) -> bool:
    """
    Update dashboard after note creation.

    Args:
        vault_path: Path to vault root

    Returns:
        True if update successful, False otherwise
    """
    try:
        # Import here to avoid circular dependency
        from scripts.update_dashboard import update_dashboard
        return update_dashboard(vault_path)
    except Exception as e:
        print(f"[WARN] Could not update dashboard: {e}")
        return False


def main():
    """Main entry point for note creation script."""
    parser = argparse.ArgumentParser(
        description='Create a new note in the Obsidian vault'
    )
    parser.add_argument(
        '--vault-path',
        type=str,
        default='obsidian-vault',
        help='Path to vault directory (default: obsidian-vault)'
    )
    parser.add_argument(
        '--folder',
        type=str,
        required=True,
        choices=['Inbox', 'Needs_Action', 'Done'],
        help='Target folder for the note'
    )
    parser.add_argument(
        '--title',
        type=str,
        required=True,
        help='Note title'
    )
    parser.add_argument(
        '--content',
        type=str,
        default='',
        help='Note body content'
    )
    parser.add_argument(
        '--source',
        type=str,
        default='manual',
        help='Source of the note (default: manual)'
    )
    parser.add_argument(
        '--sender',
        type=str,
        help='Email sender (optional)'
    )
    parser.add_argument(
        '--email-date',
        type=str,
        help='Original email date in ISO 8601 format (optional)'
    )
    parser.add_argument(
        '--tags',
        type=str,
        help='Comma-separated list of tags (optional)'
    )
    parser.add_argument(
        '--no-dashboard-update',
        action='store_true',
        help='Skip automatic dashboard update'
    )

    args = parser.parse_args()

    # Convert to absolute path
    vault_path = Path(args.vault_path).resolve()

    if not vault_path.exists():
        print(f"[ERROR] Vault directory does not exist: {vault_path}")
        sys.exit(1)

    # Parse tags
    tags = None
    if args.tags:
        tags = [tag.strip() for tag in args.tags.split(',')]

    # Create note
    note_path = create_note(
        vault_path=vault_path,
        folder=args.folder,
        title=args.title,
        content=args.content,
        source=args.source,
        sender=args.sender,
        email_date=args.email_date,
        tags=tags
    )

    if not note_path:
        sys.exit(1)

    # Update dashboard unless disabled
    if not args.no_dashboard_update:
        update_dashboard_after_creation(vault_path)

    sys.exit(0)


if __name__ == '__main__':
    main()
