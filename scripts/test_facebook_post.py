"""Test Facebook posting functionality."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from watchers.social_media_watcher.facebook_client import FacebookClient
import json


def test_facebook_post():
    """Test posting to Facebook."""
    print("=" * 60)
    print("Facebook Post Test")
    print("=" * 60)
    print()

    # Test post content
    test_content = "🤖 Digital FTE Test Post - Testing autonomous social media integration. This is an automated test from my AI assistant system."

    print(f"Test post content:")
    print(f'"{test_content}"')
    print()

    # Confirm with user
    print("This will post to your Facebook page.")
    confirm = input("Continue? (yes/no): ").strip().lower()

    if confirm != "yes":
        print("Test cancelled.")
        return False

    print()
    print("Connecting to Facebook...")

    client = FacebookClient()

    if not client.connect():
        print("[ERROR] Failed to connect to Facebook")
        return False

    print("[OK] Connected")
    print()
    print("Publishing post...")

    try:
        result = client.post(content=test_content, media_urls=None)

        if result.get("success"):
            post_id = result.get("post_id")
            print("[OK] Post published successfully!")
            print()
            print(f"Post ID: {post_id}")
            print()

            # Try to get engagement (will be 0 initially)
            print("Fetching post engagement...")
            engagement = client.get_engagement(post_id)
            print(f"Engagement: {json.dumps(engagement, indent=2)}")
            print()

            print("=" * 60)
            print("SUCCESS: Test post published to Facebook!")
            print("=" * 60)
            print()
            print(f"You can view it on your Facebook page or delete it using:")
            print(f"  Post ID: {post_id}")

            return True
        else:
            print(f"[ERROR] Failed to post: {result.get('error', 'Unknown error')}")
            return False

    except Exception as e:
        print(f"[ERROR] Exception during posting: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    try:
        success = test_facebook_post()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
