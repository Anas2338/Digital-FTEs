"""Test LinkedIn connection with session cookies."""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_linkedin():
    """Test LinkedIn API connection."""
    print("Testing LinkedIn connection...")
    print("=" * 60)

    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv('.env')

    email = os.getenv('LINKEDIN_EMAIL')
    li_at = os.getenv('LINKEDIN_LI_AT')

    print(f"Email: {email}")
    print(f"Cookie: {li_at[:30]}...{li_at[-20:]}")
    print()

    # Check if linkedin-api is installed
    try:
        from linkedin_api import Linkedin
        print("[OK] linkedin-api library found")
    except ImportError:
        print("[FAIL] linkedin-api not installed")
        print("\nInstalling linkedin-api...")
        import subprocess
        subprocess.run(['uv', 'add', 'linkedin-api'], check=True)
        from linkedin_api import Linkedin
        print("[OK] linkedin-api installed")

    print("\nConnecting to LinkedIn...")

    try:
        # Initialize client with dummy password (won't be used with cookies)
        api = Linkedin(email, '', authenticate=False)

        # Set cookie
        api.client.cookies.set('li_at', li_at, domain='.linkedin.com')

        # Add proper headers to avoid CSRF issues
        api.client.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/vnd.linkedin.normalized+json+2.1',
            'Accept-Language': 'en-US,en;q=0.9',
            'x-li-lang': 'en_US',
            'x-restli-protocol-version': '2.0.0',
            'csrf-token': 'ajax:' + li_at[:8]
        })

        # Set JSESSIONID cookie
        api.client.cookies.set('JSESSIONID', 'ajax:' + li_at[:8], domain='.linkedin.com')

        # Test: Get profile
        print("Fetching your profile...")
        print(f"Cookie length: {len(li_at)} characters")

        profile = api.get_profile()

        first_name = profile.get('firstName', 'Unknown')
        last_name = profile.get('lastName', 'Unknown')
        headline = profile.get('headline', 'No headline')

        print(f"\n[OK] Connected successfully!")
        print(f"  Name: {first_name} {last_name}")
        print(f"  Headline: {headline}")

        # Test: Get notifications
        print("\nFetching notifications...")
        notifications = api.get_notifications()
        print(f"[OK] Found {len(notifications)} notifications")

        if notifications:
            print("\nRecent notifications:")
            for i, notif in enumerate(notifications[:3], 1):
                text = notif.get('text', 'No text')[:50]
                print(f"  {i}. {text}...")

        print("\n" + "=" * 60)
        print("[OK] LinkedIn connection test PASSED")
        print("\nNext: Start LinkedIn watcher")
        print("  cd watchers")
        print("  uv run python -m linkedin_watcher.watcher")

        return True

    except Exception as e:
        print(f"\n[FAIL] Connection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure you're logged into LinkedIn")
        print("2. Extract a fresh li_at cookie")
        print("3. Check cookie is complete (~200 chars)")
        return False

if __name__ == '__main__':
    test_linkedin()
