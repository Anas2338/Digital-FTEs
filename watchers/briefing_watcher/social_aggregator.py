"""
Social Media Summary Aggregator

Aggregates social media performance data for CEO briefing.
Gracefully handles missing data when social media integration is not available.
"""

from typing import Dict, Any, List
from datetime import datetime
import logging

from watchers.shared.database import Database
from watchers.briefing_watcher.config import BriefingConfig

logger = logging.getLogger(__name__)


class SocialAggregator:
    """
    Aggregates social media data for CEO briefing.
    """

    def __init__(self, db: Database = None):
        """Initialize social media aggregator."""
        self.db = db or Database()
        self.config = BriefingConfig

    def aggregate_social_summary(
        self,
        period_start: datetime,
        period_end: datetime
    ) -> Dict[str, Any]:
        """
        Aggregate social media summary for a time period.

        Args:
            period_start: Start of period
            period_end: End of period

        Returns:
            Social media summary dictionary (empty if no data available)
        """
        try:
            # Check if social_media_posts table exists
            if not self._table_exists("social_media_posts"):
                logger.info("Social media posts table not found - returning empty summary")
                return self._get_empty_summary()

            summary = {}

            for platform in self.config.PLATFORMS:
                platform_summary = self._aggregate_platform_summary(
                    platform,
                    period_start,
                    period_end
                )
                summary[platform] = platform_summary

            logger.info(f"Social media summary aggregated for {len(summary)} platforms")
            return summary

        except Exception as e:
            logger.warning(f"Failed to aggregate social media summary: {e}")
            return self._get_empty_summary()

    def _table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database."""
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name=?
            """, (table_name,))
            return cursor.fetchone() is not None
        except Exception:
            return False

    def _aggregate_platform_summary(
        self,
        platform: str,
        period_start: datetime,
        period_end: datetime
    ) -> Dict[str, Any]:
        """Aggregate summary for a specific platform."""
        try:
            cursor = self.db.conn.cursor()

            # Get posts for this platform in the period
            cursor.execute("""
                SELECT * FROM social_media_posts
                WHERE platforms LIKE ?
                AND published_time >= ?
                AND published_time <= ?
                AND status = 'published'
            """, (f"%{platform}%", period_start.isoformat(), period_end.isoformat()))

            posts = [dict(row) for row in cursor.fetchall()]

            if not posts:
                return {
                    "posts_published": 0,
                    "total_engagement": 0,
                    "top_post": None
                }

            # Calculate total engagement
            total_engagement = 0
            top_post = None
            max_engagement = 0

            for post in posts:
                engagement_metrics = self._parse_engagement_metrics(
                    post.get("engagement_metrics", "{}"),
                    platform
                )
                post_engagement = self._calculate_post_engagement(engagement_metrics, platform)
                total_engagement += post_engagement

                if post_engagement > max_engagement:
                    max_engagement = post_engagement
                    top_post = {
                        "content": post["content"][:50] + "..." if len(post["content"]) > 50 else post["content"],
                        "engagement": post_engagement
                    }

            return {
                "posts_published": len(posts),
                "total_engagement": total_engagement,
                "top_post": top_post
            }

        except Exception as e:
            logger.warning(f"Failed to aggregate {platform} summary: {e}")
            return {
                "posts_published": 0,
                "total_engagement": 0,
                "top_post": None
            }

    def _parse_engagement_metrics(self, metrics_json: str, platform: str) -> Dict:
        """Parse engagement metrics JSON."""
        try:
            import json
            metrics = json.loads(metrics_json)
            return metrics.get(platform, {})
        except Exception:
            return {}

    def _calculate_post_engagement(self, metrics: Dict, platform: str) -> int:
        """Calculate total engagement for a post."""
        engagement = 0
        metric_names = self.config.get_engagement_metrics_for_platform(platform)

        for metric in metric_names:
            if metric in metrics:
                value = metrics[metric]
                if isinstance(value, (int, float)):
                    engagement += int(value)

        return engagement

    def _get_empty_summary(self) -> Dict[str, Any]:
        """Get empty summary structure."""
        summary = {}
        for platform in self.config.PLATFORMS:
            summary[platform] = {
                "posts_published": 0,
                "total_engagement": 0,
                "top_post": None
            }
        return summary
