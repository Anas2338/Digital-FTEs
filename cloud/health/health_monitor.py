"""
Health Monitor for Platinum Tier

Orchestrates health checks for all monitored services.
Tracks consecutive failures and triggers alerts/restarts.

Based on spec.md FR-031 through FR-034 and User Story 5.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from cloud.health.health_status import (
    HealthCheck,
    HealthStatus,
    ServiceType,
    AlertThreshold
)


class HealthMonitor:
    """
    Central health monitoring coordinator.

    Responsibilities:
    - Schedule health checks for all services
    - Track consecutive failures per service
    - Trigger alerts when thresholds exceeded
    - Trigger automatic restarts when appropriate
    - Maintain health check history
    """

    def __init__(self, vault_path: Path):
        """
        Initialize health monitor.

        Args:
            vault_path: Path to Obsidian vault for logging
        """
        self.vault_path = Path(vault_path)
        self.logger = logging.getLogger("health_monitor")

        # Track consecutive failures per service
        self.consecutive_failures: Dict[ServiceType, int] = {}
        self.restart_counts: Dict[ServiceType, int] = {}
        self.last_check_time: Dict[ServiceType, datetime] = {}

        # Alert thresholds per service (FR-031, FR-032, FR-033)
        self.thresholds: Dict[ServiceType, AlertThreshold] = {
            ServiceType.CLOUD_AGENT: AlertThreshold(
                service_type=ServiceType.CLOUD_AGENT,
                check_interval_seconds=300,  # 5 minutes
                alert_after_failures=2,
                restart_after_failures=2,
                max_restart_attempts=3
            ),
            ServiceType.VAULT_SYNC: AlertThreshold(
                service_type=ServiceType.VAULT_SYNC,
                check_interval_seconds=60,  # 1 minute (sync is critical)
                alert_after_failures=5,  # Alert after 5 minutes lag
                restart_after_failures=60,  # Restart after 1 hour lag
                max_restart_attempts=3
            ),
            ServiceType.ODOO: AlertThreshold(
                service_type=ServiceType.ODOO,
                check_interval_seconds=300,  # 5 minutes
                alert_after_failures=2,
                restart_after_failures=2,
                max_restart_attempts=3
            ),
            ServiceType.EMAIL_WATCHER: AlertThreshold(
                service_type=ServiceType.EMAIL_WATCHER,
                check_interval_seconds=300,
                alert_after_failures=3,  # Less critical than core services
                restart_after_failures=3,
                max_restart_attempts=3
            ),
            ServiceType.SOCIAL_WATCHER: AlertThreshold(
                service_type=ServiceType.SOCIAL_WATCHER,
                check_interval_seconds=300,
                alert_after_failures=3,
                restart_after_failures=3,
                max_restart_attempts=3
            ),
            ServiceType.ODOO_WATCHER: AlertThreshold(
                service_type=ServiceType.ODOO_WATCHER,
                check_interval_seconds=300,
                alert_after_failures=3,
                restart_after_failures=3,
                max_restart_attempts=3
            )
        }

    def record_check(self, check: HealthCheck) -> None:
        """
        Record a health check result and update failure tracking.

        Args:
            check: Health check result
        """
        service = check.service_type
        self.last_check_time[service] = check.checked_at

        if check.is_healthy():
            # Reset failure count on success
            if service in self.consecutive_failures:
                prev_failures = self.consecutive_failures[service]
                if prev_failures > 0:
                    self.logger.info(
                        f"{service.value} recovered after {prev_failures} failures"
                    )
            self.consecutive_failures[service] = 0
        else:
            # Increment failure count
            self.consecutive_failures[service] = \
                self.consecutive_failures.get(service, 0) + 1

            failures = self.consecutive_failures[service]
            self.logger.warning(
                f"{service.value} health check failed "
                f"(consecutive failures: {failures})"
            )

    def should_alert(self, service_type: ServiceType) -> bool:
        """
        Check if alert should be sent for a service.

        Args:
            service_type: Service to check

        Returns:
            True if alert threshold exceeded
        """
        threshold = self.thresholds.get(service_type)
        if not threshold:
            return False

        failures = self.consecutive_failures.get(service_type, 0)
        return threshold.should_alert(failures)

    def should_restart(self, service_type: ServiceType) -> bool:
        """
        Check if service should be restarted.

        Args:
            service_type: Service to check

        Returns:
            True if restart threshold exceeded and restart limit not reached
        """
        threshold = self.thresholds.get(service_type)
        if not threshold:
            return False

        failures = self.consecutive_failures.get(service_type, 0)
        restart_count = self.restart_counts.get(service_type, 0)

        return (
            threshold.should_restart(failures) and
            not threshold.has_exceeded_restart_limit(restart_count)
        )

    def requires_manual_intervention(self, service_type: ServiceType) -> bool:
        """
        Check if service requires manual intervention.

        Args:
            service_type: Service to check

        Returns:
            True if restart limit exceeded (FR-033: manual intervention required)
        """
        threshold = self.thresholds.get(service_type)
        if not threshold:
            return False

        restart_count = self.restart_counts.get(service_type, 0)
        return threshold.has_exceeded_restart_limit(restart_count)

    def record_restart(self, service_type: ServiceType) -> None:
        """
        Record that a service was restarted.

        Args:
            service_type: Service that was restarted
        """
        self.restart_counts[service_type] = \
            self.restart_counts.get(service_type, 0) + 1

        restart_count = self.restart_counts[service_type]
        self.logger.info(
            f"Restarted {service_type.value} "
            f"(restart count: {restart_count})"
        )

    def reset_restart_count(self, service_type: ServiceType) -> None:
        """
        Reset restart count after manual intervention.

        Args:
            service_type: Service to reset
        """
        if service_type in self.restart_counts:
            self.restart_counts[service_type] = 0
            self.logger.info(f"Reset restart count for {service_type.value}")

    def get_service_status(self, service_type: ServiceType) -> Dict:
        """
        Get current status summary for a service.

        Args:
            service_type: Service to check

        Returns:
            Status summary dict
        """
        return {
            "service": service_type.value,
            "consecutive_failures": self.consecutive_failures.get(service_type, 0),
            "restart_count": self.restart_counts.get(service_type, 0),
            "last_check": self.last_check_time.get(service_type),
            "requires_manual_intervention": self.requires_manual_intervention(service_type),
            "should_alert": self.should_alert(service_type),
            "should_restart": self.should_restart(service_type)
        }

    def get_all_service_statuses(self) -> List[Dict]:
        """
        Get status summary for all monitored services.

        Returns:
            List of status summaries
        """
        return [
            self.get_service_status(service_type)
            for service_type in ServiceType
        ]
