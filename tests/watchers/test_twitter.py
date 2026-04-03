#!/usr/bin/env python3
"""
Quick Twitter Connection Test

Tests if Twitter API credentials are configured correctly.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from watchers.social_media_watcher.twitter_client import TwitterClient


def main():
    print("\n" + "="*60)
    print("Twitter Connection Test")
    print("="*60)

    client = TwitterClient()

    print("\n1. Attempting to connect to Twitter API...")
    if not client.connect():
        print("[FAILED] Could not connect to Twitter")
        print("\nPlease check your credentials in .env:")
        print("  - TWITTER_CONSUMER_KEY")
        print("  - TWITTER_CONSUMER_SECRET")
        print("  - TWITTER_ACCESS_TOKEN")
        print("  - TWITTER_ACCESS_TOKEN_SECRET")
        return 1

    print("[OK] Connected to Twitter API")

    print("\n2. Testing connection and fetching account info...")
    result = client.test_connection()

    if result.get("connected"):
        print("[SUCCESS] Twitter connection successful!")
        user = result.get("user", {})
        print(f"\n  Account: @{user.get('username', 'N/A')}")
        print(f"  User ID: {user.get('id', 'N/A')}")
        print("\n" + "="*60)
        print("[SUCCESS] Your Twitter account is ready to use with Digital FTE!")
        print("="*60)
        return 0
    else:
        print("[FAILED] Twitter connection failed")
        print(f"  Error: {result.get('error', 'Unknown error')}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
