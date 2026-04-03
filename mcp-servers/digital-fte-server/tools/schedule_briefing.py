"""
MCP Tool: Schedule CEO Briefing

Schedules or reschedules the weekly CEO briefing generation.

Safety Level: 2 (Confirm) - Modifies system schedule, requires user confirmation
"""

from typing import Dict, Any, Optional
import logging
from datetime import time

from watchers.briefing_watcher.config import BriefingConfig

logger = logging.getLogger(__name__)


class ScheduleBriefingTool:
    """
    MCP tool for scheduling CEO briefing generation.
    """

    def __init__(self):
        """Initialize briefing scheduling tool."""
        self.config = BriefingConfig()

    def execute(
        self,
        day_of_week: str,
        time_str: str,
        timezone: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Schedule weekly CEO briefing generation.

        Args:
            day_of_week: Day of week (monday, tuesday, etc.)
            time_str: Time in HH:MM format (e.g., "08:00")
            timezone: Timezone (e.g., "America/New_York", default: UTC)

        Returns:
            Result dictionary
        """
        try:
            # Validate day of week
            valid_days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
            day_lower = day_of_week.lower()
            if day_lower not in valid_days:
                return {
                    "success": False,
                    "message": f"Invalid day: {day_of_week}. Must be one of: {', '.join(valid_days)}",
                    "error": "Invalid day of week"
                }

            # Parse time
            try:
                hour, minute = map(int, time_str.split(':'))
                if not (0 <= hour <= 23 and 0 <= minute <= 59):
                    raise ValueError("Invalid time range")
                schedule_time = time(hour, minute)
            except (ValueError, AttributeError) as e:
                return {
                    "success": False,
                    "message": f"Invalid time format: {time_str}. Use HH:MM format (e.g., '08:00')",
                    "error": "Invalid time format"
                }

            # Validate timezone if provided
            if timezone:
                try:
                    import pytz
                    pytz.timezone(timezone)
                except pytz.exceptions.UnknownTimeZoneError:
                    return {
                        "success": False,
                        "message": f"Invalid timezone: {timezone}",
                        "error": "Invalid timezone"
                    }

            # Update configuration
            # Note: This updates the in-memory config. For persistence,
            # the config should be saved to a file (future enhancement)
            old_schedule = {
                "day": self.config.schedule_day,
                "time": self.config.schedule_time.strftime("%H:%M"),
                "timezone": self.config.timezone
            }

            self.config.schedule_day = day_lower
            self.config.schedule_time = schedule_time
            if timezone:
                self.config.timezone = timezone

            new_schedule = {
                "day": self.config.schedule_day,
                "time": self.config.schedule_time.strftime("%H:%M"),
                "timezone": self.config.timezone,
                "cron": self.config.get_schedule_cron()
            }

            logger.info(f"Briefing schedule updated: {new_schedule}")

            return {
                "success": True,
                "message": f"CEO briefing scheduled for {day_of_week} at {time_str} ({timezone or 'UTC'})",
                "old_schedule": old_schedule,
                "new_schedule": new_schedule,
                "note": "Schedule updated in memory. Restart briefing watcher for changes to take effect."
            }

        except Exception as e:
            logger.error(f"Error scheduling briefing: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Error scheduling briefing: {str(e)}",
                "error": str(e)
            }


# Tool instance for MCP server registration
tool = ScheduleBriefingTool()


def schedule_briefing(
    day_of_week: str,
    time_str: str,
    timezone: Optional[str] = None
) -> Dict[str, Any]:
    """
    Schedule CEO briefing (function interface for MCP server).

    Args:
        day_of_week: Day of week (monday, tuesday, etc.)
        time_str: Time in HH:MM format
        timezone: Timezone (optional, default: UTC)

    Returns:
        Result dictionary
    """
    return tool.execute(day_of_week, time_str, timezone)
