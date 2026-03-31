"""Gmail Watcher - Silver Tier Implementation

Monitors Gmail for labeled emails and creates vault notes automatically.
Integrates with Silver Tier architecture (BaseWatcher, Database, VaultWriter).
"""

import sys
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from watchers.shared.base_watcher import BaseWatcher
from watchers.shared.database import Database
from watchers.shared.vault_writer import VaultWriter
from watchers.gmail_auth import authenticate_gmail
from watchers.gmail_operations import (
    get_label_id,
    get_messages_with_label,
    get_message_details
)


class GmailWatcher(BaseWatcher):
    """Gmail watcher that monitors labeled emails."""

    def __init__(
        self,
        label_name: str = 'ToVault',
        poll_interval: int = 180,
        credentials_path: str = 'credentials.json',
        token_path: str = 'watchers/.auth/gmail_token.json',
        vault_path: str = 'obsidian-vault'
    ):
        """Initialize Gmail watcher.

        Args:
            label_name: Gmail label to monitor
            poll_interval: Polling interval in seconds (default: 180)
            credentials_path: Path to credentials.json
            token_path: Path to token.json
            vault_path: Path to Obsidian vault
        """
        super().__init__("gmail_watcher", poll_interval)

        self.label_name = label_name
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.vault_writer = VaultWriter(vault_path)

        self.service = None
        self.label_id = None
        self.processed_message_ids = set()

    def initialize(self):
        """Initialize Gmail API connection."""
        print(f"[{self.watcher_name}] Initializing Gmail watcher...")
        print(f"[{self.watcher_name}] Label: {self.label_name}")

        try:
            # Authenticate Gmail
            self.service = authenticate_gmail(
                self.credentials_path,
                self.token_path
            )
            print(f"[{self.watcher_name}] Gmail authentication successful")

            # Get label ID
            self.label_id = get_label_id(self.service, self.label_name)
            print(f"[{self.watcher_name}] Label ID: {self.label_id}")

        except Exception as e:
            print(f"[{self.watcher_name}] Gmail initialization failed: {e}")
            raise

    def poll(self) -> List[Dict[str, Any]]:
        """Poll for new Gmail messages with the monitored label.

        Returns:
            List of event dicts
        """
        if not self.service or not self.label_id:
            return []

        try:
            # Get messages with label
            messages = get_messages_with_label(
                self.service,
                self.label_id,
                max_results=100
            )

            if not messages:
                return []

            events = []
            for message in messages:
                message_id = message['id']

                # Skip if already processed
                if message_id in self.processed_message_ids:
                    continue

                try:
                    # Get message details
                    message_details = get_message_details(self.service, message_id)

                    # Convert to event format
                    event = {
                        "event_type": "email_received",
                        "content": {
                            "subject": message_details['subject'],
                            "sender": message_details['sender'],
                            "date": message_details['date'],
                            "body": message_details['body'],
                            "message_id": message_id
                        }
                    }

                    events.append(event)
                    self.processed_message_ids.add(message_id)

                except Exception as e:
                    print(f"Failed to process message {message_id}: {e}")
                    continue

            return events

        except Exception as e:
            print(f"Error fetching Gmail messages: {e}")
            return []

    def get_config(self) -> Dict[str, Any]:
        """Get watcher configuration.

        Returns:
            Configuration dict
        """
        vault_path = self.vault_writer.vault_path if hasattr(self.vault_writer, 'vault_path') else 'obsidian-vault'
        return {
            "label_name": self.label_name,
            "poll_interval": self.polling_interval,
            "credentials_path": str(self.credentials_path),
            "token_path": str(self.token_path),
            "vault_path": str(vault_path)
        }

    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"


def main():
    """Main entry point for Gmail watcher."""
    import os
    from dotenv import load_dotenv

    # Load environment variables
    load_dotenv('watchers/.env')

    # Get configuration
    label_name = os.getenv('GMAIL_LABEL', 'ToVault')
    poll_interval = int(os.getenv('POLL_INTERVAL', '180'))
    credentials_path = os.getenv('CREDENTIALS_PATH', '../credentials.json')
    token_path = os.getenv('TOKEN_PATH', '.auth/gmail_token.json')
    vault_path = os.getenv('VAULT_PATH', '../obsidian-vault')

    # Create and run watcher
    watcher = GmailWatcher(
        label_name=label_name,
        poll_interval=poll_interval,
        credentials_path=credentials_path,
        token_path=token_path,
        vault_path=vault_path
    )

    # Initialize Gmail connection
    watcher.initialize()

    # Start watcher loop
    watcher.start()


if __name__ == '__main__':
    main()
