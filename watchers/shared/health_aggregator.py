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

        # Health thresholds (minutes since last check)
        self.healthy_threshold = 5
        self.degraded_threshold = 15

    def get_aggregate_status(self) -> Dict[str, Any]:
        """Get aggregate health status for all watchers.

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

        # Determine overall status
        if unhealthy_count > 0:
            overall_status = "unhealthy"
        elif degraded_count > 0:
            overall_status = "degraded"
        else:
            overall_status = "healthy"

        return {
            "overall_status": overall_status,
            "healthy_count": healthy_count,
            "degraded_count": degraded_count,
            "unhealthy_count": unhealthy_count,
            "total_watchers": len(self.watchers),
            "watchers": watcher_statuses,
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

    def format_status_report(self, aggregate: Dict[str, Any]) -> str:
        """Format aggregate status as human-readable report.

        Args:
            aggregate: Aggregate status dict

        Returns:
            Formatted report string
        """
        report = "Watcher Health Status\n"
        report += "=" * 60 + "\n\n"

        for watcher in aggregate["watchers"]:
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

        # Overall summary
        report += "-" * 60 + "\n"
        report += f"Overall Status: {aggregate['overall_status'].upper()}\n"
        report += f"Healthy: {aggregate['healthy_count']}/{aggregate['total_watchers']}, "
        report += f"Degraded: {aggregate['degraded_count']}/{aggregate['total_watchers']}, "
        report += f"Unhealthy: {aggregate['unhealthy_count']}/{aggregate['total_watchers']}\n"

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
