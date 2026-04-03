#!/usr/bin/env python3
"""
Social Media Connection Test Script

Tests connections to all configured social media platforms.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from watchers.social_media_watcher.facebook_client import FacebookClient
from watchers.social_media_watcher.twitter_client import TwitterClient
from watchers.social_media_watcher.instagram_client import InstagramClient
from watchers.social_media_watcher.config import SocialMediaConfig


def test_platform_connection(platform_name: str, client):
    """Test connection for a single platform."""
    print(f"\n{'='*60}")
    print(f"Testing {platform_name} connection...")
    print(f"{'='*60}")
    
    try:
        result = client.test_connection()
        
        if result["success"]:
            print(f"✓ {platform_name} connection successful")
            if "user_info" in result:
                print(f"  User: {result['user_info'].get('name', 'N/A')}")
                print(f"  ID: {result['user_info'].get('id', 'N/A')}")
        else:
            print(f"✗ {platform_name} connection failed")
            print(f"  Error: {result.get('error', 'Unknown error')}")
        
        return result["success"]
        
    except Exception as e:
        print(f"✗ {platform_name} connection failed with exception")
        print(f"  Error: {str(e)}")
        return False


def main():
    """Test all social media platform connections."""
    print("\n" + "="*60)
    print("Social Media Platform Connection Test")
    print("="*60)
    
    config = SocialMediaConfig
    print(f"\nConfigured platforms: {', '.join(config.PLATFORMS)}")
    
    clients = {
        "facebook": FacebookClient(),
        "twitter": TwitterClient(),
        "instagram": InstagramClient()
    }
    
    results = {}
    
    for platform in config.PLATFORMS:
        if platform in clients:
            results[platform] = test_platform_connection(platform, clients[platform])
        else:
            print(f"\n✗ {platform}: No client implementation found")
            results[platform] = False
    
    print(f"\n{'='*60}")
    print("Summary")
    print(f"{'='*60}")
    
    successful = sum(1 for success in results.values() if success)
    total = len(results)
    
    for platform, success in results.items():
        status = "✓ Connected" if success else "✗ Failed"
        print(f"{platform:15} {status}")
    
    print(f"\nTotal: {successful}/{total} platforms connected")
    
    if successful == total:
        print("\n✓ All platforms connected successfully!")
        return 0
    else:
        print(f"\n✗ {total - successful} platform(s) failed to connect")
        return 1


if __name__ == "__main__":
    sys.exit(main())
