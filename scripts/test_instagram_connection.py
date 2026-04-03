"""Test Instagram connection and get account ID."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from watchers.shared.env_loader import get_loader
import requests


def test_instagram():
    """Test Instagram connection and retrieve account info."""
    print("=" * 60)
    print("Instagram Connection Test")
    print("=" * 60)
    print()

    loader = get_loader()

    try:
        # Get Facebook credentials
        fb_credentials = loader.get_facebook_credentials()
        page_token = fb_credentials["access_token"]
        page_id = fb_credentials["page_id"]

        print(f"Facebook Page ID: {page_id}")
        print()

        # Check if Instagram account is linked
        print("Checking for linked Instagram Business Account...")
        url = f"https://graph.facebook.com/v18.0/{page_id}?fields=instagram_business_account&access_token={page_token}"

        response = requests.get(url)
        data = response.json()

        if "error" in data:
            print(f"[ERROR] {data['error']['message']}")
            print()
            print("Make sure:")
            print("  1. Your Facebook Page is linked to an Instagram Business Account")
            print("  2. Your token has 'instagram_basic' permission")
            return

        if "instagram_business_account" not in data:
            print("[ERROR] No Instagram Business Account linked to this Facebook Page")
            print()
            print("To link Instagram:")
            print("  1. Go to your Facebook Page settings")
            print("  2. Click 'Instagram' in the left menu")
            print("  3. Connect your Instagram Business Account")
            print()
            print("Note: You need an Instagram BUSINESS account, not personal")
            return

        instagram_id = data['instagram_business_account']['id']

        print(f"✓ Found Instagram Account ID: {instagram_id}")
        print()

        # Get Instagram account details
        print("Fetching Instagram account details...")
        ig_url = f"https://graph.facebook.com/v18.0/{instagram_id}?fields=username,name,profile_picture_url,followers_count,media_count&access_token={page_token}"

        ig_response = requests.get(ig_url)
        ig_data = ig_response.json()

        if "error" in ig_data:
            print(f"[ERROR] {ig_data['error']['message']}")
            return

        print()
        print("=" * 60)
        print("SUCCESS! Instagram Connected")
        print("=" * 60)
        print()
        print(f"Username: @{ig_data.get('username', 'N/A')}")
        print(f"Name: {ig_data.get('name', 'N/A')}")
        print(f"Followers: {ig_data.get('followers_count', 'N/A')}")
        print(f"Posts: {ig_data.get('media_count', 'N/A')}")
        print()
        print("=" * 60)
        print("Add these to your .env file:")
        print("=" * 60)
        print()
        print(f"INSTAGRAM_ACCOUNT_ID={instagram_id}")
        print(f"INSTAGRAM_ACCESS_TOKEN={page_token}")
        print()
        print("Note: You can use the same token as Facebook (Page Access Token)")
        print()

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_instagram()
