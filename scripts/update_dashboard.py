"""
Dashboard Update Script

Regenerates Dashboard.md with current vault statistics:
- Folder counts (Inbox, Needs_Action, Done)
- Recent activity (last 10 notes by created timestamp)
- Last updated timestamp
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import argparse

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from watchers.vault_utils import parse_frontmatter
from watchers.utils import format_iso8601


def count_notes_in_folder(vault_path: Path, folder_name: str) -> int:
    """
    Count markdown files in a vault folder.

    Args:
        vault_path: Path to vault root
        folder_name: Folder name (Inbox, Needs_Action, Done)

    Returns:
        Count of .md files in folder
    """
    folder_path = vault_path / folder_name
    if not folder_path.exists():
        return 0

    return len(list(folder_path.glob('*.md')))


def get_all_notes_with_metadata(vault_path: Path) -> List[Dict[str, Any]]:
    """
    Get all notes from vault with their frontmatter metadata.

    Args:
        vault_path: Path to vault root

    Returns:
        List of dicts with note metadata (path, frontmatter)
    """
    notes = []
    folders = ['Inbox', 'Needs_Action', 'Done']

    for folder in folders:
        folder_path = vault_path / folder
        if not folder_path.exists():
            continue

        for note_path in folder_path.glob('*.md'):
            try:
                with open(note_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                frontmatter, _ = parse_frontmatter(content)

                notes.append({
                    'path': note_path,
                    'filename': note_path.name,
                    'folder': folder,
                    'frontmatter': frontmatter
                })
            except Exception as e:
                print(f"Warning: Could not read {note_path}: {e}")
                continue

    return notes


def get_recent_notes(notes: List[Dict[str, Any]], limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get most recent notes sorted by created timestamp.

    Args:
        notes: List of note metadata dicts
        limit: Maximum number of notes to return

    Returns:
        List of recent notes sorted by created timestamp (newest first)
    """
    # Filter notes with valid created timestamp
    notes_with_timestamp = []
    for note in notes:
        created = note['frontmatter'].get('created')
        if created:
            notes_with_timestamp.append(note)

    # Sort by created timestamp descending (newest first)
    sorted_notes = sorted(
        notes_with_timestamp,
        key=lambda n: n['frontmatter']['created'],
        reverse=True
    )

    return sorted_notes[:limit]


def format_recent_notes_list(recent_notes: List[Dict[str, Any]]) -> str:
    """
    Format recent notes as markdown list with wikilinks.

    Args:
        recent_notes: List of recent note metadata

    Returns:
        Markdown formatted list
    """
    if not recent_notes:
        return "*No recent notes yet.*"

    lines = []
    for note in recent_notes:
        # Extract metadata
        title = note['frontmatter'].get('title', 'Untitled')
        created = note['frontmatter'].get('created', '')
        folder = note['folder']
        filename = note['filename'].replace('.md', '')

        # Format as wikilink with metadata
        # Example: - [[Inbox/20260329-143000-email-subject|Email Subject]] - 2026-03-29 14:30
        created_display = created[:16].replace('T', ' ') if created else 'Unknown'
        lines.append(f"- [[{folder}/{filename}|{title}]] - {created_display}")

    return '\n'.join(lines)


def generate_dashboard_content(
    vault_path: Path,
    inbox_count: int,
    needs_action_count: int,
    done_count: int,
    recent_notes_markdown: str
) -> str:
    """
    Generate complete Dashboard.md content.

    Args:
        vault_path: Path to vault root
        inbox_count: Number of notes in Inbox
        needs_action_count: Number of notes in Needs_Action
        done_count: Number of notes in Done
        recent_notes_markdown: Formatted recent notes list

    Returns:
        Complete dashboard markdown content
    """
    last_updated = format_iso8601()

    dashboard = f"""# Dashboard

## Last Updated
{last_updated}

---

## Folder Status

| Folder | Count | Link |
|--------|-------|------|
| Inbox | {inbox_count} | [[Inbox/]] |
| Needs Action | {needs_action_count} | [[Needs_Action/]] |
| Done | {done_count} | [[Done/]] |

---

## Recent Activity

{recent_notes_markdown}

---

## Quick Links

- [[Company_Handbook]] - Business processes and guidelines
- [[Inbox/]] - New items requiring processing
- [[Needs_Action/]] - Tasks requiring attention
- [[Done/]] - Completed items archive

---

*Dashboard automatically updated by Digital FTE system*
"""

    return dashboard


def update_dashboard(vault_path: Path) -> bool:
    """
    Update Dashboard.md with current vault statistics.

    Args:
        vault_path: Path to vault root

    Returns:
        True if update successful, False otherwise
    """
    try:
        # Count notes in each folder
        inbox_count = count_notes_in_folder(vault_path, 'Inbox')
        needs_action_count = count_notes_in_folder(vault_path, 'Needs_Action')
        done_count = count_notes_in_folder(vault_path, 'Done')

        # Get all notes with metadata
        all_notes = get_all_notes_with_metadata(vault_path)

        # Get recent notes
        recent_notes = get_recent_notes(all_notes, limit=10)

        # Format recent notes
        recent_notes_markdown = format_recent_notes_list(recent_notes)

        # Generate dashboard content
        dashboard_content = generate_dashboard_content(
            vault_path,
            inbox_count,
            needs_action_count,
            done_count,
            recent_notes_markdown
        )

        # Atomic write: write to temp file, then rename
        dashboard_path = vault_path / 'Dashboard.md'
        temp_path = vault_path / '.Dashboard.md.tmp'

        with open(temp_path, 'w', encoding='utf-8') as f:
            f.write(dashboard_content)

        # Atomic rename
        temp_path.replace(dashboard_path)

        print(f"[OK] Dashboard updated successfully")
        print(f"  Inbox: {inbox_count} | Needs Action: {needs_action_count} | Done: {done_count}")
        print(f"  Recent notes: {len(recent_notes)}")

        return True

    except Exception as e:
        print(f"[ERROR] Failed to update dashboard: {e}")
        return False


def main():
    """Main entry point for dashboard update script."""
    parser = argparse.ArgumentParser(
        description='Update Obsidian vault Dashboard.md with current statistics'
    )
    parser.add_argument(
        '--vault-path',
        type=str,
        default='obsidian-vault',
        help='Path to vault directory (default: obsidian-vault)'
    )

    args = parser.parse_args()

    # Convert to absolute path
    vault_path = Path(args.vault_path).resolve()

    if not vault_path.exists():
        print(f"[ERROR] Vault directory does not exist: {vault_path}")
        sys.exit(1)

    # Update dashboard
    success = update_dashboard(vault_path)

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
