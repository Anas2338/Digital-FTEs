"""API configuration script for Digital FTE watchers.

Handles OAuth2 and session-based authentication setup for:
- Gmail (OAuth2)
- WhatsApp (session-based via QR code)
- LinkedIn (session-based via cookies)
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from watchers.shared.keychain import KeychainManager


def configure_gmail():
    """Configure Gmail OAuth2 credentials.

    This is a placeholder for the actual OAuth2 flow.
    In production, this would:
    1. Open browser for OAuth2 consent
    2. Exchange authorization code for tokens
    3. Store tokens in OS keychain
    """
    print("=== Gmail OAuth2 Configuration ===")
    print()
    print("To configure Gmail:")
    print("1. Go to Google Cloud Console: https://console.cloud.google.com")
    print("2. Create OAuth2 credentials (Desktop app)")
    print("3. Download credentials.json")
    print("4. Run the OAuth2 flow to get tokens")
    print()
    print("For now, this is a placeholder. Full OAuth2 flow will be implemented.")
    print()

    # Placeholder: Store dummy token for development
    keychain = KeychainManager()
    dummy_token = {
        "token": "PLACEHOLDER_TOKEN",
        "refresh_token": "PLACEHOLDER_REFRESH_TOKEN",
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": "PLACEHOLDER_CLIENT_ID",
        "client_secret": "PLACEHOLDER_CLIENT_SECRET",
        "scopes": ["https://www.googleapis.com/auth/gmail.readonly"]
    }

    keychain.store_gmail_token(dummy_token)
    print("✓ Gmail credentials stored in OS keychain (placeholder)")


def configure_whatsapp():
    """Configure WhatsApp session.

    This is a placeholder for WhatsApp Web authentication.
    In production, this would:
    1. Launch Node.js bridge
    2. Display QR code
    3. Wait for user to scan with WhatsApp mobile
    4. Store session path in OS keychain
    """
    print("=== WhatsApp Session Configuration ===")
    print()
    print("To configure WhatsApp:")
    print("1. Ensure Node.js dependencies are installed:")
    print("   cd watchers/whatsapp_watcher && npm install")
    print("2. Run the WhatsApp bridge to generate QR code:")
    print("   node watchers/whatsapp_watcher/bridge.js")
    print("3. Scan QR code with WhatsApp mobile app")
    print("4. Session will be saved to watchers/whatsapp_watcher/.wwebjs_auth/")
    print()
    print("For now, this is a placeholder.")
    print()

    # Placeholder: Store session path
    keychain = KeychainManager()
    session_path = "watchers/whatsapp_watcher/.wwebjs_auth/"
    keychain.store_whatsapp_session(session_path)
    print("✓ WhatsApp session path stored in OS keychain (placeholder)")


def configure_linkedin():
    """Configure LinkedIn session cookies.

    This is a placeholder for LinkedIn authentication.
    In production, this would:
    1. Prompt for LinkedIn credentials
    2. Perform login via linkedin-api library
    3. Extract session cookies
    4. Store cookies in OS keychain
    """
    print("=== LinkedIn Session Configuration ===")
    print()
    print("To configure LinkedIn:")
    print("1. This will use the unofficial linkedin-api library")
    print("2. You'll need to provide your LinkedIn credentials")
    print("3. Session cookies will be stored securely in OS keychain")
    print()
    print("⚠️  WARNING: Using unofficial API may violate LinkedIn ToS")
    print("   Migration path to official API documented in research.md")
    print()
    print("For now, this is a placeholder.")
    print()

    # Placeholder: Store dummy cookies
    keychain = KeychainManager()
    dummy_cookies = {
        "li_at": "PLACEHOLDER_LI_AT_COOKIE",
        "JSESSIONID": "PLACEHOLDER_JSESSIONID"
    }

    keychain.store_linkedin_session(dummy_cookies)
    print("✓ LinkedIn session cookies stored in OS keychain (placeholder)")


def verify_credentials():
    """Verify all credentials are configured."""
    print("=== Credential Verification ===")
    print()

    keychain = KeychainManager()

    # Check Gmail
    gmail_token = keychain.get_gmail_token()
    if gmail_token:
        print("✓ Gmail credentials found")
    else:
        print("✗ Gmail credentials not found")

    # Check WhatsApp
    whatsapp_session = keychain.get_whatsapp_session()
    if whatsapp_session:
        print("✓ WhatsApp session found")
    else:
        print("✗ WhatsApp session not found")

    # Check LinkedIn
    linkedin_session = keychain.get_linkedin_session()
    if linkedin_session:
        print("✓ LinkedIn session found")
    else:
        print("✗ LinkedIn session not found")

    print()


def main():
    """Main entry point for API configuration."""
    parser = argparse.ArgumentParser(
        description="Configure API credentials for Digital FTE watchers"
    )
    parser.add_argument(
        "--service",
        choices=["gmail", "whatsapp", "linkedin", "all"],
        default="all",
        help="Service to configure (default: all)"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify existing credentials"
    )

    args = parser.parse_args()

    if args.verify:
        verify_credentials()
        return

    print("Digital FTE API Configuration")
    print("=" * 50)
    print()

    if args.service in ("gmail", "all"):
        configure_gmail()
        print()

    if args.service in ("whatsapp", "all"):
        configure_whatsapp()
        print()

    if args.service in ("linkedin", "all"):
        configure_linkedin()
        print()

    print("=" * 50)
    print("Configuration complete!")
    print()
    print("Next steps:")
    print("1. Implement full OAuth2 flow for Gmail")
    print("2. Run WhatsApp bridge to generate QR code")
    print("3. Implement LinkedIn login flow")
    print("4. Start watchers: python scripts/setup/install_watchers.py")


if __name__ == "__main__":
    main()
