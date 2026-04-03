"""Get Facebook Page Access Token from User Access Token."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from watchers.shared.env_loader import get_loader
import requests
import json


def get_page_token():
    """Retrieve page access token using user access token."""
    print("=" * 60)
    print("Facebook Page Token Generator")
    print("=" * 60)
    print()

    loader = get_loader()

    try:
        credentials = loader.get_facebook_credentials()
        user_token = credentials["access_token"]
    except Exception as e:
        print(f"[ERROR] Could not load credentials: {e}")
        return

    print("Fetching your Facebook pages...")
    print()

    # Get list of pages managed by this user
    url = f"https://graph.facebook.com/v3.1/me/accounts?access_token={user_token}"

    try:
        response = requests.get(url)
        data = response.json()

        if "error" in data:
            print(f"[ERROR] API Error: {data['error']['message']}")
            print()
            print("Make sure your token has these permissions:")
            print("  - pages_show_list")
            print("  - pages_read_engagement")
            print("  - pages_manage_posts")
            return

        pages = data.get("data", [])

        if not pages:
            print("[ERROR] No pages found. Make sure you're an admin of a Facebook page.")
            return

        print(f"Found {len(pages)} page(s):")
        print()

        for i, page in enumerate(pages, 1):
            print(f"{i}. {page['name']}")
            print(f"   Page ID: {page['id']}")
            print(f"   Access Token: {page['access_token'][:50]}...")
            print()

        print("=" * 60)
        print("INSTRUCTIONS:")
        print("=" * 60)
        print()
        print("Update your .env file with:")
        print()
        print(f"FACEBOOK_PAGE_ID={pages[0]['id']}")
        print(f"FACEBOOK_ACCESS_TOKEN={pages[0]['access_token']}")
        print()
        print("This is a PAGE ACCESS TOKEN (not user token).")
        print("It will allow posting to your page.")
        print()

    except Exception as e:
        print(f"[ERROR] Failed to fetch pages: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    get_page_token()
