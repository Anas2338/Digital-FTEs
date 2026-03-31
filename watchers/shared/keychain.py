"""OS keychain integration for secure credential storage.

Provides cross-platform credential storage using:
- Windows Credential Manager
- macOS Keychain
- Linux Secret Service (via keyring library)
"""

import keyring
from typing import Optional, Dict, Any
import json


class KeychainManager:
    """Manager for secure credential storage in OS keychain."""

    SERVICE_NAME = "digital-fte"

    def __init__(self):
        """Initialize keychain manager."""
        self.service_name = self.SERVICE_NAME

    def store_credential(self, key: str, value: str):
        """Store a credential in the OS keychain.

        Args:
            key: Credential key (e.g., 'gmail-token', 'linkedin-session')
            value: Credential value (token, password, session data)
        """
        keyring.set_password(self.service_name, key, value)

    def get_credential(self, key: str) -> Optional[str]:
        """Retrieve a credential from the OS keychain.

        Args:
            key: Credential key

        Returns:
            Credential value or None if not found
        """
        return keyring.get_password(self.service_name, key)

    def delete_credential(self, key: str):
        """Delete a credential from the OS keychain.

        Args:
            key: Credential key
        """
        try:
            keyring.delete_password(self.service_name, key)
        except keyring.errors.PasswordDeleteError:
            pass  # Credential doesn't exist

    def store_json_credential(self, key: str, data: Dict[str, Any]):
        """Store a JSON credential (for complex data like OAuth tokens).

        Args:
            key: Credential key
            data: Data dict to store as JSON
        """
        json_str = json.dumps(data)
        self.store_credential(key, json_str)

    def get_json_credential(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve a JSON credential.

        Args:
            key: Credential key

        Returns:
            Data dict or None if not found
        """
        json_str = self.get_credential(key)
        if json_str:
            return json.loads(json_str)
        return None

    # Convenience methods for specific credentials

    def store_gmail_token(self, token_data: Dict[str, Any]):
        """Store Gmail OAuth2 token."""
        self.store_json_credential("gmail-token", token_data)

    def get_gmail_token(self) -> Optional[Dict[str, Any]]:
        """Retrieve Gmail OAuth2 token."""
        return self.get_json_credential("gmail-token")

    def store_whatsapp_session(self, session_path: str):
        """Store WhatsApp session path."""
        self.store_credential("whatsapp-session-path", session_path)

    def get_whatsapp_session(self) -> Optional[str]:
        """Retrieve WhatsApp session path."""
        return self.get_credential("whatsapp-session-path")

    def store_linkedin_session(self, cookies: Dict[str, Any]):
        """Store LinkedIn session cookies."""
        self.store_json_credential("linkedin-session", cookies)

    def get_linkedin_session(self) -> Optional[Dict[str, Any]]:
        """Retrieve LinkedIn session cookies."""
        return self.get_json_credential("linkedin-session")
