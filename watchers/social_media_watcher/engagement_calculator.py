"""
Engagement Metrics Calculator

Calculates average engagement metrics and detects high-performing posts.
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
import logging

from watchers.shared.database import Database
from watchers.social_media_watcher.config import SocialMediaConfig

logger = logging.getLogger(__name__)


class EngagementCalculator:
    """
    Calculates engagement metrics and detects high-performing posts.
    """

    def __init__(self, db: Database = None):
        """Initialize engagement calculator."""
        self.db = db or Database()
        self.config = SocialMediaConfig

    def calculate_average_engagement(
        self,
        platform: str,
        lookback_days: int = 30
    ) -> Dict[str, float]:
        """
        Calculate average engagement metrics for a platform.

        Args:
            platform: Platform name (facebook, instagram, twitter)
            lookback_days: Number of days to look back

        Returns:
            Dictionary with average metrics
        """
        try:
            cursor = self.db.conn.cursor()
            lookback_date = (datetime.now() - timedelta(days=lookback_days)).isoformat()

            # Get all published posts for this platform
            cursor.execute("""
                SELECT engagement_metrics FROM social_media_posts
                WHERE platforms LIKE ?
                AND status = 'published'
                AND published_time >= ?
            """, (f"%{platform}%", lookback_date))

            posts = cursor.fetchall()

            if not posts:
                logger.info(f"No posts found for {platform} in last {lookback_days} days")
                return self._get_empty_averages()

            # Parse and aggregate metrics
            total_metrics = {}
            count = 0

            for post in posts:
                metrics = self._parse_engagement_metrics(
                    post["engagement_metrics"],
                    platform
                )

                if metrics:
                    count += 1
                    for key, value in metrics.items():
                        if isinstance(value, (int, float)):
                            total_metrics[key] = total_metrics.get(key, 0) + value

            # Calculate averages
            if count == 0:
                return self._get_empty_averages()

            averages = {
                key: value / count
                for key, value in total_metrics.items()
            }

            logger.info(
                f"Calculated averages for {platform}: "
                f"{count} posts, {averages}"
            )

            return averages

        except Exception as e:
            logger.error(f"Failed to calculate average engagement: {e}")
            return self._get_empty_averages()

    def detect_high_engagement_posts(
        self,
        platform: str,
        since: datetime = None
    ) -> List[Dict[str, Any]]:
        """
        Detect posts with engagement above threshold.

        Args:
            platform: Platform name
            since: Only check posts published after this time

        Returns:
            List of high-engagement post dictionaries
        """
        try:
            # Get average engagement
            averages = self.calculate_average_engagement(platform)

            if not averages:
                return []

            # Calculate threshold (3x average)
            threshold = self._calculate_total_engagement(averages) * self.config.HIGH_ENGAGEMENT_MULTIPLIER

            # Get recent posts
            cursor = self.db.conn.cursor()
            since_date = since.isoformat() if since else (datetime.now() - timedelta(hours=24)).isoformat()

            cursor.execute("""
                SELECT * FROM social_media_posts
                WHERE platforms LIKE ?
                AND status = 'published'
                AND published_time >= ?
            """, (f"%{platform}%", since_date))

            posts = cursor.fetchall()

            high_engagement_posts = []

            for post in posts:
                metrics = self._parse_engagement_metrics(
                    post["engagement_metrics"],
                    platform
                )

                total_engagement = self._calculate_total_engagement(metrics)

                if total_engagement >= threshold:
                    high_engagement_posts.append({
                        "id": post["id"],
                        "content": post["content"],
                        "platform": platform,
                        "published_time": post["published_time"],
                        "engagement": total_engagement,
                        "threshold": threshold,
                        "metrics": metrics
                    })

            logger.info(
                f"Detected {len(high_engagement_posts)} high-engagement posts "
                f"for {platform} (threshold: {threshold:.0f})"
            )

            return high_engagement_posts

        except Exception as e:
            logger.error(f"Failed to detect high engagement posts: {e}")
            return []

    def _parse_engagement_metrics(self, metrics_json: str, platform: str) -> Dict:
        """Parse engagement metrics JSON."""
        try:
            import json
            metrics = json.loads(metrics_json)
            return metrics.get(platform, {})
        except Exception:
            return {}

    def _calculate_total_engagement(self, metrics: Dict) -> float:
        """Calculate total engagement from metrics."""
        total = 0
        for value in metrics.values():
            if isinstance(value, (int, float)):
                total += value
        return total

    def _get_empty_averages(self) -> Dict[str, float]:
        """Get empty averages structure."""
        return {
            "likes": 0.0,
            "comments": 0.0,
            "shares": 0.0,
            "reach": 0.0
        }
