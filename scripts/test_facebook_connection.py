"""Test Facebook connection with configured credentials."""

import sys
from pathlib import Path

# Add project root to path so watchers.* imports work
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from watchers.social_media_watcher.facebook_client import FacebookClient
import json


def test_facebook_connection():
    """Test Facebook API connection."""
    print("=" * 60)
    print("Facebook Connection Test")
    print("=" * 60)
    print()

    client = FacebookClient()

    # Test connection
    print("Attempting to connect to Facebook...")
    connect_result = client.connect()

    if connect_result:
        print("[OK] Successfully connected to Facebook API")
        print()

        # Test API call
        print("Testing API access...")
        test_result = client.test_connection()

        if test_result.get("connected"):
            print("[OK] Facebook API is working correctly")
            print()
            print("Account Information:")
            print(json.dumps(test_result.get("user", {}), indent=2))
            print()
            print("=" * 60)
            print("SUCCESS: Facebook page is connected!")
            print("=" * 60)
            return True
        else:
            print("[ERROR] API test failed")
            print(f"Error: {test_result.get('error', 'Unknown error')}")
            return False
    else:
        print("[ERROR] Failed to connect to Facebook")
        print()
        print("Troubleshooting:")
        print("1. Check that FACEBOOK_ACCESS_TOKEN is set in .env")
        print("2. Verify the token is valid (not expired)")
        print("3. Ensure the token has required permissions:")
        print("   - pages_show_list")
        print("   - pages_read_engagement")
        print("   - pages_manage_posts")
        return False


if __name__ == "__main__":
    try:
        success = test_facebook_connection()
        sys.exit(0 if success else 1)
    except Exception as e:
        print()
        print("=" * 60)
        print("ERROR")
        print("=" * 60)
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
