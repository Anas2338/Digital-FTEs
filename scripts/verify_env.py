#!/usr/bin/env python3
"""
Environment Variables Verification Script

Verifies all required credentials are set and can be loaded.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from watchers.shared.env_loader import get_loader
import os


def check_env_file():
    """Check if .env file exists."""
    env_file = Path(".env")
    if env_file.exists():
        print("✓ .env file found")
        return True
    else:
        print("✗ .env file not found")
        print("  Run: cp .env.example .env")
        return False


def check_credentials():
    """Check all required credentials."""
    print("\n" + "="*70)
    print("Credential Verification")
    print("="*70)
    
    loader = get_loader()
    all_valid = True
    
    # Odoo credentials
    print("\n--- Odoo Credentials ---")
    try:
        creds = loader.get_odoo_credentials()
        print(f"✓ ODOO_URL: {creds['url']}")
        print(f"✓ ODOO_DATABASE: {creds['database']}")
        print(f"✓ ODOO_USERNAME: {creds['username']}")
        print(f"✓ ODOO_PASSWORD: {'*' * len(creds['password'])}")
    except ValueError as e:
        print(f"✗ Odoo credentials incomplete: {e}")
        all_valid = False
    
    # Facebook credentials
    print("\n--- Facebook Credentials ---")
    try:
        creds = loader.get_facebook_credentials()
        token = creds['access_token']
        print(f"✓ FACEBOOK_ACCESS_TOKEN: {token[:20]}...{token[-10:]}")
        print(f"✓ FACEBOOK_PAGE_ID: {creds['page_id']}")
    except ValueError as e:
        print(f"✗ Facebook credentials incomplete: {e}")
        all_valid = False
    
    # Twitter credentials
    print("\n--- Twitter Credentials ---")
    try:
        creds = loader.get_twitter_credentials()
        print(f"✓ TWITTER_CONSUMER_KEY: {creds['consumer_key'][:10]}...")
        print(f"✓ TWITTER_CONSUMER_SECRET: {creds['consumer_secret'][:10]}...")
        print(f"✓ TWITTER_ACCESS_TOKEN: {creds['access_token'][:10]}...")
        print(f"✓ TWITTER_ACCESS_TOKEN_SECRET: {creds['access_token_secret'][:10]}...")
    except ValueError as e:
        print(f"✗ Twitter credentials incomplete: {e}")
        all_valid = False
    
    # Instagram credentials
    print("\n--- Instagram Credentials ---")
    try:
        creds = loader.get_instagram_credentials()
        print(f"✓ INSTAGRAM_ACCOUNT_ID: {creds['account_id']}")
        token = creds['access_token']
        print(f"✓ INSTAGRAM_ACCESS_TOKEN: {token[:20]}...{token[-10:]}")
    except ValueError as e:
        print(f"✗ Instagram credentials incomplete: {e}")
        all_valid = False
    
    return all_valid


def check_optional_config():
    """Check optional configuration values."""
    print("\n--- Optional Configuration ---")
    
    loader = get_loader()
    
    vault_path = loader.get_config("VAULT_PATH", "obsidian-vault")
    print(f"✓ VAULT_PATH: {vault_path}")
    
    odoo_poll = loader.get_config("ODOO_POLL_INTERVAL", "300")
    print(f"✓ ODOO_POLL_INTERVAL: {odoo_poll}s")
    
    social_poll = loader.get_config("SOCIAL_POLL_INTERVAL", "300")
    print(f"✓ SOCIAL_POLL_INTERVAL: {social_poll}s")
    
    max_posts = loader.get_config("MAX_SOCIAL_POSTS_PER_DAY", "10")
    print(f"✓ MAX_SOCIAL_POSTS_PER_DAY: {max_posts}")


def check_security():
    """Check security configuration."""
    print("\n--- Security Check ---")
    
    env_file = Path(".env")
    
    # Check if .env is in .gitignore
    gitignore = Path(".gitignore")
    if gitignore.exists():
        with open(gitignore) as f:
            content = f.read()
            if ".env" in content:
                print("✓ .env is in .gitignore")
            else:
                print("⚠ WARNING: .env not in .gitignore - add it now!")
    
    # Check file permissions (Unix-like systems)
    if hasattr(os, 'stat'):
        try:
            import stat
            st = os.stat(env_file)
            mode = st.st_mode
            if mode & stat.S_IRWXG or mode & stat.S_IRWXO:
                print("⚠ WARNING: .env has group/other permissions")
                print("  Run: chmod 600 .env")
            else:
                print("✓ .env has restrictive permissions")
        except:
            pass


def main():
    """Run verification."""
    print("\n" + "="*70)
    print("Digital FTE Environment Verification")
    print("="*70)
    
    # Check .env file exists
    if not check_env_file():
        print("\n" + "="*70)
        print("✗ FAILED: .env file not found")
        print("="*70)
        print("\nCreate .env file:")
        print("  1. cp .env.example .env")
        print("  2. Edit .env with your credentials")
        print("  3. Run this script again")
        return 1
    
    # Check credentials
    creds_valid = check_credentials()
    
    # Check optional config
    check_optional_config()
    
    # Check security
    check_security()
    
    # Summary
    print("\n" + "="*70)
    if creds_valid:
        print("✓ SUCCESS: All credentials verified")
        print("="*70)
        print("\nNext steps:")
        print("  1. Test connections: python watchers/odoo_watcher/test_connection.py")
        print("  2. Test social media: python watchers/social_media_watcher/test_connections.py")
        print("  3. Start MCP server: cd mcp-servers/digital-fte-server && uvicorn server:app")
        print("  4. Start watchers: python watchers/odoo_watcher/watcher.py")
        return 0
    else:
        print("✗ FAILED: Some credentials missing or invalid")
        print("="*70)
        print("\nFix missing credentials in .env file and run again")
        return 1


if __name__ == "__main__":
    sys.exit(main())
