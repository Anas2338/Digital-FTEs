"""
MCP Tool: Get CEO Briefing

Retrieves a previously generated CEO briefing.

Safety Level: 0 (Auto-Execute) - Read-only operation
"""

from typing import Dict, Any, Optional
import logging
from pathlib import Path

from watchers.briefing_watcher.config import BriefingConfig

logger = logging.getLogger(__name__)


class GetBriefingTool:
    """
    MCP tool for retrieving CEO briefings.
    """

    def __init__(self):
        """Initialize briefing retrieval tool."""
        self.config = BriefingConfig()

    def execute(
        self,
        week_number: Optional[int] = None,
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get CEO briefing for specified week.

        Args:
            week_number: ISO week number (default: current week)
            year: Year (default: current year)

        Returns:
            Result dictionary with briefing content
        """
        try:
            # Use current week if not specified
            from datetime import datetime
            now = datetime.now()
            if week_number is None:
                week_number = now.isocalendar()[1]
            if year is None:
                year = now.year

            # Get briefing file path
            filename = self.config.get_briefing_filename(week_number, year)
            briefing_path = Path(self.config.output_directory) / filename

            if not briefing_path.exists():
                return {
                    "success": False,
                    "message": f"Briefing not found for week {week_number}, {year}",
                    "error": "Briefing file does not exist",
                    "file_path": str(briefing_path)
                }

            # Read briefing content
            with open(briefing_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return {
                "success": True,
                "message": f"Retrieved briefing for week {week_number}, {year}",
                "file_path": str(briefing_path),
                "week_number": week_number,
                "year": year,
                "content": content,
                "content_length": len(content)
            }

        except Exception as e:
            logger.error(f"Error retrieving briefing: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Error retrieving briefing: {str(e)}",
                "error": str(e)
            }


# Tool instance for MCP server registration
tool = GetBriefingTool()


def get_briefing(
    week_number: Optional[int] = None,
    year: Optional[int] = None
) -> Dict[str, Any]:
    """
    Get CEO briefing (function interface for MCP server).

    Args:
        week_number: ISO week number (default: current week)
        year: Year (default: current year)

    Returns:
        Result dictionary
    """
    return tool.execute(week_number, year)
