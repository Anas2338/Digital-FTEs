"""
Domain-Specific Configuration for Digital FTE

Manages configuration settings for personal vs. business domains,
ensuring proper isolation and context-appropriate behavior.
"""

from typing import Dict, Any, Optional
from enum import Enum
import json
from pathlib import Path


class DomainType(Enum):
    """Domain types."""
    PERSONAL = "personal"
    BUSINESS = "business"


class DomainConfig:
    """
    Domain-specific configuration manager.
    """

    def __init__(self, config_path: str = "watchers/shared/domain_config.json"):
        """
        Initialize domain configuration.

        Args:
            config_path: Path to configuration file
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file or create default.

        Returns:
            Configuration dict
        """
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                return json.load(f)

        # Default configuration
        return {
            "personal": {
                "watchers": ["gmail_watcher", "whatsapp_watcher"],
                "integrations": [],
                "data_retention_days": 365,
                "privacy_level": "sensitive",
                "auto_categorize": True,
                "notification_channels": ["email"],
                "rate_limits": {
                    "emails_per_day": 100,
                    "messages_per_day": 200
                }
            },
            "business": {
                "watchers": ["odoo_watcher", "social_media_watcher", "briefing_watcher"],
                "integrations": ["odoo", "facebook", "instagram", "twitter"],
                "data_retention_days": 2555,  # 7 years for compliance
                "privacy_level": "confidential",
                "auto_categorize": True,
                "notification_channels": ["email", "slack"],
                "rate_limits": {
                    "transactions_per_day": 1000,
                    "social_posts_per_day": 10,
                    "api_calls_per_hour": 500
                },
                "accounting": {
                    "categories": [
                        "Revenue",
                        "COGS",
                        "Operating Expenses",
                        "Assets",
                        "Liabilities",
                        "Equity"
                    ],
                    "duplicate_detection_window_hours": 24,
                    "duplicate_similarity_threshold": 0.8
                },
                "social_media": {
                    "high_engagement_threshold_multiplier": 3.0,
                    "platforms": ["facebook", "instagram", "twitter"],
                    "require_approval": True
                },
                "briefing": {
                    "schedule": "Monday 08:00",
                    "timezone": "UTC",
                    "include_charts": True,
                    "retention_weeks": 52
                }
            }
        }

    def get_domain_config(self, domain: DomainType) -> Dict[str, Any]:
        """
        Get configuration for a specific domain.

        Args:
            domain: Domain type

        Returns:
            Domain configuration dict
        """
        return self.config.get(domain.value, {})

    def get_watchers_for_domain(self, domain: DomainType) -> list:
        """
        Get list of watchers for a domain.

        Args:
            domain: Domain type

        Returns:
            List of watcher names
        """
        domain_config = self.get_domain_config(domain)
        return domain_config.get("watchers", [])

    def get_integrations_for_domain(self, domain: DomainType) -> list:
        """
        Get list of integrations for a domain.

        Args:
            domain: Domain type

        Returns:
            List of integration names
        """
        domain_config = self.get_domain_config(domain)
        return domain_config.get("integrations", [])

    def get_rate_limit(self, domain: DomainType, limit_type: str) -> Optional[int]:
        """
        Get rate limit for a specific domain and limit type.

        Args:
            domain: Domain type
            limit_type: Type of rate limit (e.g., "emails_per_day")

        Returns:
            Rate limit value or None if not found
        """
        domain_config = self.get_domain_config(domain)
        rate_limits = domain_config.get("rate_limits", {})
        return rate_limits.get(limit_type)

    def get_data_retention_days(self, domain: DomainType) -> int:
        """
        Get data retention period for a domain.

        Args:
            domain: Domain type

        Returns:
            Retention period in days
        """
        domain_config = self.get_domain_config(domain)
        return domain_config.get("data_retention_days", 365)

    def get_privacy_level(self, domain: DomainType) -> str:
        """
        Get privacy level for a domain.

        Args:
            domain: Domain type

        Returns:
            Privacy level (public, internal, confidential, sensitive)
        """
        domain_config = self.get_domain_config(domain)
        return domain_config.get("privacy_level", "internal")

    def save_config(self):
        """Save configuration to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)

    def update_domain_config(self, domain: DomainType, updates: Dict[str, Any]):
        """
        Update configuration for a domain.

        Args:
            domain: Domain type
            updates: Configuration updates to apply
        """
        if domain.value not in self.config:
            self.config[domain.value] = {}

        self.config[domain.value].update(updates)
        self.save_config()
