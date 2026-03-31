"""Send email tool using Gmail API.

Sends emails via Gmail API with OAuth2 authentication.
"""

import sys
from pathlib import Path
from typing import Dict, Any
from email.mime.text import MIMEText
import base64

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from watchers.gmail_auth import authenticate_gmail


class SendEmailTool:
    """Tool for sending emails via Gmail API."""

    def __init__(self):
        """Initialize send email tool."""
        self.credentials_path = "../../credentials.json"
        self.token_path = "../../watchers/.auth/gmail_token.json"
        self.service = None

    def _get_service(self):
        """Get authenticated Gmail service."""
        if not self.service:
            self.service = authenticate_gmail(
                self.credentials_path,
                self.token_path
            )
        return self.service

    def execute(self, recipient: str, subject: str, body: str) -> Dict[str, Any]:
        """Send an email.

        Args:
            recipient: Recipient email address
            subject: Email subject
            body: Email body

        Returns:
            Result dict with success status and message ID
        """
        try:
            # Get authenticated service
            service = self._get_service()

            # Create message
            message = MIMEText(body)
            message['to'] = recipient
            message['subject'] = subject

            # Encode message
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

            # Send message
            result = service.users().messages().send(
                userId='me',
                body={'raw': raw}
            ).execute()

            from datetime import datetime
            return {
                "success": True,
                "message_id": result['id'],
                "thread_id": result.get('threadId'),
                "recipient": recipient,
                "subject": subject,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }

        except Exception as e:
            from datetime import datetime
            return {
                "success": False,
                "error": str(e),
                "recipient": recipient,
                "subject": subject,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }

    def validate_parameters(self, recipient: str, subject: str, body: str) -> bool:
        """Validate email parameters.

        Args:
            recipient: Recipient email address
            subject: Email subject
            body: Email body

        Returns:
            True if valid, raises ValueError if invalid
        """
        if not recipient or "@" not in recipient:
            raise ValueError("Invalid recipient email address")

        if not subject or len(subject) > 200:
            raise ValueError("Subject must be 1-200 characters")

        if not body or len(body) > 10000:
            raise ValueError("Body must be 1-10000 characters")

        return True
