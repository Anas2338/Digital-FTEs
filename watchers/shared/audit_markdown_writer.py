"""
Daily Markdown Audit Log Generator for Digital FTE

Generates human-readable Markdown audit logs from the SQLite audit database.
Creates daily files (YYYY-MM-DD.md) in the Obsidian vault for easy review.

Usage:
    writer = AuditMarkdownWriter()
    writer.generate_daily_log("2026-04-01")  # Generate log for specific date
    writer.generate_daily_log()  # Generate log for today
"""

import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging

from watchers.shared.audit_logger import AuditLogger


logger = logging.getLogger(__name__)


class AuditMarkdownWriter:
    """
    Generates daily Markdown audit logs from SQLite database.
    """

    def __init__(self, vault_path: str = "watchers/obsidian-vault/Audit_Logs"):
        """
        Initialize Markdown audit log writer.

        Args:
            vault_path: Path to Obsidian vault Audit_Logs directory
        """
        self.vault_path = Path(vault_path)
        self.vault_path.mkdir(parents=True, exist_ok=True)
        self.audit_logger = AuditLogger()

    def generate_daily_log(self, date: Optional[str] = None) -> str:
        """
        Generate daily Markdown audit log for a specific date.

        Args:
            date: Date in YYYY-MM-DD format (None = today)

        Returns:
            Path to generated Markdown file
        """
        # Parse date or use today
        if date:
            log_date = datetime.fromisoformat(date)
        else:
            log_date = datetime.utcnow()

        date_str = log_date.strftime("%Y-%m-%d")
        logger.info(f"Generating daily audit log for {date_str}")

        # Calculate date range (full day in UTC)
        start_date = log_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)

        start_iso = start_date.isoformat() + "Z"
        end_iso = end_date.isoformat() + "Z"

        # Query audit logs for this date
        entries = self.audit_logger.get_audit_logs(
            start_date=start_iso,
            end_date=end_iso,
            limit=10000  # High limit for daily logs
        )

        # Generate Markdown content
        markdown = self._generate_markdown(date_str, entries)

        # Write to file
        file_path = self.vault_path / f"{date_str}.md"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(markdown)

        logger.info(f"Generated daily audit log: {file_path} ({len(entries)} entries)")
        return str(file_path)

    def _generate_markdown(self, date_str: str, entries: List[Dict[str, Any]]) -> str:
        """
        Generate Markdown content from audit log entries.

        Args:
            date_str: Date string (YYYY-MM-DD)
            entries: List of audit log entries

        Returns:
            Markdown content
        """
        # Header
        markdown = f"# Audit Log: {date_str}\n\n"
        markdown += f"**Generated**: {datetime.utcnow().isoformat()}Z\n"
        markdown += f"**Total Entries**: {len(entries)}\n\n"

        if not entries:
            markdown += "*No audit log entries for this date.*\n"
            return markdown

        # Summary statistics
        markdown += "## Summary\n\n"
        markdown += self._generate_summary(entries)
        markdown += "\n"

        # Group entries by action type
        by_action_type = {}
        for entry in entries:
            action_type = entry["action_type"]
            if action_type not in by_action_type:
                by_action_type[action_type] = []
            by_action_type[action_type].append(entry)

        # Generate sections for each action type
        for action_type in sorted(by_action_type.keys()):
            markdown += f"## {action_type.upper()} Actions\n\n"
            markdown += self._generate_action_section(by_action_type[action_type])
            markdown += "\n"

        # Integrity verification
        markdown += "## Integrity Verification\n\n"
        integrity = self.audit_logger.verify_chain_integrity()
        if integrity["valid"]:
            markdown += "✅ **Hash chain integrity verified** - No tampering detected\n\n"
        else:
            markdown += "⚠️ **Hash chain integrity FAILED** - Possible tampering detected\n\n"
            markdown += f"Broken links: {len(integrity['broken_links'])}\n\n"
            for link in integrity["broken_links"]:
                markdown += f"- Sequence {link['sequence_number']}: {link.get('reason', 'chain_break')}\n"
            markdown += "\n"

        # Footer
        markdown += "---\n\n"
        markdown += "*This audit log is automatically generated and tamper-evident. "
        markdown += "Each entry is cryptographically linked to the previous entry via SHA-256 hash chain.*\n"

        return markdown

    def _generate_summary(self, entries: List[Dict[str, Any]]) -> str:
        """
        Generate summary statistics section.

        Args:
            entries: List of audit log entries

        Returns:
            Markdown summary section
        """
        # Count by action type
        action_counts = {}
        for entry in entries:
            action_type = entry["action_type"]
            action_counts[action_type] = action_counts.get(action_type, 0) + 1

        # Count by safety level
        safety_counts = {0: 0, 1: 0, 2: 0, 3: 0}
        for entry in entries:
            level = entry["safety_level"]
            safety_counts[level] = safety_counts.get(level, 0) + 1

        # Count errors
        error_count = sum(1 for entry in entries if entry["error_message"])

        # Generate summary
        summary = "| Metric | Count |\n"
        summary += "|--------|-------|\n"
        summary += f"| Total Actions | {len(entries)} |\n"

        for action_type, count in sorted(action_counts.items()):
            summary += f"| {action_type.capitalize()} | {count} |\n"

        summary += f"| Errors | {error_count} |\n"
        summary += "\n"

        summary += "**Safety Levels**:\n"
        summary += f"- Level 0 (Auto-Execute): {safety_counts[0]}\n"
        summary += f"- Level 1 (Notify): {safety_counts[1]}\n"
        summary += f"- Level 2 (Confirm): {safety_counts[2]}\n"
        summary += f"- Level 3 (Explicit Approval): {safety_counts[3]}\n"

        return summary

    def _generate_action_section(self, entries: List[Dict[str, Any]]) -> str:
        """
        Generate Markdown section for a group of actions.

        Args:
            entries: List of audit log entries for this action type

        Returns:
            Markdown section content
        """
        section = ""

        for entry in entries:
            # Entry header
            timestamp = entry["timestamp"].replace("Z", "").replace("T", " ")
            section += f"### [{entry['sequence_number']}] {entry['action_name']}\n\n"
            section += f"**Time**: {timestamp} UTC\n"
            section += f"**Safety Level**: {entry['safety_level']}\n"

            # User approval if present
            if entry["user_approval"]:
                section += f"**User Approval**: {entry['user_approval']}\n"

            # Reasoning if present
            if entry["reasoning"]:
                section += f"**Reasoning**: {entry['reasoning']}\n"

            section += "\n"

            # Parameters (collapsed)
            section += "<details>\n"
            section += "<summary>Parameters</summary>\n\n"
            section += "```json\n"
            section += entry["parameters"]
            section += "\n```\n"
            section += "</details>\n\n"

            # Result if present
            if entry["result"]:
                section += "<details>\n"
                section += "<summary>Result</summary>\n\n"
                section += "```json\n"
                section += entry["result"]
                section += "\n```\n"
                section += "</details>\n\n"

            # Error if present
            if entry["error_message"]:
                section += f"⚠️ **Error**: {entry['error_message']}\n\n"

            # Hash for verification
            section += f"<small>Hash: `{entry['entry_hash'][:16]}...`</small>\n\n"
            section += "---\n\n"

        return section

    def generate_weekly_summary(self, week_start: Optional[str] = None) -> str:
        """
        Generate weekly summary audit log.

        Args:
            week_start: Week start date in YYYY-MM-DD format (None = current week)

        Returns:
            Path to generated Markdown file
        """
        # Calculate week start (Monday)
        if week_start:
            start_date = datetime.fromisoformat(week_start)
        else:
            today = datetime.utcnow()
            start_date = today - timedelta(days=today.weekday())

        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=7)

        week_str = start_date.strftime("%Y-W%W")
        logger.info(f"Generating weekly audit summary for {week_str}")

        # Query audit logs for this week
        start_iso = start_date.isoformat() + "Z"
        end_iso = end_date.isoformat() + "Z"

        entries = self.audit_logger.get_audit_logs(
            start_date=start_iso,
            end_date=end_iso,
            limit=100000  # High limit for weekly logs
        )

        # Generate Markdown content
        markdown = f"# Weekly Audit Summary: {week_str}\n\n"
        markdown += f"**Period**: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}\n"
        markdown += f"**Generated**: {datetime.utcnow().isoformat()}Z\n"
        markdown += f"**Total Entries**: {len(entries)}\n\n"

        if entries:
            markdown += "## Summary\n\n"
            markdown += self._generate_summary(entries)

        # Write to file
        file_path = self.vault_path / f"weekly-{week_str}.md"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(markdown)

        logger.info(f"Generated weekly audit summary: {file_path}")
        return str(file_path)

    def generate_all_daily_logs(self, days_back: int = 7) -> List[str]:
        """
        Generate daily logs for the past N days.

        Args:
            days_back: Number of days to generate logs for

        Returns:
            List of generated file paths
        """
        logger.info(f"Generating daily logs for past {days_back} days")

        generated_files = []
        today = datetime.utcnow()

        for i in range(days_back):
            date = today - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")

            try:
                file_path = self.generate_daily_log(date_str)
                generated_files.append(file_path)
            except Exception as e:
                logger.error(f"Failed to generate log for {date_str}: {e}")

        logger.info(f"Generated {len(generated_files)} daily logs")
        return generated_files
