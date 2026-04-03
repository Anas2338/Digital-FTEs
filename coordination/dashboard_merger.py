"""
Dashboard Merger for Local Agent

Merges cloud agent updates from /Updates/ into Dashboard.md.
Enforces single-writer rule: only local agent writes to Dashboard.md.

Based on spec.md FR-012, FR-013 and User Story 2.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict

from sync.atomic_writer import AtomicWriter


class DashboardMerger:
    """
    Merges cloud agent updates into Dashboard.md.

    Single-writer rule (FR-013):
    - Cloud agent writes to /Updates/ directory
    - Local agent reads /Updates/ and merges into Dashboard.md
    - Only local agent ever writes to Dashboard.md
    """

    def __init__(self, vault_path: Path):
        """
        Initialize dashboard merger.

        Args:
            vault_path: Path to Obsidian vault
        """
        self.vault_path = Path(vault_path)
        self.logger = logging.getLogger("dashboard_merger")
        self.dashboard_path = self.vault_path / "Dashboard.md"
        self.updates_dir = self.vault_path / "Updates"

    def merge_updates(self) -> int:
        """
        Merge all pending updates from /Updates/ into Dashboard.md.

        Returns:
            Number of updates merged
        """
        if not self.updates_dir.exists():
            self.logger.warning(f"Updates directory not found: {self.updates_dir}")
            return 0

        # Find all update files
        update_files = sorted(self.updates_dir.glob("*.md"))
        if not update_files:
            self.logger.debug("No updates to merge")
            return 0

        self.logger.info(f"Found {len(update_files)} updates to merge")

        # Load current dashboard
        dashboard_content = self._load_dashboard()

        # Process each update file
        merged_count = 0
        for update_file in update_files:
            try:
                if self._merge_single_update(update_file, dashboard_content):
                    merged_count += 1
                    # Archive processed update
                    self._archive_update(update_file)
            except Exception as e:
                self.logger.error(f"Error merging update {update_file}: {e}")

        # Write updated dashboard atomically
        if merged_count > 0:
            AtomicWriter.write(self.dashboard_path, dashboard_content)
            self.logger.info(f"Merged {merged_count} updates into Dashboard.md")

        return merged_count

    def _load_dashboard(self) -> str:
        """
        Load current Dashboard.md content.

        Returns:
            Dashboard content as string
        """
        if self.dashboard_path.exists():
            return self.dashboard_path.read_text(encoding='utf-8')
        else:
            # Create initial dashboard structure
            return """# Digital FTE Dashboard

**Last Updated**: {timestamp}

## Status

Cloud Agent: Running
Local Agent: Running

## Recent Activity

(No activity yet)

## Pending Approvals

(No pending approvals)

## Completed Tasks

(No completed tasks yet)
""".format(timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    def _merge_single_update(self, update_file: Path, dashboard_content: str) -> bool:
        """
        Merge a single update file into dashboard content.

        Args:
            update_file: Path to update file
            dashboard_content: Current dashboard content (modified in place)

        Returns:
            True if merged successfully
        """
        try:
            update_content = update_file.read_text(encoding='utf-8')

            # Parse update metadata from frontmatter
            update_data = self._parse_update_file(update_content)
            if not update_data:
                return False

            update_type = update_data.get('type')
            update_message = update_data.get('message', '')

            # Merge based on update type
            if update_type == 'status':
                self._merge_status_update(dashboard_content, update_message)
            elif update_type == 'activity':
                self._merge_activity_update(dashboard_content, update_message)
            elif update_type == 'alert':
                self._merge_alert_update(dashboard_content, update_message)
            else:
                self.logger.warning(f"Unknown update type: {update_type}")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error processing update file {update_file}: {e}")
            return False

    def _parse_update_file(self, content: str) -> Dict:
        """
        Parse update file frontmatter.

        Args:
            content: Update file content

        Returns:
            Dict with update metadata
        """
        if not content.startswith('---'):
            return {}

        parts = content.split('---', 2)
        if len(parts) < 3:
            return {}

        # Parse frontmatter
        metadata = {}
        for line in parts[1].strip().split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                metadata[key.strip()] = value.strip()

        # Get message body
        metadata['message'] = parts[2].strip()

        return metadata

    def _merge_status_update(self, dashboard_content: str, message: str) -> str:
        """
        Merge status update into dashboard.

        Args:
            dashboard_content: Current dashboard content
            message: Status update message

        Returns:
            Updated dashboard content
        """
        # Update Status section
        if "## Status" in dashboard_content:
            # Replace Status section content
            parts = dashboard_content.split("## Status")
            before = parts[0]
            after_parts = parts[1].split("\n## ", 1)
            after = "\n## " + after_parts[1] if len(after_parts) > 1 else ""

            status_section = f"\n## Status\n\n{message}\n"
            return before + status_section + after

        return dashboard_content

    def _merge_activity_update(self, dashboard_content: str, message: str) -> str:
        """
        Merge activity update into dashboard.

        Args:
            dashboard_content: Current dashboard content
            message: Activity message

        Returns:
            Updated dashboard content
        """
        # Add to Recent Activity section
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        activity_entry = f"- [{timestamp}] {message}\n"

        if "## Recent Activity" in dashboard_content:
            # Insert after Recent Activity header
            parts = dashboard_content.split("## Recent Activity\n", 1)
            if len(parts) == 2:
                # Skip any existing placeholder text
                after = parts[1]
                if "(No activity yet)" in after:
                    after = after.replace("(No activity yet)\n", "")
                return parts[0] + "## Recent Activity\n\n" + activity_entry + after

        return dashboard_content

    def _merge_alert_update(self, dashboard_content: str, message: str) -> str:
        """
        Merge alert update into dashboard.

        Args:
            dashboard_content: Current dashboard content
            message: Alert message

        Returns:
            Updated dashboard content
        """
        # Add alert to top of dashboard
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        alert_box = f"\n> ⚠️ **ALERT** [{timestamp}]: {message}\n\n"

        # Insert after title
        lines = dashboard_content.split('\n', 1)
        if len(lines) == 2:
            return lines[0] + '\n' + alert_box + lines[1]

        return alert_box + dashboard_content

    def _archive_update(self, update_file: Path) -> None:
        """
        Archive processed update file.

        Args:
            update_file: Path to update file
        """
        archive_dir = self.vault_path / "Updates" / "archive"
        archive_dir.mkdir(exist_ok=True)

        archive_path = archive_dir / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{update_file.name}"
        update_file.rename(archive_path)
        self.logger.debug(f"Archived update to {archive_path}")

    def create_update_file(self, update_type: str, message: str, agent_id: str = "cloud") -> Path:
        """
        Create an update file in /Updates/ directory.

        This method is used by cloud agent to write updates.

        Args:
            update_type: Type of update (status, activity, alert)
            message: Update message
            agent_id: Agent creating the update (default "cloud")

        Returns:
            Path to created update file
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{update_type}_{agent_id}.md"
        update_path = self.updates_dir / filename

        content = f"""---
type: {update_type}
agent_id: {agent_id}
created_at: {datetime.now().isoformat()}
---

{message}
"""

        AtomicWriter.write(update_path, content)
        self.logger.info(f"Created update file: {filename}")

        return update_path
