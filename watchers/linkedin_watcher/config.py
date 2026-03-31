"""LinkedIn watcher configuration."""

from typing import Dict, Any


class LinkedInConfig:
    """Configuration for LinkedIn watcher."""

    # Polling interval in seconds (5 minutes)
    POLLING_INTERVAL = 300

    # Notification types to monitor
    NOTIFICATION_TYPES = [
        "message",
        "connection_request",
        "post_mention",
        "comment",
        "like"
    ]

    # Maximum content length to store
    MAX_CONTENT_LENGTH = 5000

    # Rate limit (requests per hour)
    RATE_LIMIT = 100

    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """Convert config to dict.

        Returns:
            Configuration dict
        """
        return {
            "polling_interval": cls.POLLING_INTERVAL,
            "notification_types": cls.NOTIFICATION_TYPES,
            "max_content_length": cls.MAX_CONTENT_LENGTH,
            "rate_limit": cls.RATE_LIMIT
        }
