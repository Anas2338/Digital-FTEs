"""Social media delete post tool.

Deletes published posts from social media platforms.
"""

import sys
from pathlib import Path
from typing import Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from watchers.shared.database import Database
from watchers.shared.audit_logger import AuditLogger
from watchers.social_media_watcher.facebook_client import FacebookClient
from watchers.social_media_watcher.twitter_client import TwitterClient
from watchers.social_media_watcher.instagram_client import InstagramClient
import json
from datetime import datetime


class SocialDeletePostTool:
    """Tool for deleting social media posts."""

    def __init__(self):
        """Initialize delete post tool."""
        self.db = Database()
        self.audit_logger = AuditLogger(self.db)
        self.clients = {
            "facebook": FacebookClient(),
            "twitter": TwitterClient(),
            "instagram": InstagramClient()
        }

    def execute(self, post_id: str) -> Dict[str, Any]:
        """Delete a social media post."""
        try:
            cursor = self.db.conn.cursor()

            cursor.execute("""
                SELECT * FROM social_media_posts
                WHERE id = ?
            """, (post_id,))

            post = cursor.fetchone()

            if not post:
                return {
                    "success": False,
                    "error": f"Post not found: {post_id}",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }

            platform_ids = json.loads(post["platform_ids"] or "{}")
            platforms = post["platforms"].split(",")

            deletion_results = {}

            for platform in platforms:
                if platform in platform_ids:
                    client = self.clients[platform]
                    result = client.delete_post(platform_ids[platform])
                    deletion_results[platform] = result

            cursor.execute("""
                UPDATE social_media_posts
                SET status = 'deleted'
                WHERE id = ?
            """, (post_id,))

            self.db.conn.commit()

            self.audit_logger.log_action(
                action_type="social_post_deleted",
                component="social_media_mcp",
                details={
                    "post_id": post_id,
                    "platforms": platforms,
                    "deletion_results": deletion_results
                }
            )

            return {
                "success": True,
                "post_id": post_id,
                "deletion_results": deletion_results,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }

    def validate_parameters(self, post_id: str) -> bool:
        """Validate parameters."""
        if not post_id:
            raise ValueError("Post ID is required")
        return True
