"""
Environment Variable Loader

Loads credentials from .env file as fallback to OS keychain.
Provides unified interface for credential retrieval.
"""

import os
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Try to import keyring and python-dotenv
try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False
    logger.warning("keyring not available, using .env only")

try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    logger.warning("python-dotenv not available, using environment variables only")


class CredentialLoader:
    """
    Loads credentials from multiple sources with priority:
    1. Environment variables (highest priority)
    2. .env file
    3. OS keychain (fallback)
    """

    def __init__(self, env_file: str = ".env"):
        """Initialize credential loader."""
        # Look for .env in project root (parent of watchers directory)
        if not Path(env_file).is_absolute():
            # Try current directory first
            if Path(env_file).exists():
                self.env_file = Path(env_file)
            else:
                # Try project root (assuming we're in watchers/ or scripts/)
                project_root = Path(__file__).parent.parent.parent
                self.env_file = project_root / env_file
        else:
            self.env_file = Path(env_file)
        self._load_env_file()
    
    def _load_env_file(self):
        """Load .env file if it exists."""
        if DOTENV_AVAILABLE and self.env_file.exists():
            load_dotenv(self.env_file)
            logger.info(f"Loaded environment variables from {self.env_file}")
        elif self.env_file.exists():
            logger.warning(f".env file exists but python-dotenv not installed")
    
    def get_credential(
        self,
        key: str,
        service: str = "config",
        default: Optional[str] = None
    ) -> Optional[str]:
        """
        Get credential from environment or keychain.
        
        Args:
            key: Credential key (e.g., "odoo_url")
            service: Keychain service name (default: "config")
            default: Default value if not found
            
        Returns:
            Credential value or None
        """
        # 1. Check environment variable (highest priority)
        env_key = key.upper()
        value = os.getenv(env_key)
        if value:
            logger.debug(f"Loaded {key} from environment variable")
            return value
        
        # 2. Try OS keychain (fallback)
        if KEYRING_AVAILABLE:
            try:
                value = keyring.get_password(key, service)
                if value:
                    logger.debug(f"Loaded {key} from OS keychain")
                    return value
            except Exception as e:
                logger.debug(f"Failed to load {key} from keychain: {e}")
        
        # 3. Return default
        if default is not None:
            logger.debug(f"Using default value for {key}")
            return default
        
        logger.warning(f"Credential not found: {key}")
        return None
    
    def get_required_credential(self, key: str, service: str = "config") -> str:
        """
        Get required credential, raises error if not found.
        
        Args:
            key: Credential key
            service: Keychain service name
            
        Returns:
            Credential value
            
        Raises:
            ValueError: If credential not found
        """
        value = self.get_credential(key, service)
        if value is None:
            raise ValueError(
                f"Required credential not found: {key}\n"
                f"Set environment variable {key.upper()} or add to .env file"
            )
        return value
    
    def get_odoo_credentials(self) -> dict:
        """Get all Odoo credentials."""
        return {
            "url": self.get_required_credential("odoo_url"),
            "database": self.get_required_credential("odoo_database"),
            "username": self.get_required_credential("odoo_username"),
            "password": self.get_required_credential("odoo_password")
        }
    
    def get_facebook_credentials(self) -> dict:
        """Get Facebook credentials."""
        return {
            "access_token": self.get_required_credential("facebook_access_token"),
            "page_id": self.get_required_credential("facebook_page_id")
        }
    
    def get_twitter_credentials(self) -> dict:
        """Get Twitter credentials."""
        return {
            "consumer_key": self.get_required_credential("twitter_consumer_key"),
            "consumer_secret": self.get_required_credential("twitter_consumer_secret"),
            "access_token": self.get_required_credential("twitter_access_token"),
            "access_token_secret": self.get_required_credential("twitter_access_token_secret")
        }
    
    def get_instagram_credentials(self) -> dict:
        """Get Instagram credentials."""
        return {
            "account_id": self.get_required_credential("instagram_account_id"),
            "access_token": self.get_required_credential("instagram_access_token")
        }
    
    def get_config(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get configuration value."""
        return self.get_credential(key, default=default)


# Global credential loader instance
_loader = None

def get_loader() -> CredentialLoader:
    """Get global credential loader instance."""
    global _loader
    if _loader is None:
        _loader = CredentialLoader()
    return _loader
