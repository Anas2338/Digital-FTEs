"""
Domain Context Manager for Digital FTE

Manages domain boundaries between personal and business contexts to ensure
proper data isolation and privacy enforcement.

Domain Types:
- personal: Personal emails, messages, calendar, contacts
- business: Business transactions, accounting, social media, reports
"""

import uuid
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
import logging

from watchers.shared.database import Database


logger = logging.getLogger(__name__)


class DomainType(Enum):
    """Domain types for context separation."""
    PERSONAL = "personal"
    BUSINESS = "business"
    SHARED = "shared"  # Explicitly marked as cross-domain


class PrivacyLevel(Enum):
    """Privacy levels for data classification."""
    PUBLIC = "public"  # Can be shared freely
    INTERNAL = "internal"  # Within domain only
    CONFIDENTIAL = "confidential"  # Restricted access
    SENSITIVE = "sensitive"  # Highest protection (PII, financial)


class DataClassification(Enum):
    """Data classification categories."""
    COMMUNICATION = "communication"  # Emails, messages
    FINANCIAL = "financial"  # Transactions, accounting
    SOCIAL = "social"  # Social media posts, engagement
    CALENDAR = "calendar"  # Events, schedules
    CONTACTS = "contacts"  # People, organizations
    DOCUMENTS = "documents"  # Files, reports


class DomainContextManager:
    """
    Manages domain contexts and enforces boundaries.
    """

    def __init__(self, db: Optional[Database] = None):
        """
        Initialize domain context manager.

        Args:
            db: Database instance (creates new if None)
        """
        self.db = db or Database()
        self.current_context: Optional[Dict[str, Any]] = None

    def create_context(
        self,
        domain_type: DomainType,
        privacy_level: PrivacyLevel,
        data_classification: DataClassification,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new domain context.

        Args:
            domain_type: Type of domain (personal, business, shared)
            privacy_level: Privacy level for this context
            data_classification: Data classification category
            metadata: Additional context metadata

        Returns:
            Context ID
        """
        context_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat() + "Z"

        cursor = self.db.conn.cursor()
        cursor.execute("""
            INSERT INTO domain_context
            (id, domain_type, privacy_level, data_classification, created_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            context_id,
            domain_type.value,
            privacy_level.value,
            data_classification.value,
            timestamp,
            json.dumps(metadata or {})
        ))

        self.db.conn.commit()

        logger.info(
            f"Created domain context: {context_id} "
            f"(type={domain_type.value}, privacy={privacy_level.value})"
        )

        return context_id

    def get_context(self, context_id: str) -> Optional[Dict[str, Any]]:
        """
        Get domain context by ID.

        Args:
            context_id: Context identifier

        Returns:
            Context dict or None if not found
        """
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT * FROM domain_context WHERE id = ?", (context_id,))
        row = cursor.fetchone()

        if row:
            return {
                "id": row["id"],
                "domain_type": row["domain_type"],
                "privacy_level": row["privacy_level"],
                "data_classification": row["data_classification"],
                "created_at": row["created_at"],
                "metadata": json.loads(row["metadata"])
            }
        return None

    def set_current_context(self, context_id: str) -> bool:
        """
        Set the current active domain context.

        Args:
            context_id: Context identifier

        Returns:
            True if context was set, False if not found
        """
        context = self.get_context(context_id)
        if context:
            self.current_context = context
            logger.info(f"Set current context to: {context_id} ({context['domain_type']})")
            return True
        return False

    def get_current_context(self) -> Optional[Dict[str, Any]]:
        """
        Get the current active domain context.

        Returns:
            Current context dict or None
        """
        return self.current_context

    def clear_current_context(self):
        """Clear the current active domain context."""
        self.current_context = None
        logger.info("Cleared current domain context")

    def is_cross_domain_allowed(
        self,
        source_context_id: str,
        target_context_id: str
    ) -> Dict[str, Any]:
        """
        Check if cross-domain access is allowed between two contexts.

        Args:
            source_context_id: Source context ID
            target_context_id: Target context ID

        Returns:
            Dict with allowed flag and reason
        """
        source = self.get_context(source_context_id)
        target = self.get_context(target_context_id)

        if not source or not target:
            return {
                "allowed": False,
                "reason": "Context not found"
            }

        # Same domain is always allowed
        if source["domain_type"] == target["domain_type"]:
            return {
                "allowed": True,
                "reason": "Same domain"
            }

        # Shared domain can access both personal and business
        if source["domain_type"] == "shared" or target["domain_type"] == "shared":
            return {
                "allowed": True,
                "reason": "Shared domain context"
            }

        # Check privacy levels
        source_privacy = PrivacyLevel(source["privacy_level"])
        target_privacy = PrivacyLevel(target["privacy_level"])

        # Public data can be accessed across domains
        if target_privacy == PrivacyLevel.PUBLIC:
            return {
                "allowed": True,
                "reason": "Target data is public"
            }

        # Sensitive data cannot cross domain boundaries
        if target_privacy == PrivacyLevel.SENSITIVE:
            return {
                "allowed": False,
                "reason": "Target data is sensitive and cannot cross domains"
            }

        # Confidential data requires explicit approval
        if target_privacy == PrivacyLevel.CONFIDENTIAL:
            return {
                "allowed": False,
                "reason": "Target data is confidential, requires explicit approval"
            }

        # Internal data can cross domains with logging
        return {
            "allowed": True,
            "reason": "Internal data with audit logging",
            "requires_logging": True
        }

    def get_domain_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about domain contexts.

        Returns:
            Statistics dict
        """
        cursor = self.db.conn.cursor()

        # Count by domain type
        cursor.execute("""
            SELECT domain_type, COUNT(*) as count
            FROM domain_context
            GROUP BY domain_type
        """)
        by_domain = {row["domain_type"]: row["count"] for row in cursor.fetchall()}

        # Count by privacy level
        cursor.execute("""
            SELECT privacy_level, COUNT(*) as count
            FROM domain_context
            GROUP BY privacy_level
        """)
        by_privacy = {row["privacy_level"]: row["count"] for row in cursor.fetchall()}

        # Count by data classification
        cursor.execute("""
            SELECT data_classification, COUNT(*) as count
            FROM domain_context
            GROUP BY data_classification
        """)
        by_classification = {row["data_classification"]: row["count"] for row in cursor.fetchall()}

        return {
            "by_domain_type": by_domain,
            "by_privacy_level": by_privacy,
            "by_data_classification": by_classification,
            "current_context": self.current_context["id"] if self.current_context else None,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

    def infer_domain_from_action(self, action_type: str, parameters: Dict[str, Any]) -> DomainType:
        """
        Infer domain type from action type and parameters.

        Args:
            action_type: Type of action
            parameters: Action parameters

        Returns:
            Inferred domain type
        """
        # Business-related actions
        business_keywords = [
            "odoo", "accounting", "transaction", "invoice", "payment",
            "social", "facebook", "instagram", "twitter", "post",
            "briefing", "report", "financial"
        ]

        # Personal-related actions
        personal_keywords = [
            "gmail", "personal", "calendar", "contact",
            "whatsapp", "message"
        ]

        action_lower = action_type.lower()
        params_str = json.dumps(parameters).lower()

        # Check for business keywords
        if any(keyword in action_lower or keyword in params_str for keyword in business_keywords):
            return DomainType.BUSINESS

        # Check for personal keywords
        if any(keyword in action_lower or keyword in params_str for keyword in personal_keywords):
            return DomainType.PERSONAL

        # Default to shared if unclear
        return DomainType.SHARED
