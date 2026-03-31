"""Health check module for Digital FTE watchers.

Provides health monitoring and status reporting for all watchers.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from .database import Database


class HealthCheck:
    """Health check manager for watchers."""

    def __init__(self, db: Database):
        """Initialize health check manager.

        Args:
            db: Database instance
        """
        self.db = db

    def check_watcher(self, watcher_name: str) -> Dict[str, Any]:
        """Check health status of a specific watcher.

        Args:
            watcher_name: Name of the watcher

        Returns:
            Health status dict
        """
        health = self.db.get_watcher_health(watcher_name)

        if not health:
            return {
                "watcher_name": watcher_name,
                "status": "unknown",
                "message": "Watcher not registered"
            }

        # Check if last check was recent (within 10 minutes)
        last_check = datetime.fromisoformat(health["last_check_timestamp"].replace("Z", ""))
        now = datetime.utcnow()
        time_since_check = (now - last_check).total_seconds()

        if time_since_check > 600:  # 10 minutes
            status = "unhealthy"
            message = f"No health check in {int(time_since_check / 60)} minutes"
        elif health["error_count"] >= 3:
            status = "unhealthy"
            message = f"High error count: {health['error_count']}"
        elif health["error_count"] > 0:
            status = "degraded"
            message = f"Recent errors: {health['error_count']}"
        else:
            status = "healthy"
            message = "Operating normally"

        return {
            "watcher_name": watcher_name,
            "status": status,
            "message": message,
            "last_check": health["last_check_timestamp"],
            "error_count": health["error_count"]
        }

    def check_all(self) -> List[Dict[str, Any]]:
        """Check health status of all watchers.

        Returns:
            List of health status dicts
        """
        watchers = ["gmail", "whatsapp", "linkedin"]
        results = []

        for watcher_name in watchers:
            results.append(self.check_watcher(watcher_name))

        return results

    def get_overall_status(self) -> str:
        """Get overall system health status.

        Returns:
            Overall status (healthy, degraded, unhealthy)
        """
        all_health = self.check_all()

        unhealthy_count = sum(1 for h in all_health if h["status"] == "unhealthy")
        degraded_count = sum(1 for h in all_health if h["status"] == "degraded")

        if unhealthy_count > 0:
            return "unhealthy"
        elif degraded_count > 0:
            return "degraded"
        else:
            return "healthy"

    def report(self) -> str:
        """Generate health check report.

        Returns:
            Formatted health report
        """
        all_health = self.check_all()
        overall = self.get_overall_status()

        lines = [
            "=== Digital FTE Watcher Health Report ===",
            f"Overall Status: {overall.upper()}",
            f"Timestamp: {datetime.utcnow().isoformat()}Z",
            "",
            "Individual Watchers:"
        ]

        for health in all_health:
            status_icon = "[OK]" if health["status"] == "healthy" else "[WARN]" if health["status"] == "degraded" else "[FAIL]"
            lines.append(f"  {status_icon} {health['watcher_name']}: {health['status']} - {health['message']}")

        return "\n".join(lines)
