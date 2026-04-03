"""
Briefing Watcher Configuration

Defines configuration for weekly CEO briefing generation including
schedule, timezone settings, and content preferences.
"""

from dataclasses import dataclass
from datetime import time
from typing import Optional
import pytz


@dataclass
class BriefingConfig:
    """Configuration for CEO briefing generation."""

    # Schedule configuration
    schedule_day: str = "monday"  # Day of week for briefing generation
    schedule_time: time = time(8, 0)  # 8:00 AM local time
    timezone: str = "UTC"  # Default timezone (should be set to user's local timezone)

    # Content configuration
    include_financial_summary: bool = True
    include_social_media_summary: bool = True
    include_task_summary: bool = True
    include_critical_issues: bool = True
    include_week_over_week_comparison: bool = True

    # Financial summary settings
    financial_lookback_days: int = 7  # Days to include in financial summary
    financial_chart_type: str = "ascii"  # ascii or none

    # Social media summary settings
    social_media_lookback_days: int = 7  # Days to include in social media summary
    social_media_platforms: list = None  # Platforms to include (default: all)

    # Task summary settings
    task_lookback_days: int = 7  # Days to include in task summary

    # Critical issues detection
    critical_issue_thresholds: dict = None

    # Output settings
    output_format: str = "markdown"  # markdown or html
    output_directory: str = "obsidian-vault/Briefings"

    def __post_init__(self):
        """Initialize default values."""
        if self.social_media_platforms is None:
            self.social_media_platforms = ["facebook", "instagram", "twitter"]

        if self.critical_issue_thresholds is None:
            self.critical_issue_thresholds = {
                "overdue_invoices_days": 30,  # Flag invoices overdue by 30+ days
                "low_cash_balance_threshold": 1000.0,  # Flag if cash < $1000
                "negative_profit_margin": True,  # Flag if profit margin is negative
                "social_engagement_drop_percent": 50,  # Flag if engagement drops >50%
                "failed_posts_count": 3,  # Flag if 3+ posts failed to publish
            }

    def get_timezone(self) -> pytz.timezone:
        """
        Get timezone object.

        Returns:
            pytz timezone object
        """
        try:
            return pytz.timezone(self.timezone)
        except pytz.exceptions.UnknownTimeZoneError:
            # Fallback to UTC if timezone is invalid
            return pytz.UTC

    def get_schedule_cron(self) -> str:
        """
        Get cron expression for schedule.

        Returns:
            Cron expression string (e.g., "0 8 * * 1" for Monday 8:00 AM)
        """
        # Map day names to cron day numbers (0=Sunday, 1=Monday, etc.)
        day_map = {
            "sunday": "0",
            "monday": "1",
            "tuesday": "2",
            "wednesday": "3",
            "thursday": "4",
            "friday": "5",
            "saturday": "6"
        }

        day_num = day_map.get(self.schedule_day.lower(), "1")  # Default to Monday
        hour = self.schedule_time.hour
        minute = self.schedule_time.minute

        # Cron format: minute hour day month day_of_week
        return f"{minute} {hour} * * {day_num}"

    def should_generate_briefing_now(self, current_datetime) -> bool:
        """
        Check if briefing should be generated at current time.

        Args:
            current_datetime: Current datetime object

        Returns:
            True if briefing should be generated, False otherwise
        """
        # Convert to configured timezone
        tz = self.get_timezone()
        current_local = current_datetime.astimezone(tz)

        # Check day of week
        day_map = {
            "monday": 0,
            "tuesday": 1,
            "wednesday": 2,
            "thursday": 3,
            "friday": 4,
            "saturday": 5,
            "sunday": 6
        }
        target_day = day_map.get(self.schedule_day.lower(), 0)

        if current_local.weekday() != target_day:
            return False

        # Check time (within 5-minute window)
        current_time = current_local.time()
        target_time = self.schedule_time

        # Calculate time difference in minutes
        current_minutes = current_time.hour * 60 + current_time.minute
        target_minutes = target_time.hour * 60 + target_time.minute

        time_diff = abs(current_minutes - target_minutes)

        # Allow 5-minute window
        return time_diff <= 5

    def get_briefing_filename(self, week_number: int, year: int) -> str:
        """
        Get filename for briefing.

        Args:
            week_number: ISO week number
            year: Year

        Returns:
            Filename string (e.g., "2026-14.md")
        """
        return f"{year}-{week_number:02d}.md"


# Global configuration instance
config = BriefingConfig()
