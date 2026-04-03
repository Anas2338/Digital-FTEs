"""Watcher health check aggregator.

Queries all watchers and reports aggregate health status:
- healthy: All watchers operational
- degraded: Some watchers having issues
- unhealthy: Critical watchers down
"""

import sys
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from watchers.shared.database import Database


class WatcherHealthAggregator:
    """Aggregator for watcher health status."""

    def __init__(self):
        """Initialize health aggregator."""
        self.db = Database()
        self.watchers = ["gmail_watcher", "whatsapp_watcher", "linkedin_watcher"]
        self.integrations = ["odoo", "facebook", "instagram", "twitter"]

        # Health thresholds (minutes since last check)
        self.healthy_threshold = 5
        self.degraded_threshold = 15

    def get_aggregate_status(self) -> Dict[str, Any]:
        """Get aggregate health status for all watchers and integrations.

        Returns:
            Aggregate status dict
        """
        watcher_statuses = []
        healthy_count = 0
        degraded_count = 0
        unhealthy_count = 0

        for watcher_name in self.watchers:
            status = self._get_watcher_status(watcher_name)
            watcher_statuses.append(status)

            if status["health"] == "healthy":
                healthy_count += 1
            elif status["health"] == "degraded":
                degraded_count += 1
            else:
                unhealthy_count += 1

        # Get integration statuses
        integration_statuses = []
        integration_healthy = 0
        integration_degraded = 0
        integration_unhealthy = 0

        for integration_name in self.integrations:
            status = self._get_integration_status(integration_name)
            integration_statuses.append(status)

            if status["health"] == "healthy":
                integration_healthy += 1
            elif status["health"] == "degraded":
                integration_degraded += 1
            else:
                integration_unhealthy += 1

        # Determine overall status
        total_unhealthy = unhealthy_count + integration_unhealthy
        total_degraded = degraded_count + integration_degraded

        if total_unhealthy > 0:
            overall_status = "unhealthy"
        elif total_degraded > 0:
            overall_status = "degraded"
        else:
            overall_status = "healthy"

        return {
            "overall_status": overall_status,
            "watchers": {
                "healthy_count": healthy_count,
                "degraded_count": degraded_count,
                "unhealthy_count": unhealthy_count,
                "total": len(self.watchers),
                "details": watcher_statuses
            },
            "integrations": {
                "healthy_count": integration_healthy,
                "degraded_count": integration_degraded,
                "unhealthy_count": integration_unhealthy,
                "total": len(self.integrations),
                "details": integration_statuses
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

    def _get_watcher_status(self, watcher_name: str) -> Dict[str, Any]:
        """Get status for a specific watcher.

        Args:
            watcher_name: Name of the watcher

        Returns:
            Watcher status dict
        """
        health = self.db.get_watcher_health(watcher_name)

        if not health:
            return {
                "name": watcher_name,
                "health": "unhealthy",
                "status": "unknown",
                "last_check": None,
                "minutes_since_check": None,
                "error": "No health record found",
                "events_processed": 0
            }

        # Calculate time since last check
        try:
            last_check = datetime.fromisoformat(
                health["last_check_timestamp"].replace("Z", "")
            )
            now = datetime.utcnow()
            minutes_since = (now - last_check).total_seconds() / 60

            # Determine health level
            if minutes_since <= self.healthy_threshold:
                health_level = "healthy"
            elif minutes_since <= self.degraded_threshold:
                health_level = "degraded"
            else:
                health_level = "unhealthy"

        except Exception:
            minutes_since = None
            health_level = "unhealthy"

        return {
            "name": watcher_name,
            "health": health_level,
            "status": health.get("status", "unknown"),
            "last_check": health.get("last_check_timestamp"),
            "minutes_since_check": round(minutes_since, 1) if minutes_since else None,
            "error": health.get("error_message"),
            "events_processed": health.get("events_processed", 0)
        }

    def _get_integration_status(self, integration_name: str) -> Dict[str, Any]:
        """Get status for a specific integration (circuit breaker).

        Args:
            integration_name: Name of the integration (odoo, facebook, instagram, twitter)

        Returns:
            Integration status dict
        """
        status = self.db.get_integration_status(integration_name)

        if not status:
            return {
                "name": integration_name,
                "health": "unknown",
                "circuit_state": "unknown",
                "error_rate": 0.0,
                "last_success": None,
                "last_failure": None,
                "recovery_attempt": 0,
                "next_recovery": None
            }

        # Determine health level based on circuit breaker state
        circuit_state = status.get("circuit_breaker_state", "unknown")
        if circuit_state == "closed":
            health_level = "healthy"
        elif circuit_state == "half_open":
            health_level = "degraded"
        elif circuit_state == "open":
            health_level = "unhealthy"
        else:
            health_level = "unknown"

        return {
            "name": integration_name,
            "health": health_level,
            "circuit_state": circuit_state,
            "error_rate": status.get("error_rate", 0.0),
            "error_count": status.get("error_count", 0),
            "success_count": status.get("success_count", 0),
            "last_success": status.get("last_success_at"),
            "last_failure": status.get("last_failure_at"),
            "recovery_attempt": status.get("recovery_attempt", 0),
            "next_recovery": status.get("next_recovery_at")
        }

    def format_status_report(self, aggregate: Dict[str, Any]) -> str:
        """Format aggregate status as human-readable report.

        Args:
            aggregate: Aggregate status dict

        Returns:
            Formatted report string
        """
        report = "Digital FTE Health Status\n"
        report += "=" * 60 + "\n\n"

        # Watchers section
        report += "WATCHERS\n"
        report += "-" * 60 + "\n"

        for watcher in aggregate["watchers"]["details"]:
            # Status icon
            if watcher["health"] == "healthy":
                icon = "[PASS]"
            elif watcher["health"] == "degraded":
                icon = "[WARN]"
            else:
                icon = "[FAIL]"

            report += f"{icon} {watcher['name']}\n"

            if watcher["last_check"]:
                report += f"  Last check: {watcher['last_check']}"
                if watcher["minutes_since_check"] is not None:
                    report += f" ({watcher['minutes_since_check']:.1f} minutes ago)\n"
                else:
                    report += "\n"
            else:
                report += "  Last check: Never\n"

            report += f"  Status: {watcher['status']}\n"

            if watcher["error"]:
                report += f"  Error: {watcher['error']}\n"

            report += f"  Events processed: {watcher['events_processed']}\n"

            # Add action recommendation for unhealthy watchers
            if watcher["health"] == "unhealthy":
                report += f"  Action: Restart watcher with: python watchers/{watcher['name']}/watcher.py\n"

            report += "\n"

        # Integrations section
        report += "INTEGRATIONS (Circuit Breakers)\n"
        report += "-" * 60 + "\n"

        for integration in aggregate["integrations"]["details"]:
            # Status icon
            if integration["health"] == "healthy":
                icon = "[PASS]"
            elif integration["health"] == "degraded":
                icon = "[WARN]"
            elif integration["health"] == "unhealthy":
                icon = "[FAIL]"
            else:
                icon = "[????]"

            report += f"{icon} {integration['name']}\n"
            report += f"  Circuit State: {integration['circuit_state'].upper()}\n"
            report += f"  Error Rate: {integration['error_rate']:.1%}\n"
            report += f"  Errors: {integration['error_count']}, Successes: {integration['success_count']}\n"

            if integration["last_success"]:
                report += f"  Last Success: {integration['last_success']}\n"

            if integration["last_failure"]:
                report += f"  Last Failure: {integration['last_failure']}\n"

            if integration["circuit_state"] == "open":
                report += f"  Recovery Attempt: {integration['recovery_attempt']}\n"
                if integration["next_recovery"]:
                    report += f"  Next Recovery: {integration['next_recovery']}\n"
                report += f"  Action: Wait for automatic recovery or manually reset circuit breaker\n"

            report += "\n"

        # Overall summary
        report += "=" * 60 + "\n"
        report += f"Overall Status: {aggregate['overall_status'].upper()}\n\n"

        report += f"Watchers: "
        report += f"Healthy: {aggregate['watchers']['healthy_count']}/{aggregate['watchers']['total']}, "
        report += f"Degraded: {aggregate['watchers']['degraded_count']}/{aggregate['watchers']['total']}, "
        report += f"Unhealthy: {aggregate['watchers']['unhealthy_count']}/{aggregate['watchers']['total']}\n"

        report += f"Integrations: "
        report += f"Healthy: {aggregate['integrations']['healthy_count']}/{aggregate['integrations']['total']}, "
        report += f"Degraded: {aggregate['integrations']['degraded_count']}/{aggregate['integrations']['total']}, "
        report += f"Unhealthy: {aggregate['integrations']['unhealthy_count']}/{aggregate['integrations']['total']}\n"

        return report

    def get_watcher_uptime(self, watcher_name: str, days: int = 7) -> Dict[str, Any]:
        """Calculate watcher uptime percentage.

        Args:
            watcher_name: Name of the watcher
            days: Number of days to calculate uptime for

        Returns:
            Uptime statistics dict
        """
        # This would query historical health checks from database
        # For now, return placeholder
        return {
            "watcher_name": watcher_name,
            "period_days": days,
            "uptime_percentage": 99.5,
            "total_checks": 2016,  # 7 days * 24 hours * 12 checks/hour
            "successful_checks": 2006,
            "failed_checks": 10
        }

    def check_and_alert(self) -> List[Dict[str, Any]]:
        """Check health and generate alerts for issues.

        Returns:
            List of alert dicts
        """
        aggregate = self.get_aggregate_status()
        alerts = []

        for watcher in aggregate["watchers"]:
            if watcher["health"] == "unhealthy":
                alerts.append({
                    "severity": "critical",
                    "watcher": watcher["name"],
                    "message": f"{watcher['name']} is unhealthy",
                    "details": watcher["error"] or "No recent health check",
                    "action": f"Restart watcher: python watchers/{watcher['name']}/watcher.py",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                })
            elif watcher["health"] == "degraded":
                alerts.append({
                    "severity": "warning",
                    "watcher": watcher["name"],
                    "message": f"{watcher['name']} is degraded",
                    "details": watcher["error"] or "Health check delayed",
                    "action": "Monitor watcher logs for issues",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                })

        return alerts


if __name__ == "__main__":
    # Example usage
    aggregator = WatcherHealthAggregator()

    # Get aggregate status
    status = aggregator.get_aggregate_status()

    # Print formatted report
    report = aggregator.format_status_report(status)
    print(report)

    # Check for alerts
    alerts = aggregator.check_and_alert()
    if alerts:
        print("\nAlerts:")
        for alert in alerts:
            print(f"  [{alert['severity'].upper()}] {alert['message']}")
            print(f"    Details: {alert['details']}")
            print(f"    Action: {alert['action']}")
