"""
Privacy Boundary Enforcer for Digital FTE

Prevents unauthorized cross-domain data access and enforces privacy policies
between personal and business domains.

Features:
- Real-time access control checks
- Privacy policy enforcement
- Data leak prevention
- Audit logging of boundary violations
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from watchers.shared.domain_manager import (
    DomainContextManager,
    DomainType,
    PrivacyLevel,
    DataClassification
)
from watchers.shared.audit_logger import AuditLogger


logger = logging.getLogger(__name__)


class PrivacyViolation(Exception):
    """Raised when a privacy boundary violation is detected."""
    pass


class PrivacyBoundaryEnforcer:
    """
    Enforces privacy boundaries between domains.
    """

    def __init__(
        self,
        domain_manager: Optional[DomainContextManager] = None,
        audit_logger: Optional[AuditLogger] = None
    ):
        """
        Initialize privacy boundary enforcer.

        Args:
            domain_manager: Domain context manager instance
            audit_logger: Audit logger instance
        """
        self.domain_manager = domain_manager or DomainContextManager()
        self.audit_logger = audit_logger or AuditLogger()
        self.violation_count = 0

    def check_access(
        self,
        source_context_id: str,
        target_context_id: str,
        action: str,
        data_type: str
    ) -> Dict[str, Any]:
        """
        Check if access from source to target context is allowed.

        Args:
            source_context_id: Source context ID
            target_context_id: Target context ID
            action: Action being performed (read, write, delete)
            data_type: Type of data being accessed

        Returns:
            Access decision dict

        Raises:
            PrivacyViolation: If access violates privacy boundaries
        """
        # Get contexts
        source = self.domain_manager.get_context(source_context_id)
        target = self.domain_manager.get_context(target_context_id)

        if not source or not target:
            self._log_violation(
                source_context_id,
                target_context_id,
                action,
                "Context not found"
            )
            raise PrivacyViolation("Invalid context")

        # Check cross-domain access
        access_check = self.domain_manager.is_cross_domain_allowed(
            source_context_id,
            target_context_id
        )

        if not access_check["allowed"]:
            self._log_violation(
                source_context_id,
                target_context_id,
                action,
                access_check["reason"]
            )
            raise PrivacyViolation(
                f"Cross-domain access denied: {access_check['reason']}"
            )

        # Check action-specific permissions
        if action == "write" or action == "delete":
            # Write/delete operations require higher privileges
            target_privacy = PrivacyLevel(target["privacy_level"])

            if target_privacy in [PrivacyLevel.CONFIDENTIAL, PrivacyLevel.SENSITIVE]:
                self._log_violation(
                    source_context_id,
                    target_context_id,
                    action,
                    f"Cannot {action} {target_privacy.value} data across domains"
                )
                raise PrivacyViolation(
                    f"Cannot {action} {target_privacy.value} data across domains"
                )

        # Log successful access (if requires logging)
        if access_check.get("requires_logging"):
            self.audit_logger.log_action(
                action_type="access",
                action_name=f"cross_domain_{action}",
                parameters={
                    "source_context": source_context_id,
                    "target_context": target_context_id,
                    "data_type": data_type
                },
                reasoning="Cross-domain access granted with audit logging",
                safety_level=1
            )

        return {
            "allowed": True,
            "source_domain": source["domain_type"],
            "target_domain": target["domain_type"],
            "action": action,
            "requires_logging": access_check.get("requires_logging", False)
        }

    def _log_violation(
        self,
        source_context_id: str,
        target_context_id: str,
        action: str,
        reason: str
    ):
        """
        Log a privacy boundary violation.

        Args:
            source_context_id: Source context ID
            target_context_id: Target context ID
            action: Action that was attempted
            reason: Reason for violation
        """
        self.violation_count += 1

        self.audit_logger.log_action(
            action_type="violation",
            action_name="privacy_boundary_violation",
            parameters={
                "source_context": source_context_id,
                "target_context": target_context_id,
                "action": action,
                "violation_number": self.violation_count
            },
            error_message=reason,
            reasoning="Privacy boundary violation detected and blocked",
            safety_level=3  # High severity
        )

        logger.warning(
            f"Privacy violation #{self.violation_count}: {reason} "
            f"(source={source_context_id}, target={target_context_id}, action={action})"
        )

    def validate_data_transfer(
        self,
        data: Dict[str, Any],
        source_domain: DomainType,
        target_domain: DomainType
    ) -> Dict[str, Any]:
        """
        Validate and sanitize data for cross-domain transfer.

        Args:
            data: Data to transfer
            source_domain: Source domain type
            target_domain: Target domain type

        Returns:
            Validation result with sanitized data

        Raises:
            PrivacyViolation: If data contains sensitive information
        """
        # Check for sensitive fields that should not cross domains
        sensitive_fields = [
            "password", "api_key", "token", "secret", "ssn",
            "credit_card", "bank_account", "private_key"
        ]

        violations = []
        for field in sensitive_fields:
            if field in data:
                violations.append(field)

        if violations:
            self._log_violation(
                source_domain.value,
                target_domain.value,
                "transfer",
                f"Sensitive fields detected: {', '.join(violations)}"
            )
            raise PrivacyViolation(
                f"Cannot transfer sensitive fields across domains: {', '.join(violations)}"
            )

        # Sanitize data (remove internal metadata)
        sanitized = {
            k: v for k, v in data.items()
            if not k.startswith("_") and k not in ["internal_id", "session_token"]
        }

        return {
            "valid": True,
            "sanitized_data": sanitized,
            "removed_fields": list(set(data.keys()) - set(sanitized.keys()))
        }

    def enforce_data_classification(
        self,
        data: Dict[str, Any],
        required_classification: DataClassification
    ) -> bool:
        """
        Enforce data classification requirements.

        Args:
            data: Data to check
            required_classification: Required classification level

        Returns:
            True if data meets classification requirements

        Raises:
            PrivacyViolation: If data does not meet requirements
        """
        # Check if data contains classification metadata
        if "data_classification" not in data:
            logger.warning("Data missing classification metadata")
            return True  # Allow if no classification specified

        data_classification = DataClassification(data["data_classification"])

        # Verify classification matches requirement
        if data_classification != required_classification:
            self._log_violation(
                "unknown",
                "unknown",
                "classify",
                f"Data classification mismatch: expected {required_classification.value}, "
                f"got {data_classification.value}"
            )
            raise PrivacyViolation(
                f"Data classification mismatch: expected {required_classification.value}, "
                f"got {data_classification.value}"
            )

        return True

    def get_violation_report(self) -> Dict[str, Any]:
        """
        Get privacy violation statistics.

        Returns:
            Violation report dict
        """
        # Query audit log for violations
        violations = self.audit_logger.get_audit_logs(
            action_type="violation",
            limit=1000
        )

        # Group by reason
        by_reason = {}
        for violation in violations:
            reason = violation.get("error_message", "Unknown")
            by_reason[reason] = by_reason.get(reason, 0) + 1

        return {
            "total_violations": self.violation_count,
            "logged_violations": len(violations),
            "by_reason": by_reason,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

    def reset_violation_count(self):
        """Reset the violation counter."""
        self.violation_count = 0
        logger.info("Reset privacy violation counter")
