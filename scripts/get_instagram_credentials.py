"""Get Instagram Business Account credentials via Facebook Graph API."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import requests


def get_instagram_credentials():
    """Interactive script to get Instagram credentials."""
    print("=" * 60)
    print("Instagram Credentials Setup")
    print("=" * 60)
    print()
    print("Prerequisites:")
    print("  1. Instagram Business Account (not personal)")
    print("  2. Facebook Page linked to Instagram account")
    print("  3. Facebook App with Instagram permissions")
    print()
    print("=" * 60)
    print()

    # Get user access token
    print("Step 1: Get Facebook User Access Token")
    print()
    print("Go to: https://developers.facebook.com/tools/explorer/")
    print("  - Select your Facebook App")
    print("  - Click 'Generate Access Token'")
    print("  - Add permissions: instagram_basic, instagram_content_publish, pages_read_engagement")
    print()

    user_token = input("Paste your User Access Token: ").strip()

    if not user_token:
        print("[ERROR] Token is required")
        return

    print()
    print("Fetching your Facebook pages...")
    print()

    # Get Facebook pages
    url = f"https://graph.facebook.com/v18.0/me/accounts?access_token={user_token}"

    try:
        response = requests.get(url)
        data = response.json()

        if "error" in data:
            print(f"[ERROR] {data['error']['message']}")
            return

        pages = data.get("data", [])

        if not pages:
            print("[ERROR] No pages found. You must be admin of a Facebook page.")
            return

        print(f"Found {len(pages)} page(s):")
        print()

        for i, page in enumerate(pages, 1):
            print(f"{i}. {page['name']} (ID: {page['id']})")

        print()

        if len(pages) == 1:
            selected_page = pages[0]
        else:
            choice = int(input(f"Select page (1-{len(pages)}): ")) - 1
            selected_page = pages[choice]

        page_id = selected_page['id']
        page_token = selected_page['access_token']

        print()
        print(f"Selected: {selected_page['name']}")
        print()
        print("Fetching Instagram Business Account...")
        print()

        # Get Instagram account linked to this page
        ig_url = f"https://graph.facebook.com/v18.0/{page_id}?fields=instagram_business_account&access_token={page_token}"

        ig_response = requests.get(ig_url)
        ig_data = ig_response.json()

        if "instagram_business_account" not in ig_data:
            print("[ERROR] No Instagram Business Account linked to this page.")
            print()
            print("To fix this:")
            print("  1. Go to your Facebook Page settings")
            print("  2. Navigate to 'Instagram' section")
            print("  3. Connect your Instagram Business Account")
            return

        instagram_account_id = ig_data['instagram_business_account']['id']

        # Verify Instagram access
        verify_url = f"https://graph.facebook.com/v18.0/{instagram_account_id}?fields=username,id&access_token={page_token}"
        verify_response = requests.get(verify_url)
        verify_data = verify_response.json()

        if "error" in verify_data:
            print(f"[ERROR] Cannot access Instagram account: {verify_data['error']['message']}")
            return

        username = verify_data.get('username', 'Unknown')

        print("=" * 60)
        print("SUCCESS!")
        print("=" * 60)
        print()
        print(f"Instagram Account: @{username}")
        print(f"Account ID: {instagram_account_id}")
        print()
        print("Add these to your .env file:")
        print()
        print(f"INSTAGRAM_ACCOUNT_ID={instagram_account_id}")
        print(f"INSTAGRAM_ACCESS_TOKEN={page_token}")
        print()
        print("Note: This token is a Page Access Token that works for Instagram.")
        print("It will expire - consider getting a long-lived token.")
        print()

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    get_instagram_credentials()
