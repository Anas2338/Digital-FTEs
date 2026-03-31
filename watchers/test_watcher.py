"""Quick test script for Gmail watcher."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from watchers.gmail_watcher.watcher import GmailWatcher

def test_watcher():
    """Test Gmail watcher for one poll cycle."""
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

    print("\nPolling for messages with 'ToVault' label...")
    events = watcher.poll()

    print(f"\nFound {len(events)} event(s)")

    if events:
        print("\nEvents:")
        for i, event in enumerate(events, 1):
            print(f"\n{i}. {event['event_type']}")
            print(f"   Subject: {event['content']['subject']}")
            print(f"   From: {event['content']['sender']}")
            print(f"   Date: {event['content']['date']}")
    else:
        print("\nNo messages with 'ToVault' label found.")
        print("To test: Send yourself an email and apply the 'ToVault' label in Gmail.")

    print("\n✓ Gmail watcher test complete")

if __name__ == '__main__':
    test_watcher()
