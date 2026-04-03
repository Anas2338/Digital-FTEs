"""Social media post tool.

Creates and publishes social media posts across platforms.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from watchers.shared.database import Database
from watchers.shared.audit_logger import AuditLogger
from watchers.social_media_watcher.config import SocialMediaConfig
from watchers.social_media_watcher.facebook_client import FacebookClient
from watchers.social_media_watcher.twitter_client import TwitterClient
from watchers.social_media_watcher.instagram_client import InstagramClient
import json
import uuid
from datetime import datetime


class SocialPostTool:
    """Tool for creating social media posts."""

    def __init__(self):
        """Initialize social post tool."""
        self.db = Database()
        self.audit_logger = AuditLogger(self.db)
        self.config = SocialMediaConfig
        self.clients = {
            "facebook": FacebookClient(),
            "twitter": TwitterClient(),
            "instagram": InstagramClient()
        }

    def execute(
        self,
        content: str,
        platforms: List[str],
        media_urls: Optional[List[str]] = None,
        scheduled_time: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create and publish a social media post."""
        try:
            # Check rate limits before posting
            if not self._check_rate_limits(platforms):
                return {
                    "success": False,
                    "error": f"Rate limit exceeded: {self.config.MAX_POSTS_PER_DAY} posts per day",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }

            post_id = str(uuid.uuid4())

            if scheduled_time:
                return self._schedule_post(
                    post_id, content, platforms, media_urls, scheduled_time
                )

            return self._publish_post(
                post_id, content, platforms, media_urls
            )

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }

    def validate_parameters(
        self,
        content: str,
        platforms: List[str],
        media_urls: Optional[List[str]] = None
    ) -> bool:
        """Validate post parameters."""
        if not content or len(content) > self.config.MAX_CONTENT_LENGTH:
            raise ValueError(f"Content must be 1-{self.config.MAX_CONTENT_LENGTH} characters")

        if not platforms:
            raise ValueError("At least one platform required")

        invalid_platforms = [p for p in platforms if p not in self.config.PLATFORMS]
        if invalid_platforms:
            raise ValueError(f"Invalid platforms: {invalid_platforms}")

        return True

    def _schedule_post(
        self,
        post_id: str,
        content: str,
        platforms: List[str],
        media_urls: Optional[List[str]],
        scheduled_time: str
    ) -> Dict[str, Any]:
        """Schedule a post for later publication."""
        cursor = self.db.conn.cursor()

        cursor.execute("""
            INSERT INTO social_media_posts (
                id, content, media_urls, platforms,
                scheduled_time, status, approval_status
            ) VALUES (?, ?, ?, ?, ?, 'scheduled', 'pending')
        """, (
            post_id,
            content,
            json.dumps(media_urls) if media_urls else None,
            ",".join(platforms),
            scheduled_time
        ))

        self.db.conn.commit()

        self.audit_logger.log_action(
            action_type="social_post_scheduled",
            component="social_media_mcp",
            details={
                "post_id": post_id,
                "platforms": platforms,
                "scheduled_time": scheduled_time
            }
        )

        return {
            "success": True,
            "post_id": post_id,
            "status": "scheduled",
            "scheduled_time": scheduled_time,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

    def _publish_post(
        self,
        post_id: str,
        content: str,
        platforms: List[str],
        media_urls: Optional[List[str]]
    ) -> Dict[str, Any]:
        """Publish a post immediately to all platforms."""
        platform_ids = {}
        publication_results = {}

        for platform in platforms:
            client = self.clients[platform]

            if not client.connected:
                client.connect()

            result = client.post(content, media_urls)
            publication_results[platform] = result

            if result["success"]:
                platform_ids[platform] = result["post_id"]

        cursor = self.db.conn.cursor()

        cursor.execute("""
            INSERT INTO social_media_posts (
                id, content, media_urls, platforms,
                scheduled_time, published_time, status,
                platform_ids, approval_status
            ) VALUES (?, ?, ?, ?, ?, ?, 'published', ?, 'approved')
        """, (
            post_id,
            content,
            json.dumps(media_urls) if media_urls else None,
            ",".join(platforms),
            datetime.now().isoformat(),
            datetime.now().isoformat(),
            json.dumps(platform_ids)
        ))

        self.db.conn.commit()

        self.audit_logger.log_action(
            action_type="social_post_published",
            component="social_media_mcp",
            details={
                "post_id": post_id,
                "platforms": platforms,
                "publication_results": publication_results
            }
        )

        return {
            "success": True,
            "post_id": post_id,
            "status": "published",
            "platform_ids": platform_ids,
            "publication_results": publication_results,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

    def _check_rate_limits(self, platforms: List[str]) -> bool:
        """Check if posting would exceed rate limits."""
        cursor = self.db.conn.cursor()
        today = datetime.now().date().isoformat()

        # Check total posts today
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM social_media_posts
            WHERE DATE(published_time) = ?
            AND status = 'published'
        """, (today,))

        row = cursor.fetchone()
        total_today = row[0] if row else 0

        if total_today >= self.config.MAX_POSTS_PER_DAY:
            return False

        # Check per-platform limits
        for platform in platforms:
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM social_media_posts
                WHERE DATE(published_time) = ?
                AND status = 'published'
                AND platforms LIKE ?
            """, (today, f"%{platform}%"))

            row = cursor.fetchone()
            platform_count = row[0] if row else 0

            if platform_count >= self.config.MAX_POSTS_PER_PLATFORM_PER_DAY:
                return False

        return True
