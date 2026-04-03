"""
Task Summary Aggregator

Aggregates task completion data from Obsidian vault for CEO briefing.
"""

from typing import Dict, Any
from datetime import datetime
from pathlib import Path
import re
import logging

logger = logging.getLogger(__name__)


class TaskAggregator:
    """
    Aggregates task data for CEO briefing.
    """

    def __init__(self, vault_path: str = "obsidian-vault"):
        """Initialize task aggregator."""
        self.vault_path = Path(vault_path)

    def aggregate_task_summary(
        self,
        period_start: datetime,
        period_end: datetime
    ) -> Dict[str, Any]:
        """
        Aggregate task summary for a time period.

        Args:
            period_start: Start of period
            period_end: End of period

        Returns:
            Task summary dictionary
        """
        try:
            # Scan vault for task markers
            completed_tasks = []
            pending_tasks = []

            # Search all markdown files in vault
            for md_file in self.vault_path.rglob("*.md"):
                tasks = self._extract_tasks_from_file(md_file)
                completed_tasks.extend(tasks["completed"])
                pending_tasks.extend(tasks["pending"])

            summary = {
                "tasks_completed": len(completed_tasks),
                "tasks_pending": len(pending_tasks),
                "completion_rate": self._calculate_completion_rate(
                    len(completed_tasks),
                    len(pending_tasks)
                ),
                "top_completed_tasks": completed_tasks[:5]  # Top 5
            }

            logger.info(
                f"Task summary: {len(completed_tasks)} completed, "
                f"{len(pending_tasks)} pending"
            )

            return summary

        except Exception as e:
            logger.warning(f"Failed to aggregate task summary: {e}")
            return {
                "tasks_completed": 0,
                "tasks_pending": 0,
                "completion_rate": 0.0,
                "top_completed_tasks": []
            }

    def _extract_tasks_from_file(self, file_path: Path) -> Dict[str, list]:
        """Extract tasks from a markdown file."""
        completed = []
        pending = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Find completed tasks: - [x] or - [X]
            completed_pattern = r'- \[x\] (.+)'
            completed_matches = re.findall(completed_pattern, content, re.IGNORECASE)
            completed.extend(completed_matches)

            # Find pending tasks: - [ ]
            pending_pattern = r'- \[ \] (.+)'
            pending_matches = re.findall(pending_pattern, content)
            pending.extend(pending_matches)

        except Exception as e:
            logger.debug(f"Failed to extract tasks from {file_path}: {e}")

        return {
            "completed": completed,
            "pending": pending
        }

    def _calculate_completion_rate(self, completed: int, pending: int) -> float:
        """Calculate task completion rate."""
        total = completed + pending
        if total == 0:
            return 0.0
        return (completed / total) * 100
