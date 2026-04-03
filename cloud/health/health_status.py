"""
Health Status Entity for Platinum Tier

Represents the health status of a monitored service or component.

Based on spec.md FR-031 through FR-034 and User Story 5.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Dict


class HealthStatus(Enum):
    """Health status values."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ServiceType(Enum):
    """Types of services being monitored."""
    CLOUD_AGENT = "cloud_agent"
    LOCAL_AGENT = "local_agent"
    VAULT_SYNC = "vault_sync"
    ODOO = "odoo"
    EMAIL_WATCHER = "email_watcher"
    SOCIAL_WATCHER = "social_watcher"
    ODOO_WATCHER = "odoo_watcher"


@dataclass
class HealthCheck:
    """
    Health check result for a service.

    Attributes:
        service_type: Type of service being checked
        status: Current health status
        checked_at: Timestamp of check
        response_time_seconds: Response time (if applicable)
        error_message: Error message if unhealthy
        metadata: Additional check-specific data
    """
    service_type: ServiceType
    status: HealthStatus
    checked_at: datetime
    response_time_seconds: Optional[float] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "service_type": self.service_type.value,
            "status": self.status.value,
            "checked_at": self.checked_at.isoformat(),
            "response_time_seconds": self.response_time_seconds,
            "error_message": self.error_message,
            "metadata": self.metadata or {}
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "HealthCheck":
        """Create from dictionary."""
        return cls(
            service_type=ServiceType(data["service_type"]),
            status=HealthStatus(data["status"]),
            checked_at=datetime.fromisoformat(data["checked_at"]),
            response_time_seconds=data.get("response_time_seconds"),
            error_message=data.get("error_message"),
            metadata=data.get("metadata")
        )

    def is_healthy(self) -> bool:
        """Check if status is healthy."""
        return self.status == HealthStatus.HEALTHY

    def is_critical(self) -> bool:
        """Check if status requires immediate attention."""
        return self.status == HealthStatus.UNHEALTHY


@dataclass
class AlertThreshold:
    """
    Alert threshold configuration for a service.

    Attributes:
        service_type: Type of service
        check_interval_seconds: How often to check (default 300 = 5 minutes per FR-031)
        alert_after_failures: Number of consecutive failures before alerting (default 2 per FR-032)
        restart_after_failures: Number of failures before auto-restart (default 2 per FR-033)
        max_restart_attempts: Maximum restart attempts before manual intervention (default 3 per FR-033)
        response_time_threshold_seconds: Max acceptable response time
    """
    service_type: ServiceType
    check_interval_seconds: int = 300  # 5 minutes (FR-031)
    alert_after_failures: int = 2  # Alert after 2 failures (FR-032: 2-minute alert)
    restart_after_failures: int = 2  # Restart after 2 failures (FR-033)
    max_restart_attempts: int = 3  # Max 3 restart attempts (FR-033)
    response_time_threshold_seconds: float = 5.0  # 5 seconds max response time

    def should_alert(self, consecutive_failures: int) -> bool:
        """Check if alert should be sent."""
        return consecutive_failures >= self.alert_after_failures

    def should_restart(self, consecutive_failures: int) -> bool:
        """Check if service should be restarted."""
        return consecutive_failures >= self.restart_after_failures

    def has_exceeded_restart_limit(self, restart_count: int) -> bool:
        """Check if restart limit exceeded (requires manual intervention)."""
        return restart_count >= self.max_restart_attempts
