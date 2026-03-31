"""LinkedIn watcher implementation using linkedin-api library.

This watcher monitors LinkedIn notifications (messages, connection requests,
post mentions) using the unofficial linkedin-api library.
"""

import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from watchers.shared.base_watcher import BaseWatcher

try:
    from linkedin_api import Linkedin
except ImportError:
    Linkedin = None


class LinkedInWatcher(BaseWatcher):
    """LinkedIn watcher using linkedin-api library."""

    def __init__(
        self,
        email: Optional[str] = None,
        li_at_cookie: Optional[str] = None,
        poll_interval: int = 300
    ):
        """Initialize LinkedIn watcher.

        Args:
            email: LinkedIn email address
            li_at_cookie: LinkedIn li_at session cookie
            poll_interval: Polling interval in seconds (default: 300)
        """
        super().__init__("linkedin_watcher", poll_interval)

        self.email = email or os.getenv('LINKEDIN_EMAIL')
        self.li_at_cookie = li_at_cookie or os.getenv('LINKEDIN_LI_AT')
        self.linkedin_client = None
        self.last_notification_id = None
        self.processed_notification_ids = set()

    def initialize(self):
        """Initialize LinkedIn API client."""
        if not Linkedin:
            raise ImportError(
                "linkedin-api not installed. Run: uv add linkedin-api"
            )

        if not self.email or not self.li_at_cookie:
            raise ValueError(
                "LinkedIn credentials not provided. Set LINKEDIN_EMAIL and LINKEDIN_LI_AT "
                "environment variables or pass to constructor."
            )

        print(f"[{self.watcher_name}] Initializing LinkedIn watcher...")
        print(f"[{self.watcher_name}] Email: {self.email}")

        try:
            # Initialize LinkedIn client
            self.linkedin_client = Linkedin(self.email, authenticate=False)
            self.linkedin_client.client.cookies.set(
                'li_at',
                self.li_at_cookie,
                domain='.linkedin.com'
            )

            # Test connection by getting profile
            profile = self.linkedin_client.get_profile()
            print(f"[{self.watcher_name}] Connected as: {profile.get('firstName')} {profile.get('lastName')}")

        except Exception as e:
            print(f"[{self.watcher_name}] LinkedIn initialization failed: {e}")
            raise

    def poll(self) -> List[Dict[str, Any]]:
        """Poll for new LinkedIn notifications.

        Returns:
            List of event dicts
        """
        if not self.linkedin_client:
            return []

        try:
            # Get notifications
            notifications = self.linkedin_client.get_notifications()

            if not notifications:
                return []

            events = []
            for notification in notifications:
                notification_id = notification.get('id')

                # Skip if already processed
                if notification_id in self.processed_notification_ids:
                    continue

                try:
                    # Parse notification into event format
                    event = self._parse_notification(notification)
                    events.append(event)
                    self.processed_notification_ids.add(notification_id)

                except Exception as e:
                    print(f"[{self.watcher_name}] Failed to parse notification {notification_id}: {e}")
                    continue

            return events

        except Exception as e:
            print(f"[{self.watcher_name}] Error fetching notifications: {e}")
            return []

    def get_config(self) -> Dict[str, Any]:
        """Get watcher configuration.

        Returns:
            Configuration dict
        """
        return {
            "email": self.email,
            "poll_interval": self.polling_interval,
            "has_credentials": bool(self.email and self.li_at_cookie)
        }

    def _parse_notification(self, notification: Dict[str, Any]) -> Dict[str, Any]:
        """Parse LinkedIn notification into event format.

        Args:
            notification: Raw notification from LinkedIn API

        Returns:
            Formatted event dict
        """
        # Extract notification details
        actor = notification.get('actor', {})
        notification_type = notification.get('type', 'notification')

        return {
            "event_type": f"linkedin_{notification_type}",
            "content": {
                "notification_id": notification.get('id'),
                "notification_type": notification_type,
                "sender_name": actor.get('name', 'Unknown'),
                "sender_profile_url": actor.get('profileUrl', ''),
                "text": notification.get('text', ''),
                "timestamp": notification.get('timestamp', ''),
                "read": notification.get('read', False)
            }
        }


def main():
    """Main entry point for LinkedIn watcher."""
    from dotenv import load_dotenv

    # Load environment variables
    load_dotenv('../.env')

    # Get configuration
    email = os.getenv('LINKEDIN_EMAIL')
    li_at_cookie = os.getenv('LINKEDIN_LI_AT')
    poll_interval = int(os.getenv('POLL_INTERVAL', '300'))

    # Create and run watcher
    watcher = LinkedInWatcher(
        email=email,
        li_at_cookie=li_at_cookie,
        poll_interval=poll_interval
    )

    # Initialize LinkedIn connection
    watcher.initialize()

    # Start watcher loop
    watcher.start()


if __name__ == "__main__":
    main()
    main()
