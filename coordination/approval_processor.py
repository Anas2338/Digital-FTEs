"""
Approval Processor for Local Agent

Monitors /Pending_Approval/ directories and processes user approvals.
Tracks approval rates for SC-011 (≥80% approval rate metric).

Based on spec.md FR-010, FR-029, SC-011 and User Story 2.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from coordination.draft_approval import DraftApproval, ApprovalStatus, DraftType
from coordination.logical_clock import LamportClock, LamportTimestamp
from sync.atomic_writer import AtomicWriter


class ApprovalProcessor:
    """
    Processes draft approvals for local agent.

    Responsibilities:
    - Monitor /Pending_Approval/{domain}/ directories
    - Present drafts to user via Dashboard.md
    - Process approval decisions
    - Track approval rate for SC-011
    - Execute approved actions via MCP
    """

    def __init__(self, vault_path: Path, agent_id: str = "local"):
        """
        Initialize approval processor.

        Args:
            vault_path: Path to Obsidian vault
            agent_id: Agent ID (default "local")
        """
        self.vault_path = Path(vault_path)
        self.agent_id = agent_id
        self.clock = LamportClock(agent_id=agent_id)
        self.logger = logging.getLogger("approval_processor")

        # Approval rate tracking for SC-011
        self.total_drafts = 0
        self.approved_drafts = 0

    def scan_pending_approvals(self) -> List[DraftApproval]:
        """
        Scan all /Pending_Approval/ directories for pending drafts.

        Returns:
            List of DraftApproval objects with pending status
        """
        pending_approvals = []

        # Scan each domain directory
        for domain in ["email", "social", "accounting"]:
            domain_dir = self.vault_path / "Pending_Approval" / domain
            if not domain_dir.exists():
                continue

            # Find all markdown files
            for draft_file in domain_dir.glob("*.md"):
                try:
                    approval = self._load_draft_approval(draft_file)
                    if approval and approval.is_pending():
                        pending_approvals.append(approval)
                except Exception as e:
                    self.logger.error(f"Error loading draft {draft_file}: {e}")

        self.logger.info(f"Found {len(pending_approvals)} pending approvals")
        return pending_approvals

    def _load_draft_approval(self, draft_file: Path) -> Optional[DraftApproval]:
        """
        Load draft approval from markdown file.

        Args:
            draft_file: Path to draft markdown file

        Returns:
            DraftApproval object or None if invalid
        """
        try:
            content = draft_file.read_text(encoding='utf-8')

            # Parse frontmatter (YAML between --- markers)
            if not content.startswith('---'):
                return None

            parts = content.split('---', 2)
            if len(parts) < 3:
                return None

            # Parse frontmatter as simple key-value pairs
            frontmatter = {}
            for line in parts[1].strip().split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    frontmatter[key.strip()] = value.strip()

            # Extract draft metadata
            approval_id = frontmatter.get('draft_id')
            draft_type_str = frontmatter.get('draft_type')
            created_by = frontmatter.get('created_by')
            approval_status_str = frontmatter.get('approval_status', 'pending')

            if not all([approval_id, draft_type_str, created_by]):
                return None

            # Create DraftApproval object
            # Note: Simplified - would parse full timestamp in production
            created_at = LamportTimestamp(
                agent_id=created_by,
                counter=0,  # Would parse from frontmatter
                wall_clock_time=datetime.now()
            )

            return DraftApproval(
                approval_id=approval_id,
                draft_type=DraftType(draft_type_str),
                draft_content_path=draft_file,
                created_by=created_by,
                created_at=created_at,
                approval_status=ApprovalStatus(approval_status_str)
            )

        except Exception as e:
            self.logger.error(f"Error parsing draft file {draft_file}: {e}")
            return None

    def update_dashboard_with_approvals(self, pending_approvals: List[DraftApproval]) -> None:
        """
        Update Dashboard.md with pending approvals section.

        Args:
            pending_approvals: List of pending draft approvals
        """
        dashboard_path = self.vault_path / "Dashboard.md"

        # Read existing dashboard
        if dashboard_path.exists():
            dashboard_content = dashboard_path.read_text(encoding='utf-8')
        else:
            dashboard_content = "# Digital FTE Dashboard\n\n"

        # Remove existing pending approvals section
        if "## Pending Approvals" in dashboard_content:
            parts = dashboard_content.split("## Pending Approvals")
            before = parts[0]
            # Find next section or end
            after_parts = parts[1].split("\n## ", 1)
            after = "\n## " + after_parts[1] if len(after_parts) > 1 else ""
            dashboard_content = before + after

        # Add new pending approvals section
        if pending_approvals:
            approvals_section = self._format_approvals_section(pending_approvals)
            # Insert before first ## section or at end
            if "\n## " in dashboard_content:
                parts = dashboard_content.split("\n## ", 1)
                dashboard_content = parts[0] + approvals_section + "\n## " + parts[1]
            else:
                dashboard_content += approvals_section

        # Write updated dashboard atomically
        AtomicWriter.write(dashboard_path, dashboard_content)
        self.logger.info(f"Updated Dashboard.md with {len(pending_approvals)} pending approvals")

    def _format_approvals_section(self, approvals: List[DraftApproval]) -> str:
        """
        Format pending approvals as markdown section.

        Args:
            approvals: List of pending approvals

        Returns:
            Formatted markdown string
        """
        section = "\n## Pending Approvals\n\n"
        section += f"**Total pending**: {len(approvals)}\n\n"

        # Group by type
        by_type: Dict[DraftType, List[DraftApproval]] = {}
        for approval in approvals:
            if approval.draft_type not in by_type:
                by_type[approval.draft_type] = []
            by_type[approval.draft_type].append(approval)

        # Format each type
        for draft_type, type_approvals in by_type.items():
            section += f"### {draft_type.value.replace('_', ' ').title()}\n\n"
            for approval in type_approvals:
                section += f"- [ ] [{approval.approval_id[:8]}]({approval.draft_content_path.name}) "
                section += f"(created {approval.created_at.wall_clock_time.strftime('%Y-%m-%d %H:%M')})\n"

        section += "\n**To approve**: Check the box and save Dashboard.md\n\n"
        return section

    def process_approvals_from_dashboard(self) -> int:
        """
        Process approval decisions from Dashboard.md checkboxes.

        Returns:
            Number of approvals processed
        """
        dashboard_path = self.vault_path / "Dashboard.md"
        if not dashboard_path.exists():
            return 0

        dashboard_content = dashboard_path.read_text(encoding='utf-8')

        # Find checked boxes in Pending Approvals section
        if "## Pending Approvals" not in dashboard_content:
            return 0

        processed_count = 0
        timestamp = self.clock.tick()

        # Parse checked items (simplified - would use proper markdown parser)
        lines = dashboard_content.split('\n')
        in_approvals_section = False

        for line in lines:
            if "## Pending Approvals" in line:
                in_approvals_section = True
                continue
            if in_approvals_section and line.startswith("## "):
                break
            if in_approvals_section and "- [x]" in line.lower():
                # Extract approval ID from line
                if "[" in line and "]" in line:
                    # Parse approval ID from markdown link
                    start = line.find("[") + 1
                    end = line.find("]", start)
                    approval_id_prefix = line[start:end]

                    # Find and process the approval
                    if self._process_single_approval(approval_id_prefix, timestamp):
                        processed_count += 1
                        self.approved_drafts += 1
                    self.total_drafts += 1

        # Update approval rate metric
        if self.total_drafts > 0:
            approval_rate = (self.approved_drafts / self.total_drafts) * 100
            self.logger.info(f"Approval rate: {approval_rate:.1f}% ({self.approved_drafts}/{self.total_drafts})")

        return processed_count

    def _process_single_approval(self, approval_id_prefix: str, timestamp: LamportTimestamp) -> bool:
        """
        Process a single approval.

        Args:
            approval_id_prefix: First 8 characters of approval ID
            timestamp: Logical timestamp of approval

        Returns:
            True if processed successfully
        """
        # Find draft file matching ID prefix
        for domain in ["email", "social", "accounting"]:
            domain_dir = self.vault_path / "Pending_Approval" / domain
            if not domain_dir.exists():
                continue

            for draft_file in domain_dir.glob(f"{approval_id_prefix}*.md"):
                try:
                    # Update draft status to approved
                    content = draft_file.read_text(encoding='utf-8')
                    content = content.replace(
                        "approval_status: pending",
                        f"approval_status: approved"
                    )
                    content += f"\n\n**Approved at**: {timestamp.wall_clock_time.isoformat()}\n"

                    AtomicWriter.write(draft_file, content)
                    self.logger.info(f"Approved draft {approval_id_prefix}")
                    return True

                except Exception as e:
                    self.logger.error(f"Error processing approval {approval_id_prefix}: {e}")
                    return False

        return False

    def get_approval_rate(self) -> float:
        """
        Get current approval rate for SC-011 metric.

        Returns:
            Approval rate as percentage (0-100)
        """
        if self.total_drafts == 0:
            return 0.0
        return (self.approved_drafts / self.total_drafts) * 100
