"""
Social Media Watcher

Monitors social media engagement and detects high-performing posts.
Polls every 5 minutes for engagement metrics.
"""

import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List

from watchers.shared.database import Database
from watchers.shared.circuit_breaker import CircuitBreaker
from watchers.shared.audit_logger import AuditLogger
from watchers.social_media_watcher.config import SocialMediaConfig
from watchers.social_media_watcher.engagement_calculator import EngagementCalculator
from watchers.social_media_watcher.facebook_client import FacebookClient
from watchers.social_media_watcher.twitter_client import TwitterClient
from watchers.social_media_watcher.instagram_client import InstagramClient

logger = logging.getLogger(__name__)


class SocialMediaWatcher:
    """
    Monitors social media engagement and creates notifications for high-performing posts.
    """

    def __init__(
        self,
        db: Database = None,
        vault_path: str = "obsidian-vault"
    ):
        """Initialize social media watcher."""
        self.db = db or Database()
        self.vault_path = Path(vault_path)
        self.config = SocialMediaConfig

        self.engagement_calculator = EngagementCalculator(self.db)
        self.audit_logger = AuditLogger(self.db)

        self.clients = {
            "facebook": FacebookClient(),
            "twitter": TwitterClient(),
            "instagram": InstagramClient()
        }

        self.circuit_breakers = {
            platform: CircuitBreaker(
                name=f"social_media_{platform}",
                db=self.db
            )
            for platform in self.config.PLATFORMS
        }

        self.last_check = {
            platform: datetime.now() - timedelta(hours=1)
            for platform in self.config.PLATFORMS
        }

        self.running = False

    def start(self):
        """Start the watcher main loop."""
        self.running = True
        logger.info("Social media watcher started")

        self.audit_logger.log_action(
            action_type="watcher_start",
            component="social_media_watcher",
            details={"platforms": self.config.PLATFORMS}
        )

        while self.running:
            try:
                self._check_engagement()
                time.sleep(self.config.POLL_INTERVAL)
            except KeyboardInterrupt:
                logger.info("Received shutdown signal")
                self.stop()
            except Exception as e:
                logger.error(f"Error in watcher main loop: {e}")
                time.sleep(60)

    def stop(self):
        """Stop the watcher."""
        self.running = False
        logger.info("Social media watcher stopped")

        self.audit_logger.log_action(
            action_type="watcher_stop",
            component="social_media_watcher",
            details={}
        )

    def _check_engagement(self):
        """Check engagement metrics for all platforms."""
        for platform in self.config.PLATFORMS:
            try:
                self._check_platform_engagement(platform)
            except Exception as e:
                logger.error(f"Error checking {platform} engagement: {e}")

    def _check_platform_engagement(self, platform: str):
        """Check engagement metrics for a specific platform."""
        circuit_breaker = self.circuit_breakers[platform]

        if not circuit_breaker.can_execute():
            logger.warning(f"Circuit breaker open for {platform}, skipping check")
            return

        try:
            client = self.clients[platform]

            if not client.connected:
                client.connect()

            high_engagement_posts = self.engagement_calculator.detect_high_engagement_posts(
                platform=platform,
                since=self.last_check[platform]
            )

            for post in high_engagement_posts:
                self._create_high_engagement_notification(post)

            self.last_check[platform] = datetime.now()
            circuit_breaker.record_success()

            logger.info(
                f"Checked {platform} engagement: "
                f"{len(high_engagement_posts)} high-performing posts"
            )

        except Exception as e:
            logger.error(f"Failed to check {platform} engagement: {e}")
            circuit_breaker.record_failure()

            self.audit_logger.log_action(
                action_type="engagement_check_failed",
                component="social_media_watcher",
                details={
                    "platform": platform,
                    "error": str(e)
                }
            )

    def _create_high_engagement_notification(self, post: Dict[str, Any]):
        """Create Obsidian vault task for high engagement post."""
        try:
            notifications_dir = self.vault_path / "Notifications"
            notifications_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"high_engagement_{post['platform']}_{timestamp}.md"
            filepath = notifications_dir / filename

            content = self._format_notification(post)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.info(f"Created high engagement notification: {filename}")

            self.audit_logger.log_action(
                action_type="high_engagement_detected",
                component="social_media_watcher",
                details={
                    "platform": post["platform"],
                    "post_id": post["id"],
                    "engagement": post["engagement"],
                    "threshold": post["threshold"],
                    "notification_file": str(filepath)
                }
            )

        except Exception as e:
            logger.error(f"Failed to create high engagement notification: {e}")

    def _format_notification(self, post: Dict[str, Any]) -> str:
        """Format notification content."""
        platform = post["platform"].capitalize()
        engagement = post["engagement"]
        threshold = post["threshold"]
        multiplier = engagement / threshold if threshold > 0 else 0

        content_preview = post['content'][:200]
        if len(post['content']) > 200:
            content_preview += '...'

        lines = [
            f"# High Engagement Alert - {platform}",
            "",
            "## Post Details",
            f"- **Platform**: {platform}",
            f"- **Published**: {post['published_time']}",
            f"- **Post ID**: {post['id']}",
            "",
            "## Content",
            content_preview,
            "",
            "## Engagement Metrics",
            f"- **Total Engagement**: {engagement:.0f}",
            f"- **Threshold**: {threshold:.0f}",
            f"- **Performance**: {multiplier:.1f}x average",
            "",
            "### Breakdown"
        ]

        for metric, value in post['metrics'].items():
            lines.append(f"- **{metric.capitalize()}**: {value}")

        lines.extend([
            "",
            "## Action Items",
            "- [ ] Review post performance",
            "- [ ] Analyze what made this post successful",
            "- [ ] Consider similar content strategy",
            "- [ ] Engage with high-performing comments",
            "",
            "---",
            f"*Generated by Social Media Watcher on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
        ])

        return '\n'.join(lines)

    def get_status(self) -> Dict[str, Any]:
        """Get watcher status."""
        return {
            "running": self.running,
            "platforms": self.config.PLATFORMS,
            "last_check": {
                platform: time.isoformat()
                for platform, time in self.last_check.items()
            },
            "circuit_breakers": {
                platform: cb.get_state()
                for platform, cb in self.circuit_breakers.items()
            }
        }


def main():
    """Main entry point for social media watcher."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    watcher = SocialMediaWatcher()

    try:
        watcher.start()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        watcher.stop()


if __name__ == "__main__":
    main()
