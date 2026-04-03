"""Social media engagement metrics tool.

Retrieves engagement metrics for published posts.
"""

import sys
from pathlib import Path
from typing import Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from watchers.shared.database import Database
import json
from datetime import datetime


class SocialGetEngagementTool:
    """Tool for retrieving social media engagement metrics."""

    def __init__(self):
        """Initialize engagement tool."""
        self.db = Database()

    def execute(self, post_id: str) -> Dict[str, Any]:
        """Get engagement metrics for a post."""
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

            engagement_metrics = json.loads(post["engagement_metrics"] or "{}")

            return {
                "success": True,
                "post_id": post_id,
                "platforms": post["platforms"].split(","),
                "status": post["status"],
                "published_time": post["published_time"],
                "engagement_metrics": engagement_metrics,
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
