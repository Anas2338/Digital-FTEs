"""
MCP Tool: Generate CEO Briefing

Generates a comprehensive weekly executive briefing with financial summary,
social media performance, tasks, and critical issues.

Safety Level: 1 (Notify) - Briefing generation notifies user
"""

from typing import Dict, Any, Optional
import logging
from datetime import datetime

from watchers.briefing_watcher.briefing_generator import BriefingGenerator
from watchers.briefing_watcher.config import BriefingConfig

logger = logging.getLogger(__name__)


class GenerateBriefingTool:
    """
    MCP tool for generating CEO briefings.
    """

    def __init__(self):
        """Initialize briefing generation tool."""
        self.config = BriefingConfig()
        self.generator = BriefingGenerator(self.config)

    def execute(
        self,
        week_number: Optional[int] = None,
        year: Optional[int] = None,
        force_regenerate: bool = False
    ) -> Dict[str, Any]:
        """
        Generate CEO briefing for specified week.

        Args:
            week_number: ISO week number (default: current week)
            year: Year (default: current year)
            force_regenerate: Force regeneration even if briefing exists

        Returns:
            Result dictionary with success status and briefing details
        """
        try:
            # Use current week if not specified
            now = datetime.now()
            if week_number is None:
                week_number = now.isocalendar()[1]
            if year is None:
                year = now.year

            logger.info(f"Generating CEO briefing for week {week_number}, {year}")

            # Check if briefing already exists
            filename = self.config.get_briefing_filename(week_number, year)
            from pathlib import Path
            briefing_path = Path(self.config.output_directory) / filename

            if briefing_path.exists() and not force_regenerate:
                logger.info(f"Briefing already exists: {briefing_path}")
                return {
                    "success": True,
                    "message": f"Briefing for week {week_number}, {year} already exists",
                    "file_path": str(briefing_path),
                    "week_number": week_number,
                    "year": year,
                    "regenerated": False
                }

            # Generate briefing
            result = self.generator.generate_briefing(
                week_number=week_number,
                year=year
            )

            if result.get("success"):
                return {
                    "success": True,
                    "message": f"CEO briefing generated successfully for week {week_number}, {year}",
                    "file_path": result["file_path"],
                    "week_number": week_number,
                    "year": year,
                    "regenerated": force_regenerate,
                    "data_summary": {
                        "has_financial": "financial" in result.get("data", {}),
                        "has_social_media": "social_media" in result.get("data", {}),
                        "has_tasks": "tasks" in result.get("data", {}),
                        "critical_issues_count": len(result.get("data", {}).get("critical_issues", []))
                    }
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to generate briefing: {result.get('error', 'Unknown error')}",
                    "error": result.get("error")
                }

        except Exception as e:
            logger.error(f"Error generating briefing: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Error generating briefing: {str(e)}",
                "error": str(e)
            }


# Tool instance for MCP server registration
tool = GenerateBriefingTool()


def generate_briefing(
    week_number: Optional[int] = None,
    year: Optional[int] = None,
    force_regenerate: bool = False
) -> Dict[str, Any]:
    """
    Generate CEO briefing (function interface for MCP server).

    Args:
        week_number: ISO week number (default: current week)
        year: Year (default: current year)
        force_regenerate: Force regeneration even if briefing exists

    Returns:
        Result dictionary
    """
    return tool.execute(week_number, year, force_regenerate)
