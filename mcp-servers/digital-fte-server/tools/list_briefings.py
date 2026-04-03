"""
MCP Tool: List CEO Briefings

Lists all available CEO briefings with metadata.

Safety Level: 0 (Auto-Execute) - Read-only operation
"""

from typing import Dict, Any, List
import logging
from pathlib import Path
from datetime import datetime

from watchers.briefing_watcher.config import BriefingConfig

logger = logging.getLogger(__name__)


class ListBriefingsTool:
    """
    MCP tool for listing available CEO briefings.
    """

    def __init__(self):
        """Initialize briefing listing tool."""
        self.config = BriefingConfig()

    def execute(
        self,
        limit: int = 10,
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        List available CEO briefings.

        Args:
            limit: Maximum number of briefings to return (default: 10)
            year: Filter by year (default: all years)

        Returns:
            Result dictionary with list of briefings
        """
        try:
            briefings_dir = Path(self.config.output_directory)

            if not briefings_dir.exists():
                return {
                    "success": True,
                    "message": "No briefings directory found",
                    "briefings": [],
                    "count": 0
                }

            # Find all briefing files (YYYY-WW.md format)
            briefing_files = list(briefings_dir.glob("*.md"))

            # Filter out README
            briefing_files = [f for f in briefing_files if f.name != "README.md"]

            # Parse and sort briefings
            briefings = []
            for file_path in briefing_files:
                try:
                    # Parse filename (YYYY-WW.md)
                    name_parts = file_path.stem.split('-')
                    if len(name_parts) == 2:
                        file_year = int(name_parts[0])
                        week_num = int(name_parts[1])

                        # Filter by year if specified
                        if year is not None and file_year != year:
                            continue

                        # Get file stats
                        stat = file_path.stat()

                        briefings.append({
                            "week_number": week_num,
                            "year": file_year,
                            "filename": file_path.name,
                            "file_path": str(file_path),
                            "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                            "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            "size_bytes": stat.st_size
                        })
                except (ValueError, IndexError) as e:
                    logger.warning(f"Skipping invalid briefing filename: {file_path.name}")
                    continue

            # Sort by year and week (most recent first)
            briefings.sort(key=lambda x: (x["year"], x["week_number"]), reverse=True)

            # Apply limit
            briefings = briefings[:limit]

            return {
                "success": True,
                "message": f"Found {len(briefings)} briefing(s)",
                "briefings": briefings,
                "count": len(briefings),
                "total_available": len(briefing_files) - 1  # Exclude README
            }

        except Exception as e:
            logger.error(f"Error listing briefings: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Error listing briefings: {str(e)}",
                "error": str(e)
            }


# Tool instance for MCP server registration
tool = ListBriefingsTool()


def list_briefings(
    limit: int = 10,
    year: Optional[int] = None
) -> Dict[str, Any]:
    """
    List CEO briefings (function interface for MCP server).

    Args:
        limit: Maximum number of briefings to return
        year: Filter by year (optional)

    Returns:
        Result dictionary
    """
    return tool.execute(limit, year)
