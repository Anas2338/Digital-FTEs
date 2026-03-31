"""Test full Gmail watcher with vault note creation."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from watchers.gmail_watcher.watcher import GmailWatcher

def test_full_watcher():
    """Test Gmail watcher with full event processing."""
    print("Creating Gmail watcher...")

    watcher = GmailWatcher(
        label_name='ToVault',
        poll_interval=180,
        credentials_path='../credentials.json',
        token_path='.auth/gmail_token.json',
        vault_path='../obsidian-vault'
    )

    print("Initializing Gmail connection...")
    watcher.initialize()

    print("\nPolling for messages...")
    events = watcher.poll()

    print(f"Found {len(events)} event(s)")

    if events:
        print("\nProcessing events through BaseWatcher...")
        for event in events:
            watcher._process_event(event)

        print("\nCheck obsidian-vault/Inbox/ for new notes")
    else:
        print("\nNo new messages found.")

    print("\nTest complete")

if __name__ == '__main__':
    test_full_watcher()
