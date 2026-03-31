"""Mock API fixtures for testing Digital FTE watchers.

Provides mock implementations of Gmail, WhatsApp, and LinkedIn APIs
for unit and integration testing.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid


class MockGmailAPI:
    """Mock Gmail API for testing."""

    def __init__(self):
        """Initialize mock Gmail API."""
        self.messages = []
        self._add_sample_messages()

    def _add_sample_messages(self):
        """Add sample messages for testing."""
        self.messages = [
            {
                "id": "msg001",
                "threadId": "thread001",
                "labelIds": ["INBOX", "ToVault"],
                "snippet": "Q1 revenue report attached...",
                "payload": {
                    "headers": [
                        {"name": "From", "value": "cfo@company.com"},
                        {"name": "Subject", "value": "Q1 Revenue Report"},
                        {"name": "Date", "value": "2026-03-30T14:30:00Z"}
                    ],
                    "body": {
                        "data": "Please review the attached Q1 revenue report. Key highlights: Revenue up 25% YoY."
                    }
                }
            },
            {
                "id": "msg002",
                "threadId": "thread002",
                "labelIds": ["INBOX", "ToVault"],
                "snippet": "Meeting request for tomorrow...",
                "payload": {
                    "headers": [
                        {"name": "From", "value": "manager@company.com"},
                        {"name": "Subject", "value": "Meeting Request: Strategy Review"},
                        {"name": "Date", "value": "2026-03-30T15:00:00Z"}
                    ],
                    "body": {
                        "data": "Can we schedule a meeting tomorrow at 10am to review our Q2 strategy?"
                    }
                }
            }
        ]

    def list_messages(self, label_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """List messages with optional label filtering.

        Args:
            label_ids: Optional list of label IDs to filter by

        Returns:
            List of message dicts
        """
        if label_ids:
            return [
                msg for msg in self.messages
                if any(label in msg["labelIds"] for label in label_ids)
            ]
        return self.messages

    def get_message(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific message by ID.

        Args:
            message_id: Message ID

        Returns:
            Message dict or None
        """
        for msg in self.messages:
            if msg["id"] == message_id:
                return msg
        return None

    def send_message(self, to: str, subject: str, body: str) -> Dict[str, Any]:
        """Mock send message.

        Args:
            to: Recipient email
            subject: Email subject
            body: Email body

        Returns:
            Sent message dict
        """
        message_id = f"msg{len(self.messages) + 1:03d}"
        return {
            "id": message_id,
            "threadId": f"thread{len(self.messages) + 1:03d}",
            "labelIds": ["SENT"]
        }


class MockWhatsAppAPI:
    """Mock WhatsApp API for testing."""

    def __init__(self):
        """Initialize mock WhatsApp API."""
        self.messages = []
        self._add_sample_messages()

    def _add_sample_messages(self):
        """Add sample messages for testing."""
        self.messages = [
            {
                "id": "3EB0C767D26A1234",
                "from": "+14155552671",
                "fromName": "John Doe",
                "body": "Can we schedule a call tomorrow?",
                "timestamp": "2026-03-30T15:45:00Z",
                "isGroup": False
            },
            {
                "id": "3EB0C767D26A5678",
                "from": "+14155552672",
                "fromName": "Jane Smith",
                "body": "Thanks for the update!",
                "timestamp": "2026-03-30T16:00:00Z",
                "isGroup": False
            }
        ]

    def get_messages(self) -> List[Dict[str, Any]]:
        """Get all messages.

        Returns:
            List of message dicts
        """
        return self.messages

    def send_message(self, to: str, body: str) -> Dict[str, Any]:
        """Mock send message.

        Args:
            to: Recipient phone number
            body: Message body

        Returns:
            Sent message dict
        """
        message_id = f"3EB0C767D26A{len(self.messages) + 1:04d}"
        return {
            "id": message_id,
            "to": to,
            "body": body,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }


class MockLinkedInAPI:
    """Mock LinkedIn API for testing."""

    def __init__(self):
        """Initialize mock LinkedIn API."""
        self.notifications = []
        self._add_sample_notifications()

    def _add_sample_notifications(self):
        """Add sample notifications for testing."""
        self.notifications = [
            {
                "id": "urn:li:message:12345",
                "type": "message",
                "from": {
                    "name": "Jane Doe",
                    "profileUrl": "https://linkedin.com/in/janedoe"
                },
                "content": "I saw your post about AI automation...",
                "timestamp": "2026-03-30T16:20:00Z"
            },
            {
                "id": "urn:li:connection:67890",
                "type": "connection_request",
                "from": {
                    "name": "Bob Smith",
                    "profileUrl": "https://linkedin.com/in/bobsmith"
                },
                "content": "I'd like to connect with you",
                "timestamp": "2026-03-30T17:00:00Z"
            }
        ]

    def get_notifications(self) -> List[Dict[str, Any]]:
        """Get all notifications.

        Returns:
            List of notification dicts
        """
        return self.notifications

    def post_update(self, content: str) -> Dict[str, Any]:
        """Mock post update.

        Args:
            content: Post content

        Returns:
            Posted update dict
        """
        post_id = f"urn:li:share:{len(self.notifications) + 1}"
        return {
            "id": post_id,
            "content": content,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "views": 0,
            "likes": 0,
            "comments": 0
        }


# Factory functions for easy test setup

def create_mock_gmail_api() -> MockGmailAPI:
    """Create a mock Gmail API instance."""
    return MockGmailAPI()


def create_mock_whatsapp_api() -> MockWhatsAppAPI:
    """Create a mock WhatsApp API instance."""
    return MockWhatsAppAPI()


def create_mock_linkedin_api() -> MockLinkedInAPI:
    """Create a mock LinkedIn API instance."""
    return MockLinkedInAPI()
