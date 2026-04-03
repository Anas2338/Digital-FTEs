#!/usr/bin/env python3
"""
Audit Log Rotation Script

Implements daily log rotation with 7-year retention policy.
"""

import sys
from pathlib import Path
import shutil
from datetime import datetime, timedelta
import sqlite3

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from watchers.shared.database import Database


def get_log_file_path(date: datetime, vault_path: Path) -> Path:
    """Get log file path for a specific date."""
    log_dir = vault_path / "Audit_Logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"audit_{date.strftime('%Y%m%d')}.db"
    return log_dir / filename


def rotate_logs(vault_path: Path = Path("obsidian-vault")):
    """
    Rotate audit logs to daily files.
    
    Creates a new database file for each day and archives old entries.
    """
    print("\n" + "="*70)
    print("Audit Log Rotation")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    db = Database()
    today = datetime.now().date()
    
    # Get all audit log entries
    cursor = db.conn.cursor()
    cursor.execute("""
        SELECT * FROM audit_log
        ORDER BY sequence_number
    """)
    
    entries = cursor.fetchall()
    
    if not entries:
        print("\nNo audit log entries to rotate.")
        return 0
    
    print(f"\nFound {len(entries)} audit log entries")
    
    # Group entries by date
    entries_by_date = {}
    for entry in entries:
        timestamp = datetime.fromisoformat(entry["timestamp"].replace('Z', '+00:00'))
        date = timestamp.date()
        
        if date not in entries_by_date:
            entries_by_date[date] = []
        entries_by_date[date].append(entry)
    
    print(f"Spanning {len(entries_by_date)} days")
    
    # Create daily log files
    rotated_count = 0
    for date, date_entries in entries_by_date.items():
        if date == today:
            continue  # Don't rotate today's logs
        
        log_file = get_log_file_path(datetime.combine(date, datetime.min.time()), vault_path)
        
        if log_file.exists():
            print(f"  ✓ {date}: Already rotated ({len(date_entries)} entries)")
            continue
        
        # Create daily log database
        conn = sqlite3.connect(str(log_file))
        conn.row_factory = sqlite3.Row
        daily_cursor = conn.cursor()
        
        # Create audit_log table
        daily_cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id TEXT PRIMARY KEY,
                sequence_number INTEGER NOT NULL UNIQUE,
                timestamp TEXT NOT NULL,
                action_type TEXT NOT NULL,
                action_name TEXT NOT NULL,
                parameters TEXT NOT NULL,
                result TEXT,
                error_message TEXT,
                reasoning TEXT,
                user_approval TEXT,
                safety_level INTEGER NOT NULL DEFAULT 0,
                previous_entry_hash TEXT,
                entry_hash TEXT NOT NULL,
                component TEXT,
                details TEXT
            )
        """)
        
        # Insert entries for this date
        for entry in date_entries:
            daily_cursor.execute("""
                INSERT INTO audit_log VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry["id"],
                entry["sequence_number"],
                entry["timestamp"],
                entry["action_type"],
                entry.get("action_name", ""),
                entry["parameters"],
                entry.get("result"),
                entry.get("error_message"),
                entry.get("reasoning"),
                entry.get("user_approval"),
                entry.get("safety_level", 0),
                entry.get("previous_entry_hash"),
                entry["entry_hash"],
                entry.get("component", ""),
                entry.get("details", "")
            ))
        
        conn.commit()
        conn.close()
        
        print(f"  ✓ {date}: Rotated {len(date_entries)} entries to {log_file.name}")
        rotated_count += 1
    
    print(f"\n✓ Rotated {rotated_count} daily log files")
    
    return rotated_count


def cleanup_old_logs(vault_path: Path = Path("obsidian-vault"), retention_days: int = 2555):
    """
    Clean up audit logs older than retention period (default: 7 years = 2555 days).
    """
    print("\n" + "="*70)
    print("Audit Log Cleanup")
    print("="*70)
    
    log_dir = vault_path / "Audit_Logs"
    
    if not log_dir.exists():
        print("\nNo audit logs directory found.")
        return 0
    
    cutoff_date = datetime.now() - timedelta(days=retention_days)
    print(f"\nRetention policy: {retention_days} days (7 years)")
    print(f"Cutoff date: {cutoff_date.strftime('%Y-%m-%d')}")
    
    deleted_count = 0
    archived_size = 0
    
    for log_file in log_dir.glob("audit_*.db"):
        # Extract date from filename
        try:
            date_str = log_file.stem.replace("audit_", "")
            file_date = datetime.strptime(date_str, "%Y%m%d")
            
            if file_date < cutoff_date:
                file_size = log_file.stat().st_size
                log_file.unlink()
                deleted_count += 1
                archived_size += file_size
                print(f"  ✗ Deleted: {log_file.name} ({file_size / 1024:.1f} KB)")
        except (ValueError, OSError) as e:
            print(f"  ⚠ Skipped: {log_file.name} ({e})")
    
    if deleted_count == 0:
        print("\n✓ No logs older than retention period")
    else:
        print(f"\n✓ Deleted {deleted_count} old log files ({archived_size / 1024 / 1024:.2f} MB)")
    
    return deleted_count


def main():
    """Run log rotation and cleanup."""
    vault_path = Path("obsidian-vault")
    
    # Rotate logs
    rotated = rotate_logs(vault_path)
    
    # Cleanup old logs
    deleted = cleanup_old_logs(vault_path, retention_days=2555)
    
    print("\n" + "="*70)
    print("Log Rotation Complete")
    print("="*70)
    print(f"\nRotated: {rotated} daily log files")
    print(f"Deleted: {deleted} old log files")
    print("\nSchedule: Run this script daily via cron/Task Scheduler")
    print("="*70 + "\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
