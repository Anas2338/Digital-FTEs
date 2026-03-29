"""
Gmail Watcher Script

Monitors Gmail for labeled emails and creates vault notes automatically.
Runs continuously with configurable polling interval.
"""

import os
import sys
import time
import logging
import subprocess
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from watchers.gmail_auth import authenticate_gmail
from watchers.gmail_operations import (
    get_label_id,
    get_messages_with_label,
    get_message_details
)
from watchers.error_handler import GmailErrorHandler
from watchers.utils import sanitize_filename, format_timestamp_filename, format_iso8601
from watchers.vault_utils import generate_frontmatter


class GmailWatcher:
    """
    Gmail watcher that monitors labeled emails and creates vault notes.
    """

    def __init__(
        self,
        label_name: str = 'ToVault',
        poll_interval: int = 180,
        credentials_path: str = '../credentials.json',
        token_path: str = '.auth/token.json',
        vault_path: str = '../obsidian-vault'
    ):
        """
        Initialize Gmail watcher.

        Args:
            label_name: Gmail label to monitor
            poll_interval: Polling interval in seconds (default: 180 = 3 minutes)
            credentials_path: Path to credentials.json
            token_path: Path to token.json
            vault_path: Path to Obsidian vault root
        """
        self.label_name = label_name
        self.poll_interval = poll_interval
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.vault_path = Path(vault_path)

        self.service = None
        self.label_id = None
        self.last_message_id = None
        self.logger = None

        self.setup_logging()

    def setup_logging(self):
        """Configure logging to file and console."""
        # Create logs directory
        log_dir = Path('watchers/logs')
        log_dir.mkdir(parents=True, exist_ok=True)

        # Configure logger
        self.logger = logging.getLogger('GmailWatcher')
        self.logger.setLevel(logging.INFO)

        # File handler
        log_file = log_dir / 'gmail-watcher.log'
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

        self.logger.info("Logging initialized")

    def initialize(self):
        """
        Initialize watcher: authenticate Gmail and get label ID.

        Raises:
            Exception: If initialization fails
        """
        self.logger.info("Initializing Gmail watcher...")
        self.logger.info(f"Label: {self.label_name}")
        self.logger.info(f"Poll interval: {self.poll_interval}s")
        self.logger.info(f"Vault path: {self.vault_path}")

        # Authenticate Gmail
        try:
            self.service = authenticate_gmail(
                self.credentials_path,
                self.token_path
            )
            self.logger.info("Gmail authentication successful")
        except Exception as e:
            self.logger.error(f"Gmail authentication failed: {e}")
            raise

        # Get label ID
        try:
            self.label_id = get_label_id(self.service, self.label_name)
            self.logger.info(f"Label ID: {self.label_id}")
        except Exception as e:
            self.logger.error(f"Failed to get label ID: {e}")
            raise

        # Initialize last_message_id to None (will process all messages on first run)
        self.last_message_id = None
        self.logger.info("Initialization complete")

    def create_vault_note(self, message_details: dict) -> Optional[Path]:
        """
        Create a vault note from email message details.

        Args:
            message_details: Dict with subject, sender, email_date, body, message_id

        Returns:
            Path to created note, or None if creation failed
        """
        try:
            # Generate filename
            timestamp = format_timestamp_filename()
            sanitized_subject = sanitize_filename(
                message_details['subject'],
                max_length=50
            )
            filename = f"{timestamp}-{sanitized_subject}.md"

            # Ensure Inbox folder exists
            inbox_path = self.vault_path / 'Inbox'
            inbox_path.mkdir(parents=True, exist_ok=True)

            note_path = inbox_path / filename

            # Generate frontmatter
            frontmatter = generate_frontmatter(
                title=message_details['subject'],
                created=format_iso8601(),
                source='gmail',
                sender=message_details['sender'],
                email_date=message_details.get('email_date'),
                status='inbox',
                tags=['email']
            )

            # Format note body
            body_header = f"**From:** {message_details['sender']}\n"
            body_header += f"**Date:** {message_details['date']}\n"
            body_header += f"**Message ID:** {message_details['message_id']}\n\n"
            body_header += "---\n\n"

            note_content = frontmatter + body_header + message_details['body'] + "\n"

            # Write note
            with open(note_path, 'w', encoding='utf-8') as f:
                f.write(note_content)

            self.logger.info(f"Created note: {note_path}")
            return note_path

        except Exception as e:
            self.logger.error(f"Failed to create vault note: {e}")
            return None

    def update_dashboard(self):
        """Update dashboard using the update script."""
        try:
            result = subprocess.run(
                ['python', '../scripts/update_dashboard.py'],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                self.logger.info("Dashboard updated successfully")
            else:
                self.logger.warning(f"Dashboard update failed: {result.stderr}")

        except Exception as e:
            self.logger.warning(f"Could not update dashboard: {e}")

    def process_new_messages(self):
        """
        Process new messages with the monitored label.

        Retrieves messages, extracts details, creates vault notes, and updates dashboard.
        """
        try:
            # Get messages with label
            messages = GmailErrorHandler.exponential_backoff_retry(
                get_messages_with_label,
                self.service,
                self.label_id,
                max_results=100
            )

            if not messages:
                self.logger.debug("No messages found")
                return

            self.logger.info(f"Found {len(messages)} message(s) with label '{self.label_name}'")

            # Process each message
            notes_created = 0
            for message in messages:
                message_id = message['id']

                # Skip if already processed (basic deduplication)
                if self.last_message_id and message_id == self.last_message_id:
                    continue

                try:
                    # Get message details with retry
                    self.logger.info(f"Processing message: {message_id}")
                    message_details = GmailErrorHandler.exponential_backoff_retry(
                        get_message_details,
                        self.service,
                        message_id
                    )

                    # Create vault note
                    note_path = self.create_vault_note(message_details)
                    if note_path:
                        notes_created += 1
                        self.logger.info(f"Note created: {note_path.name}")

                except Exception as e:
                    self.logger.error(f"Failed to process message {message_id}: {e}")
                    # Continue with next message
                    continue

            # Update last_message_id to most recent
            if messages:
                self.last_message_id = messages[0]['id']

            # Update dashboard if notes were created
            if notes_created > 0:
                self.logger.info(f"Created {notes_created} note(s), updating dashboard...")
                self.update_dashboard()

        except Exception as e:
            self.logger.error(f"Error processing messages: {e}")
            # Don't raise - continue polling

    def run(self):
        """
        Main run loop: initialize and continuously poll for new messages.

        Runs until interrupted with Ctrl+C.
        """
        try:
            # Initialize
            self.initialize()

            self.logger.info("="*60)
            self.logger.info("Gmail Watcher started")
            self.logger.info(f"Monitoring label: {self.label_name}")
            self.logger.info(f"Polling every {self.poll_interval}s")
            self.logger.info("Press Ctrl+C to stop")
            self.logger.info("="*60)

            # Main polling loop
            while True:
                try:
                    self.process_new_messages()
                except Exception as e:
                    self.logger.error(f"Error in polling loop: {e}")
                    # Continue polling even after error

                # Sleep until next poll
                time.sleep(self.poll_interval)

        except KeyboardInterrupt:
            self.logger.info("\nReceived interrupt signal, shutting down...")
            self.logger.info("Gmail Watcher stopped")

        except Exception as e:
            self.logger.error(f"Fatal error: {e}")
            raise


def main():
    """Main entry point for Gmail watcher."""
    # Load environment variables
    load_dotenv('watchers/.env')

    # Get configuration from environment
    label_name = os.getenv('GMAIL_LABEL', 'ToVault')
    poll_interval = int(os.getenv('POLL_INTERVAL', '180'))
    credentials_path = os.getenv('CREDENTIALS_PATH', 'credentials.json')
    token_path = os.getenv('TOKEN_PATH', 'watchers/.auth/token.json')
    vault_path = os.getenv('VAULT_PATH', 'obsidian-vault')

    # Create and run watcher
    watcher = GmailWatcher(
        label_name=label_name,
        poll_interval=poll_interval,
        credentials_path=credentials_path,
        token_path=token_path,
        vault_path=vault_path
    )

    watcher.run()


if __name__ == '__main__':
    main()
