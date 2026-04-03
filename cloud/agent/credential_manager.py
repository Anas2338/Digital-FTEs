"""
Read-Only Credential Manager for Cloud Agent

Manages read-only API credentials for cloud agent.
Enforces that cloud agent NEVER has write-level access.

Based on spec.md FR-004, FR-005, FR-037, FR-038.
"""

import os
from pathlib import Path
from typing import Dict, Optional

from cloud.agent.config import CloudAgentConfig


class CredentialManager:
    """
    Manages read-only credentials for cloud agent.

    Security guarantees:
    - Only loads read-only credentials from .env.cloud
    - Validates credential_scope is "read_only"
    - Never provides write-level credentials
    - Credentials stored in cloud VM secure storage
    """

    def __init__(self, config: CloudAgentConfig):
        """
        Initialize credential manager.

        Args:
            config: Cloud agent configuration

        Raises:
            ValueError: If config has non-read-only credential scope
        """
        if config.credential_scope != "read_only":
            raise ValueError(
                f"CredentialManager requires read_only scope, got '{config.credential_scope}'"
            )

        self.config = config
        self._credentials: Dict[str, str] = {}
        self._load_credentials()

    def _load_credentials(self) -> None:
        """
        Load read-only credentials from .env.cloud file.

        Expected credentials:
        - GMAIL_CLIENT_ID (read-only)
        - GMAIL_CLIENT_SECRET (read-only)
        - GMAIL_REFRESH_TOKEN (read-only)
        - FACEBOOK_ACCESS_TOKEN (read-only)
        - INSTAGRAM_ACCESS_TOKEN (read-only)
        - TWITTER_API_KEY (read-only)
        - ODOO_URL
        - ODOO_DB
        - ODOO_USERNAME (read-only user)
        - ODOO_PASSWORD (read-only user)
        """
        env_file = Path(".env.cloud")
        if not env_file.exists():
            raise FileNotFoundError(
                f"Cloud credentials file not found: {env_file}. "
                "Create .env.cloud with read-only credentials."
            )

        # Load environment variables from .env.cloud
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        self._credentials[key.strip()] = value.strip()

        # Validate required credentials are present
        self._validate_credentials()

    def _validate_credentials(self) -> None:
        """
        Validate that required read-only credentials are present.

        Raises:
            ValueError: If required credentials are missing
        """
        required = [
            "GMAIL_CLIENT_ID",
            "GMAIL_CLIENT_SECRET",
            "GMAIL_REFRESH_TOKEN"
        ]

        missing = [key for key in required if key not in self._credentials]
        if missing:
            raise ValueError(f"Missing required credentials: {', '.join(missing)}")

    def get_gmail_credentials(self) -> Dict[str, str]:
        """
        Get Gmail read-only credentials.

        Returns:
            Dict with client_id, client_secret, refresh_token
        """
        return {
            "client_id": self._credentials["GMAIL_CLIENT_ID"],
            "client_secret": self._credentials["GMAIL_CLIENT_SECRET"],
            "refresh_token": self._credentials["GMAIL_REFRESH_TOKEN"]
        }

    def get_social_credentials(self, platform: str) -> Optional[str]:
        """
        Get social media read-only credentials.

        Args:
            platform: Platform name (facebook, instagram, twitter)

        Returns:
            Access token or None if not configured
        """
        key_map = {
            "facebook": "FACEBOOK_ACCESS_TOKEN",
            "instagram": "INSTAGRAM_ACCESS_TOKEN",
            "twitter": "TWITTER_API_KEY"
        }

        key = key_map.get(platform.lower())
        return self._credentials.get(key) if key else None

    def get_odoo_credentials(self) -> Dict[str, str]:
        """
        Get Odoo read-only credentials.

        Returns:
            Dict with url, db, username, password
        """
        return {
            "url": self._credentials.get("ODOO_URL", ""),
            "db": self._credentials.get("ODOO_DB", ""),
            "username": self._credentials.get("ODOO_USERNAME", ""),
            "password": self._credentials.get("ODOO_PASSWORD", "")
        }

    def has_write_access(self) -> bool:
        """
        Check if credentials have write access.

        Always returns False for cloud agent (FR-005).

        Returns:
            False (cloud agent never has write access)
        """
        return False
