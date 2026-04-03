#!/usr/bin/env python3
"""
Integration Status Viewer

Displays real-time status of all integrations and their health.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from watchers.shared.database import Database
from datetime import datetime
import json


def format_timestamp(timestamp_str):
    """Format ISO timestamp for display."""
    if not timestamp_str:
        return "Never"
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return timestamp_str


def display_integration_status(db: Database):
    """Display status of all integrations."""
    cursor = db.conn.cursor()
    cursor.execute("""
        SELECT * FROM integration_status
        ORDER BY integration_name
    """)
    
    integrations = cursor.fetchall()
    
    print("\n" + "="*80)
    print("Integration Status Dashboard")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    if not integrations:
        print("\nNo integrations configured.")
        return
    
    for integration in integrations:
        name = integration["integration_name"]
        status = integration["status"]
        cb_state = integration["circuit_breaker_state"]
        
        # Status symbol
        if status == "connected" and cb_state == "CLOSED":
            symbol = "✓"
            color = "GREEN"
        elif cb_state == "OPEN":
            symbol = "✗"
            color = "RED"
        elif cb_state == "HALF_OPEN":
            symbol = "⚠"
            color = "YELLOW"
        else:
            symbol = "○"
            color = "GRAY"
        
        print(f"\n{symbol} {name}")
        print(f"  Status: {status}")
        print(f"  Circuit Breaker: {cb_state}")
        print(f"  Failures: {integration['failure_count']}")
        print(f"  Last Check: {format_timestamp(integration['last_check_time'])}")
        print(f"  Last Success: {format_timestamp(integration['last_success_time'])}")
        print(f"  Last Failure: {format_timestamp(integration['last_failure_time'])}")
        
        if integration["error_message"]:
            print(f"  Last Error: {integration['error_message'][:100]}")


def display_watcher_status(db: Database):
    """Display status of all watchers."""
    cursor = db.conn.cursor()
    cursor.execute("""
        SELECT * FROM watchers
        ORDER BY watcher_name
    """)
    
    watchers = cursor.fetchall()
    
    print("\n" + "="*80)
    print("Watcher Status")
    print("="*80)
    
    if not watchers:
        print("\nNo watchers configured.")
        return
    
    for watcher in watchers:
        name = watcher["watcher_name"]
        health = watcher["health_status"]
        
        symbol = "✓" if health == "healthy" else "✗"
        
        print(f"\n{symbol} {name}")
        print(f"  Health: {health}")
        print(f"  Errors: {watcher['error_count']}")
        print(f"  Last Check: {format_timestamp(watcher['last_check_timestamp'])}")


def display_recent_activity(db: Database):
    """Display recent activity from audit log."""
    cursor = db.conn.cursor()
    cursor.execute("""
        SELECT action_type, component, timestamp
        FROM audit_log
        ORDER BY sequence_number DESC
        LIMIT 10
    """)
    
    activities = cursor.fetchall()
    
    print("\n" + "="*80)
    print("Recent Activity (Last 10 Actions)")
    print("="*80)
    
    if not activities:
        print("\nNo recent activity.")
        return
    
    for activity in activities:
        timestamp = format_timestamp(activity["timestamp"])
        print(f"  {timestamp} - {activity['component']}: {activity['action_type']}")


def display_statistics(db: Database):
    """Display system statistics."""
    cursor = db.conn.cursor()
    
    # Count integrations by status
    cursor.execute("""
        SELECT status, COUNT(*) as count
        FROM integration_status
        GROUP BY status
    """)
    integration_stats = {row["status"]: row["count"] for row in cursor.fetchall()}
    
    # Count circuit breakers by state
    cursor.execute("""
        SELECT circuit_breaker_state, COUNT(*) as count
        FROM integration_status
        GROUP BY circuit_breaker_state
    """)
    cb_stats = {row["circuit_breaker_state"]: row["count"] for row in cursor.fetchall()}
    
    # Count actions by status
    cursor.execute("""
        SELECT status, COUNT(*) as count
        FROM actions
        GROUP BY status
    """)
    action_stats = {row["status"]: row["count"] for row in cursor.fetchall()}
    
    print("\n" + "="*80)
    print("System Statistics")
    print("="*80)
    
    print("\nIntegrations:")
    for status, count in integration_stats.items():
        print(f"  {status}: {count}")
    
    print("\nCircuit Breakers:")
    for state, count in cb_stats.items():
        print(f"  {state}: {count}")
    
    print("\nActions:")
    for status, count in action_stats.items():
        print(f"  {status}: {count}")


def main():
    """Display integration status dashboard."""
    db = Database()
    
    display_integration_status(db)
    display_watcher_status(db)
    display_recent_activity(db)
    display_statistics(db)
    
    print("\n" + "="*80)
    print("\nRefresh: Run this script again to see updated status")
    print("="*80 + "\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
