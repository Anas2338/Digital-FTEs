"""Social media connection check tool.

Tests connection status for social media platforms.
"""

import sys
from pathlib import Path
from typing import Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from watchers.social_media_watcher.config import SocialMediaConfig
from watchers.social_media_watcher.facebook_client import FacebookClient
from watchers.social_media_watcher.twitter_client import TwitterClient
from watchers.social_media_watcher.instagram_client import InstagramClient
from datetime import datetime


class SocialCheckConnectionTool:
    """Tool for checking social media platform connections."""

    def __init__(self):
        """Initialize connection check tool."""
        self.config = SocialMediaConfig
        self.clients = {
            "facebook": FacebookClient(),
            "twitter": TwitterClient(),
            "instagram": InstagramClient()
        }

    def execute(self, platform: str) -> Dict[str, Any]:
        """Check connection status for a platform."""
        try:
            if platform not in self.config.PLATFORMS:
                return {
                    "success": False,
                    "error": f"Invalid platform: {platform}",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }

            client = self.clients[platform]
            connection_result = client.test_connection()

            return {
                "success": True,
                "platform": platform,
                "connected": connection_result["success"],
                "details": connection_result,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }

    def validate_parameters(self, platform: str) -> bool:
        """Validate parameters."""
        if not platform:
            raise ValueError("Platform is required")
        if platform not in self.config.PLATFORMS:
            raise ValueError(f"Invalid platform: {platform}")
        return True
