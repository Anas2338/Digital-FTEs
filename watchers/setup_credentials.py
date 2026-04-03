"""
Credential Setup Script for Digital FTE Gold Tier

This script helps users securely store API credentials in the OS keychain
for Odoo, Facebook, Instagram, and Twitter integrations.

Usage:
    python setup_credentials.py
"""

import keyring
import getpass
import sys
from typing import Dict, List


SERVICE_NAME = "digital-fte"


def store_credential(service_key: str, username: str, prompt: str) -> bool:
    """Store a credential in the OS keychain."""
    try:
        password = getpass.getpass(f"{prompt}: ")
        if not password:
            print(f"  ⚠️  Skipped (empty value)")
            return False

        keyring.set_password(SERVICE_NAME, f"{service_key}:{username}", password)
        print(f"  ✓ Stored successfully")
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def verify_credential(service_key: str, username: str) -> bool:
    """Verify a credential exists in the OS keychain."""
    try:
        password = keyring.get_password(SERVICE_NAME, f"{service_key}:{username}")
        return password is not None
    except Exception:
        return False


def setup_odoo_credentials():
    """Setup Odoo Community Edition credentials."""
    print("\n=== Odoo Community Edition Credentials ===")
    print("Enter your Odoo server details and credentials.")

    credentials = {}

    # Odoo URL
    url = input("Odoo Server URL (e.g., http://localhost:8069): ").strip()
    if url:
        keyring.set_password(SERVICE_NAME, "odoo:url", url)
        credentials['url'] = url

    # Odoo Database
    database = input("Odoo Database Name: ").strip()
    if database:
        keyring.set_password(SERVICE_NAME, "odoo:database", database)
        credentials['database'] = database

    # Odoo Username
    username = input("Odoo Username: ").strip()
    if username:
        keyring.set_password(SERVICE_NAME, "odoo:username", username)
        credentials['username'] = username

    # Odoo Password
    if username:
        store_credential("odoo", "password", "Odoo Password")

    return len(credentials) > 0


def setup_facebook_credentials():
    """Setup Facebook API credentials."""
    print("\n=== Facebook API Credentials ===")
    print("Get your credentials from: https://developers.facebook.com/")

    app_id = input("Facebook App ID: ").strip()
    if app_id:
        keyring.set_password(SERVICE_NAME, "facebook:app_id", app_id)

    if app_id:
        store_credential("facebook", "app_secret", "Facebook App Secret")
        store_credential("facebook", "access_token", "Facebook Access Token")
        return True

    return False


def setup_instagram_credentials():
    """Setup Instagram API credentials (via Facebook Graph API)."""
    print("\n=== Instagram API Credentials ===")
    print("Instagram uses Facebook Graph API. Get credentials from: https://developers.facebook.com/")

    business_account_id = input("Instagram Business Account ID: ").strip()
    if business_account_id:
        keyring.set_password(SERVICE_NAME, "instagram:business_account_id", business_account_id)

    if business_account_id:
        store_credential("instagram", "access_token", "Instagram Access Token")
        return True

    return False


def setup_twitter_credentials():
    """Setup Twitter API credentials."""
    print("\n=== Twitter API Credentials ===")
    print("Get your credentials from: https://developer.twitter.com/")

    api_key = input("Twitter API Key: ").strip()
    if api_key:
        keyring.set_password(SERVICE_NAME, "twitter:api_key", api_key)

    if api_key:
        store_credential("twitter", "api_secret", "Twitter API Secret")
        store_credential("twitter", "access_token", "Twitter Access Token")
        store_credential("twitter", "access_token_secret", "Twitter Access Token Secret")
        return True

    return False


def verify_all_credentials():
    """Verify all stored credentials."""
    print("\n=== Credential Verification ===")

    services = {
        "Odoo": [
            ("odoo:url", "URL"),
            ("odoo:database", "Database"),
            ("odoo:username", "Username"),
            ("odoo:password", "Password"),
        ],
        "Facebook": [
            ("facebook:app_id", "App ID"),
            ("facebook:app_secret", "App Secret"),
            ("facebook:access_token", "Access Token"),
        ],
        "Instagram": [
            ("instagram:business_account_id", "Business Account ID"),
            ("instagram:access_token", "Access Token"),
        ],
        "Twitter": [
            ("twitter:api_key", "API Key"),
            ("twitter:api_secret", "API Secret"),
            ("twitter:access_token", "Access Token"),
            ("twitter:access_token_secret", "Access Token Secret"),
        ],
    }

    for service_name, creds in services.items():
        print(f"\n{service_name}:")
        for key, label in creds:
            exists = False
            try:
                value = keyring.get_password(SERVICE_NAME, key)
                exists = value is not None
            except Exception:
                pass

            status = "✓" if exists else "✗"
            print(f"  {status} {label}")


def main():
    """Main credential setup workflow."""
    print("=" * 60)
    print("Digital FTE Gold Tier - Credential Setup")
    print("=" * 60)
    print("\nThis script will help you securely store API credentials")
    print("in your operating system's keychain.")
    print("\nCredentials are stored using:")
    print("  - Windows: Windows Credential Manager")
    print("  - macOS: Keychain")
    print("  - Linux: Secret Service API")

    # Setup each service
    services_setup = []

    if input("\nSetup Odoo credentials? (y/n): ").lower() == 'y':
        if setup_odoo_credentials():
            services_setup.append("Odoo")

    if input("\nSetup Facebook credentials? (y/n): ").lower() == 'y':
        if setup_facebook_credentials():
            services_setup.append("Facebook")

    if input("\nSetup Instagram credentials? (y/n): ").lower() == 'y':
        if setup_instagram_credentials():
            services_setup.append("Instagram")

    if input("\nSetup Twitter credentials? (y/n): ").lower() == 'y':
        if setup_twitter_credentials():
            services_setup.append("Twitter")

    # Verify all credentials
    verify_all_credentials()

    # Summary
    print("\n" + "=" * 60)
    print("Setup Complete!")
    print("=" * 60)
    if services_setup:
        print(f"\nConfigured services: {', '.join(services_setup)}")
    else:
        print("\nNo services were configured.")

    print("\nYou can re-run this script anytime to update credentials.")
    print("\nNext steps:")
    print("  1. Start the watchers: python -m watchers.odoo_watcher.watcher")
    print("  2. Check the Obsidian vault for detected transactions")
    print("  3. Review the quickstart.md for testing instructions")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError: {e}")
        sys.exit(1)
