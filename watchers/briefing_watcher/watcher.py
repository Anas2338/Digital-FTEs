"""
Briefing Watcher

Monitors schedule and automatically generates weekly CEO briefings
every Monday at 8:00 AM local time.

Polling Interval: 5 minutes (checks if briefing should be generated)
Safety Level: Level 1 (Notify) - Briefing generation notifies user
"""

import sys
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import logging
import schedule
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from watchers.shared.base_watcher import BaseWatcher
from watchers.shared.audit_logger import AuditLogger
from watchers.briefing_watcher.config import BriefingConfig
from watchers.briefing_watcher.briefing_generator import BriefingGenerator

logger = logging.getLogger(__name__)


class BriefingWatcher(BaseWatcher):
    """
    Watcher for automated CEO briefing generation.

    Generates comprehensive weekly briefings every Monday at 8:00 AM
    containing financial summary, social media performance, tasks, and critical issues.
    """

    def __init__(self):
        """Initialize briefing watcher."""
        super().__init__(
            watcher_name="briefing_watcher",
            polling_interval=300  # 5 minutes
        )

        # Initialize components
        self.config = BriefingConfig()
        self.generator = BriefingGenerator(self.config)
        self.audit_logger = AuditLogger(self.db)

        # Track last generated briefing
        self.last_generated_week = None
        self.last_generated_year = None

        # Setup schedule
        self._setup_schedule()

    def _setup_schedule(self):
        """Setup scheduled briefing generation."""
        # Get cron expression from config
        cron_expr = self.config.get_schedule_cron()
        logger.info(f"Briefing schedule: {cron_expr} ({self.config.schedule_day} at {self.config.schedule_time})")

        # Setup schedule library
        day_map = {
            "monday": schedule.every().monday,
            "tuesday": schedule.every().tuesday,
            "wednesday": schedule.every().wednesday,
            "thursday": schedule.every().thursday,
            "friday": schedule.every().friday,
            "saturday": schedule.every().saturday,
            "sunday": schedule.every().sunday
        }

        scheduler = day_map.get(self.config.schedule_day.lower(), schedule.every().monday)
        time_str = self.config.schedule_time.strftime("%H:%M")
        scheduler.at(time_str).do(self._generate_briefing_job)

        logger.info(f"Scheduled briefing generation for {self.config.schedule_day} at {time_str}")

    def poll(self) -> List[Dict[str, Any]]:
        """
        Poll for scheduled briefing generation.

        Returns:
            List of event dictionaries (empty, as schedule library handles timing)
        """
        # Run pending scheduled jobs
        schedule.run_pending()

        # Check if we should generate briefing now (fallback check)
        now = datetime.now()
        if self.config.should_generate_briefing_now(now):
            current_week = now.isocalendar()[1]
            current_year = now.year

            # Check if we already generated briefing for this week
            if (self.last_generated_week != current_week or
                self.last_generated_year != current_year):
                logger.info("Fallback trigger: Generating briefing now")
                self._generate_briefing_job()

        return []  # No events to process

    def _generate_briefing_job(self):
        """
        Job function for scheduled briefing generation.
        """
        try:
            now = datetime.now()
            week_number = now.isocalendar()[1]
            year = now.year

            logger.info(f"Starting scheduled briefing generation for week {week_number}, {year}")

            # Generate briefing
            result = self.generator.generate_briefing(
                week_number=week_number,
                year=year
            )

            if result.get("success"):
                logger.info(f"Briefing generated successfully: {result['file_path']}")

                # Update tracking
                self.last_generated_week = week_number
                self.last_generated_year = year

                # Log to audit trail
                self.audit_logger.log_action(
                    action_type="generate_briefing",
                    action_name="Weekly CEO Briefing Generation",
                    parameters={
                        "week_number": week_number,
                        "year": year
                    },
                    result={
                        "success": True,
                        "file_path": result["file_path"]
                    },
                    reasoning="Scheduled weekly briefing generation",
                    safety_level=1
                )

                # Create notification in Obsidian vault
                self._create_notification(result)

            else:
                logger.error(f"Briefing generation failed: {result.get('error')}")

        except Exception as e:
            logger.error(f"Error generating briefing: {e}", exc_info=True)

    def _create_notification(self, result: Dict[str, Any]):
        """
        Create notification in Obsidian vault for new briefing.

        Args:
            result: Briefing generation result
        """
        try:
            notification_path = Path("obsidian-vault/Inbox")
            notification_path.mkdir(parents=True, exist_ok=True)

            notification_file = notification_path / f"briefing-week-{result['week_number']}-{result['year']}.md"

            content = f"""# Weekly CEO Briefing Available

**Week**: {result['week_number']}, {result['year']}
**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Location**: [[{result['file_path']}]]

## Quick Summary

Your weekly executive briefing is ready for review.

**Action Required**: Review briefing and address any critical issues flagged.

---

*This is an automated notification from the Digital FTE Agent*
"""

            with open(notification_file, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.info(f"Created briefing notification: {notification_file}")

        except Exception as e:
            logger.error(f"Failed to create notification: {e}")

    def _process_event(self, event: Dict[str, Any]):
        """
        Process events (not used by briefing watcher).

        Args:
            event: Event dictionary
        """
        pass  # Briefing watcher doesn't process events

    def generate_briefing_now(self) -> Dict[str, Any]:
        """
        Manually trigger briefing generation (for testing or on-demand generation).

        Returns:
            Briefing generation result
        """
        logger.info("Manual briefing generation triggered")
        now = datetime.now()
        week_number = now.isocalendar()[1]
        year = now.year

        result = self.generator.generate_briefing(
            week_number=week_number,
            year=year
        )

        if result.get("success"):
            self.last_generated_week = week_number
            self.last_generated_year = year

        return result


def main():
    """Main entry point for briefing watcher."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    watcher = BriefingWatcher()
    try:
        logger.info("Starting briefing watcher...")
        watcher.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, stopping...")
        watcher.stop()


if __name__ == "__main__":
    main()
