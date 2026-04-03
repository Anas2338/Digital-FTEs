"""
MCP Tool: Add Critical Issue to Briefing

Adds a critical issue to the current week's briefing for immediate attention.

Safety Level: 1 (Notify) - Modifies briefing content
"""

from typing import Dict, Any, Optional
import logging
from pathlib import Path
from datetime import datetime

from watchers.briefing_watcher.config import BriefingConfig

logger = logging.getLogger(__name__)


class AddCriticalIssueTool:
    """
    MCP tool for adding critical issues to briefings.
    """

    def __init__(self):
        """Initialize critical issue tool."""
        self.config = BriefingConfig()

    def execute(
        self,
        title: str,
        description: str,
        severity: str = "high",
        week_number: Optional[int] = None,
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Add critical issue to briefing.

        Args:
            title: Issue title
            description: Issue description
            severity: Severity level (low, medium, high, critical)
            week_number: ISO week number (default: current week)
            year: Year (default: current year)

        Returns:
            Result dictionary
        """
        try:
            # Validate severity
            valid_severities = ["low", "medium", "high", "critical"]
            if severity.lower() not in valid_severities:
                return {
                    "success": False,
                    "message": f"Invalid severity: {severity}. Must be one of: {', '.join(valid_severities)}",
                    "error": "Invalid severity level"
                }

            # Use current week if not specified
            now = datetime.now()
            if week_number is None:
                week_number = now.isocalendar()[1]
            if year is None:
                year = now.year

            # Get briefing file path
            filename = self.config.get_briefing_filename(week_number, year)
            briefing_path = Path(self.config.output_directory) / filename

            # Create issue entry
            issue_entry = f"\n- **{severity.upper()}**: {title}\n  - {description}\n  - Added: {now.strftime('%Y-%m-%d %H:%M')}\n"

            # If briefing exists, append to critical issues section
            if briefing_path.exists():
                with open(briefing_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Find critical issues section
                if "## ⚠️ Requires Attention" in content:
                    # Append to existing section
                    content = content.replace(
                        "## ⚠️ Requires Attention\n\n",
                        f"## ⚠️ Requires Attention\n\n{issue_entry}"
                    )
                else:
                    # Add new section after header
                    lines = content.split('\n')
                    # Find end of header (after Generated line)
                    insert_index = 0
                    for i, line in enumerate(lines):
                        if line.startswith('**Generated**:'):
                            insert_index = i + 2  # After Generated line and blank line
                            break

                    lines.insert(insert_index, f"## ⚠️ Requires Attention\n{issue_entry}")
                    content = '\n'.join(lines)

                # Write updated content
                with open(briefing_path, 'w', encoding='utf-8') as f:
                    f.write(content)

                return {
                    "success": True,
                    "message": f"Critical issue added to briefing for week {week_number}, {year}",
                    "file_path": str(briefing_path),
                    "issue": {
                        "title": title,
                        "description": description,
                        "severity": severity,
                        "added_at": now.isoformat()
                    }
                }
            else:
                # Briefing doesn't exist yet - create a placeholder
                content = f"""# CEO Briefing - Week {week_number}, {year}

**Period**: Week {week_number}
**Generated**: {now.strftime('%Y-%m-%d %H:%M')}

## ⚠️ Requires Attention
{issue_entry}

---

*This briefing was created to track a critical issue. Full briefing will be generated on schedule.*
"""
                briefing_path.parent.mkdir(parents=True, exist_ok=True)
                with open(briefing_path, 'w', encoding='utf-8') as f:
                    f.write(content)

                return {
                    "success": True,
                    "message": f"Created new briefing with critical issue for week {week_number}, {year}",
                    "file_path": str(briefing_path),
                    "issue": {
                        "title": title,
                        "description": description,
                        "severity": severity,
                        "added_at": now.isoformat()
                    }
                }

        except Exception as e:
            logger.error(f"Error adding critical issue: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Error adding critical issue: {str(e)}",
                "error": str(e)
            }


# Tool instance for MCP server registration
tool = AddCriticalIssueTool()


def add_critical_issue(
    title: str,
    description: str,
    severity: str = "high",
    week_number: Optional[int] = None,
    year: Optional[int] = None
) -> Dict[str, Any]:
    """
    Add critical issue to briefing (function interface for MCP server).

    Args:
        title: Issue title
        description: Issue description
        severity: Severity level (low, medium, high, critical)
        week_number: ISO week number (default: current week)
        year: Year (default: current year)

    Returns:
        Result dictionary
    """
    return tool.execute(title, description, severity, week_number, year)
