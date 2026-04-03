#!/usr/bin/env python3
"""
Daily Health Check Script

Verifies all watchers are running, integrations are healthy,
and no circuit breakers are open. Generates a health report.

Usage: python scripts/daily_health_check.py
"""

import sys
from pathlib import Path
from datetime import datetime
import sqlite3

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from watchers.shared.database import Database


def check_watchers_health(db: Database) -> dict:
    """Check health status of all watchers."""
    cursor = db.conn.cursor()
    cursor.execute("SELECT * FROM watchers")
    watchers = cursor.fetchall()

    results = {
        "total": len(watchers),
        "healthy": 0,
        "degraded": 0,
        "unhealthy": 0,
        "details": []
    }

    for watcher in watchers:
        status = watcher["health_status"]
        if status == "healthy":
            results["healthy"] += 1
        elif status == "degraded":
            results["degraded"] += 1
        else:
            results["unhealthy"] += 1

        results["details"].append({
            "name": watcher["watcher_name"],
            "status": status,
            "last_check": watcher["last_check_timestamp"],
            "error_count": watcher["error_count"]
        })

    return results


def check_integration_status(db: Database) -> dict:
    """Check status of all integrations and circuit breakers."""
    cursor = db.conn.cursor()
    cursor.execute("SELECT * FROM integration_status")
    integrations = cursor.fetchall()

    results = {
        "total": len(integrations),
        "healthy": 0,
        "circuit_breakers_open": 0,
        "details": []
    }

    for integration in integrations:
        circuit_state = integration["circuit_breaker_state"]
        is_open = circuit_state == "open"

        if is_open:
            results["circuit_breakers_open"] += 1
        else:
            results["healthy"] += 1

        results["details"].append({
            "name": integration["integration_name"],
            "status": integration["status"],
            "circuit_breaker": circuit_state,
            "error_rate": integration["error_rate"],
            "last_success": integration["last_success_at"],
            "last_failure": integration["last_failure_at"]
        })

    return results


def check_pending_actions(db: Database) -> dict:
    """Check for pending actions in approval queue."""
    cursor = db.conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM actions WHERE status = 'pending_approval'")
    pending_count = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) as count FROM action_queue WHERE status = 'pending'")
    queued_count = cursor.fetchone()["count"]

    return {
        "pending_approval": pending_count,
        "queued_for_retry": queued_count
    }


def generate_health_report(watchers: dict, integrations: dict, actions: dict) -> str:
    """Generate health report in Markdown format."""
    now = datetime.now()

    lines = [
        f"# Digital FTE Health Check Report",
        f"",
        f"**Generated**: {now.strftime('%Y-%m-%d %H:%M:%S')}",
        f"",
        f"## Overall Status",
        f"",
    ]

    # Determine overall status
    if (watchers["unhealthy"] > 0 or integrations["circuit_breakers_open"] > 0):
        overall = "⚠️ **DEGRADED**"
    elif (watchers["degraded"] > 0):
        overall = "⚠️ **WARNING**"
    else:
        overall = "✅ **HEALTHY**"

    lines.append(f"{overall}")
    lines.append("")

    # Watchers section
    lines.append("## Watchers")
    lines.append("")
    lines.append(f"- **Total**: {watchers['total']}")
    lines.append(f"- **Healthy**: {watchers['healthy']}")
    lines.append(f"- **Degraded**: {watchers['degraded']}")
    lines.append(f"- **Unhealthy**: {watchers['unhealthy']}")
    lines.append("")

    if watchers["details"]:
        lines.append("### Watcher Details")
        lines.append("")
        for watcher in watchers["details"]:
            status_icon = "✅" if watcher["status"] == "healthy" else "⚠️"
            lines.append(f"- {status_icon} **{watcher['name']}**: {watcher['status']} (errors: {watcher['error_count']})")
        lines.append("")

    # Integrations section
    lines.append("## Integrations")
    lines.append("")
    lines.append(f"- **Total**: {integrations['total']}")
    lines.append(f"- **Healthy**: {integrations['healthy']}")
    lines.append(f"- **Circuit Breakers Open**: {integrations['circuit_breakers_open']}")
    lines.append("")

    if integrations["details"]:
        lines.append("### Integration Details")
        lines.append("")
        for integration in integrations["details"]:
            status_icon = "✅" if integration["circuit_breaker"] == "closed" else "⚠️"
            lines.append(f"- {status_icon} **{integration['name']}**: {integration['circuit_breaker']} (error rate: {integration['error_rate']:.1%})")
        lines.append("")

    # Actions section
    lines.append("## Pending Actions")
    lines.append("")
    lines.append(f"- **Awaiting Approval**: {actions['pending_approval']}")
    lines.append(f"- **Queued for Retry**: {actions['queued_for_retry']}")
    lines.append("")

    # Recommendations
    if integrations["circuit_breakers_open"] > 0:
        lines.append("## ⚠️ Recommendations")
        lines.append("")
        lines.append("- **Circuit breakers are open**: Check integration connectivity and logs")
        lines.append("- Run `python watchers/shared/reset_circuit_breaker.py <integration_name>` to manually reset")
        lines.append("")

    if actions["pending_approval"] > 0:
        lines.append("## 📋 Action Required")
        lines.append("")
        lines.append(f"- **{actions['pending_approval']} action(s)** awaiting approval in `obsidian-vault/Approvals/`")
        lines.append("")

    lines.append("---")
    lines.append("*Generated by Digital FTE Health Check*")

    return "\n".join(lines)


def main():
    """Main entry point."""
    print("Running Digital FTE health check...")

    # Initialize database
    db = Database()

    # Run health checks
    print("Checking watchers...")
    watchers = check_watchers_health(db)

    print("Checking integrations...")
    integrations = check_integration_status(db)

    print("Checking pending actions...")
    actions = check_pending_actions(db)

    # Generate report
    report = generate_health_report(watchers, integrations, actions)

    # Save report
    report_dir = Path("obsidian-vault/Reports")
    report_dir.mkdir(parents=True, exist_ok=True)

    report_file = report_dir / f"health-check-{datetime.now().strftime('%Y-%m-%d')}.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n✅ Health check complete!")
    print(f"📄 Report saved to: {report_file}")

    # Print summary
    print("\n" + "="*60)
    print(report)
    print("="*60)

    # Exit with error code if unhealthy
    if watchers["unhealthy"] > 0 or integrations["circuit_breakers_open"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
