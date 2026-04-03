"""
Unit tests for DomainContextManager class.

Tests domain context creation, boundary enforcement, and privacy levels.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from watchers.shared.domain_manager import (
    DomainContextManager,
    DomainType,
    PrivacyLevel,
    DataClassification
)
from watchers.shared.database import Database


class TestDomainContextCreation:
    """Test domain context creation and retrieval."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create temporary database for testing."""
        db_path = tmp_path / "test.db"
        return Database(str(db_path))

    @pytest.fixture
    def manager(self, db):
        """Create domain context manager instance."""
        return DomainContextManager(db=db)

    def test_create_personal_context(self, manager):
        """Test creating a personal domain context."""
        context_id = manager.create_context(
            domain_type=DomainType.PERSONAL,
            privacy_level=PrivacyLevel.SENSITIVE,
            data_classification=DataClassification.COMMUNICATION,
            metadata={"source": "gmail"}
        )

        assert context_id is not None
        context = manager.get_context(context_id)
        assert context["domain_type"] == "personal"
        assert context["privacy_level"] == "sensitive"
        assert context["data_classification"] == "communication"
        assert context["metadata"]["source"] == "gmail"

    def test_create_business_context(self, manager):
        """Test creating a business domain context."""
        context_id = manager.create_context(
            domain_type=DomainType.BUSINESS,
            privacy_level=PrivacyLevel.CONFIDENTIAL,
            data_classification=DataClassification.FINANCIAL,
            metadata={"source": "odoo"}
        )

        context = manager.get_context(context_id)
        assert context["domain_type"] == "business"
        assert context["privacy_level"] == "confidential"
        assert context["data_classification"] == "financial"

    def test_create_shared_context(self, manager):
        """Test creating a shared domain context."""
        context_id = manager.create_context(
            domain_type=DomainType.SHARED,
            privacy_level=PrivacyLevel.PUBLIC,
            data_classification=DataClassification.SOCIAL
        )

        context = manager.get_context(context_id)
        assert context["domain_type"] == "shared"
        assert context["privacy_level"] == "public"

    def test_get_nonexistent_context(self, manager):
        """Test retrieving a context that doesn't exist."""
        context = manager.get_context("nonexistent-id")
        assert context is None


class TestCurrentContextManagement:
    """Test current context management."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create temporary database for testing."""
        db_path = tmp_path / "test.db"
        return Database(str(db_path))

    @pytest.fixture
    def manager(self, db):
        """Create domain context manager instance."""
        return DomainContextManager(db=db)

    def test_set_current_context(self, manager):
        """Test setting the current active context."""
        context_id = manager.create_context(
            domain_type=DomainType.PERSONAL,
            privacy_level=PrivacyLevel.INTERNAL,
            data_classification=DataClassification.CALENDAR
        )

        result = manager.set_current_context(context_id)
        assert result is True
        assert manager.get_current_context()["id"] == context_id

    def test_set_nonexistent_context(self, manager):
        """Test setting a context that doesn't exist."""
        result = manager.set_current_context("nonexistent-id")
        assert result is False
        assert manager.get_current_context() is None

    def test_clear_current_context(self, manager):
        """Test clearing the current context."""
        context_id = manager.create_context(
            domain_type=DomainType.BUSINESS,
            privacy_level=PrivacyLevel.INTERNAL,
            data_classification=DataClassification.DOCUMENTS
        )

        manager.set_current_context(context_id)
        assert manager.get_current_context() is not None

        manager.clear_current_context()
        assert manager.get_current_context() is None


class TestCrossDomainAccess:
    """Test cross-domain access control."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create temporary database for testing."""
        db_path = tmp_path / "test.db"
        return Database(str(db_path))

    @pytest.fixture
    def manager(self, db):
        """Create domain context manager instance."""
        return DomainContextManager(db=db)

    def test_same_domain_access_allowed(self, manager):
        """Test that same domain access is always allowed."""
        ctx1 = manager.create_context(
            DomainType.PERSONAL, PrivacyLevel.SENSITIVE, DataClassification.COMMUNICATION
        )
        ctx2 = manager.create_context(
            DomainType.PERSONAL, PrivacyLevel.CONFIDENTIAL, DataClassification.CONTACTS
        )

        result = manager.is_cross_domain_allowed(ctx1, ctx2)
        assert result["allowed"] is True
        assert result["reason"] == "Same domain"

    def test_shared_domain_access_allowed(self, manager):
        """Test that shared domain can access other domains."""
        shared_ctx = manager.create_context(
            DomainType.SHARED, PrivacyLevel.PUBLIC, DataClassification.SOCIAL
        )
        personal_ctx = manager.create_context(
            DomainType.PERSONAL, PrivacyLevel.INTERNAL, DataClassification.CALENDAR
        )

        result = manager.is_cross_domain_allowed(shared_ctx, personal_ctx)
        assert result["allowed"] is True
        assert "Shared domain" in result["reason"]

    def test_public_data_cross_domain_allowed(self, manager):
        """Test that public data can be accessed across domains."""
        personal_ctx = manager.create_context(
            DomainType.PERSONAL, PrivacyLevel.INTERNAL, DataClassification.COMMUNICATION
        )
        business_ctx = manager.create_context(
            DomainType.BUSINESS, PrivacyLevel.PUBLIC, DataClassification.SOCIAL
        )

        result = manager.is_cross_domain_allowed(personal_ctx, business_ctx)
        assert result["allowed"] is True
        assert "public" in result["reason"].lower()

    def test_sensitive_data_cross_domain_blocked(self, manager):
        """Test that sensitive data cannot cross domain boundaries."""
        personal_ctx = manager.create_context(
            DomainType.PERSONAL, PrivacyLevel.INTERNAL, DataClassification.COMMUNICATION
        )
        business_ctx = manager.create_context(
            DomainType.BUSINESS, PrivacyLevel.SENSITIVE, DataClassification.FINANCIAL
        )

        result = manager.is_cross_domain_allowed(personal_ctx, business_ctx)
        assert result["allowed"] is False
        assert "sensitive" in result["reason"].lower()

    def test_confidential_data_requires_approval(self, manager):
        """Test that confidential data requires explicit approval."""
        personal_ctx = manager.create_context(
            DomainType.PERSONAL, PrivacyLevel.INTERNAL, DataClassification.COMMUNICATION
        )
        business_ctx = manager.create_context(
            DomainType.BUSINESS, PrivacyLevel.CONFIDENTIAL, DataClassification.FINANCIAL
        )

        result = manager.is_cross_domain_allowed(personal_ctx, business_ctx)
        assert result["allowed"] is False
        assert "confidential" in result["reason"].lower()

    def test_internal_data_requires_logging(self, manager):
        """Test that internal data cross-domain access requires logging."""
        personal_ctx = manager.create_context(
            DomainType.PERSONAL, PrivacyLevel.INTERNAL, DataClassification.COMMUNICATION
        )
        business_ctx = manager.create_context(
            DomainType.BUSINESS, PrivacyLevel.INTERNAL, DataClassification.DOCUMENTS
        )

        result = manager.is_cross_domain_allowed(personal_ctx, business_ctx)
        assert result["allowed"] is True
        assert result.get("requires_logging") is True


class TestDomainInference:
    """Test domain type inference from actions."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create temporary database for testing."""
        db_path = tmp_path / "test.db"
        return Database(str(db_path))

    @pytest.fixture
    def manager(self, db):
        """Create domain context manager instance."""
        return DomainContextManager(db=db)

    def test_infer_business_from_odoo_action(self, manager):
        """Test inferring business domain from Odoo action."""
        domain = manager.infer_domain_from_action(
            "odoo_record_transaction",
            {"amount": 1000, "category": "Revenue"}
        )
        assert domain == DomainType.BUSINESS

    def test_infer_business_from_social_media_action(self, manager):
        """Test inferring business domain from social media action."""
        domain = manager.infer_domain_from_action(
            "social_post",
            {"platform": "facebook", "content": "New product launch"}
        )
        assert domain == DomainType.BUSINESS

    def test_infer_personal_from_gmail_action(self, manager):
        """Test inferring personal domain from Gmail action."""
        domain = manager.infer_domain_from_action(
            "gmail_send",
            {"to": "friend@example.com", "subject": "Dinner plans"}
        )
        assert domain == DomainType.PERSONAL

    def test_infer_personal_from_whatsapp_action(self, manager):
        """Test inferring personal domain from WhatsApp action."""
        domain = manager.infer_domain_from_action(
            "whatsapp_message",
            {"contact": "Mom", "message": "On my way home"}
        )
        assert domain == DomainType.PERSONAL

    def test_infer_shared_from_ambiguous_action(self, manager):
        """Test inferring shared domain from ambiguous action."""
        domain = manager.infer_domain_from_action(
            "generic_action",
            {"data": "something"}
        )
        assert domain == DomainType.SHARED


class TestDomainStatistics:
    """Test domain statistics reporting."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create temporary database for testing."""
        db_path = tmp_path / "test.db"
        return Database(str(db_path))

    @pytest.fixture
    def manager(self, db):
        """Create domain context manager instance."""
        return DomainContextManager(db=db)

    def test_get_statistics_empty(self, manager):
        """Test getting statistics with no contexts."""
        stats = manager.get_domain_statistics()
        assert stats["by_domain_type"] == {}
        assert stats["by_privacy_level"] == {}
        assert stats["by_data_classification"] == {}
        assert stats["current_context"] is None

    def test_get_statistics_with_contexts(self, manager):
        """Test getting statistics with multiple contexts."""
        # Create various contexts
        manager.create_context(
            DomainType.PERSONAL, PrivacyLevel.SENSITIVE, DataClassification.COMMUNICATION
        )
        manager.create_context(
            DomainType.PERSONAL, PrivacyLevel.INTERNAL, DataClassification.CALENDAR
        )
        manager.create_context(
            DomainType.BUSINESS, PrivacyLevel.CONFIDENTIAL, DataClassification.FINANCIAL
        )

        stats = manager.get_domain_statistics()

        assert stats["by_domain_type"]["personal"] == 2
        assert stats["by_domain_type"]["business"] == 1
        assert stats["by_privacy_level"]["sensitive"] == 1
        assert stats["by_privacy_level"]["internal"] == 1
        assert stats["by_privacy_level"]["confidential"] == 1
        assert stats["by_data_classification"]["communication"] == 1
        assert stats["by_data_classification"]["calendar"] == 1
        assert stats["by_data_classification"]["financial"] == 1

    def test_statistics_includes_current_context(self, manager):
        """Test that statistics include current context ID."""
        context_id = manager.create_context(
            DomainType.BUSINESS, PrivacyLevel.INTERNAL, DataClassification.DOCUMENTS
        )
        manager.set_current_context(context_id)

        stats = manager.get_domain_statistics()
        assert stats["current_context"] == context_id
