"""Watcher installation and startup script for Digital FTE.

Launches all three watchers (Gmail, WhatsApp, LinkedIn) as daemon processes.
"""

import sys
import subprocess
import time
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from watchers.shared.database import Database
from watchers.shared.health_check import HealthCheck


def start_watcher(watcher_name: str, script_path: str, use_nohup: bool = True):
    """Start a watcher as a daemon process.

    Args:
        watcher_name: Name of the watcher (gmail, whatsapp, linkedin)
        script_path: Path to watcher script
        use_nohup: Use nohup for Unix/Linux (default: True)
    """
    print(f"Starting {watcher_name} watcher...")

    script_path = Path(script_path)
    if not script_path.exists():
        print(f"  ✗ Error: Script not found at {script_path}")
        return False

    try:
        if sys.platform == "win32":
            # Windows: Use pythonw for background execution
            subprocess.Popen(
                ["pythonw", str(script_path)],
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        else:
            # Unix/Linux/macOS: Use nohup
            if use_nohup:
                subprocess.Popen(
                    ["nohup", "python", str(script_path)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
            else:
                subprocess.Popen(
                    ["python", str(script_path)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )

        print(f"  ✓ {watcher_name} watcher started")
        return True

    except Exception as e:
        print(f"  ✗ Error starting {watcher_name} watcher: {e}")
        return False


def stop_watchers():
    """Stop all running watchers.

    This is a placeholder. Full implementation would:
    1. Read PID files
    2. Send SIGTERM to each process
    3. Wait for graceful shutdown
    """
    print("Stopping all watchers...")
    print("  (PID tracking not yet implemented)")
    print("  Use 'pkill -f watcher.py' or Task Manager to stop watchers manually")


def check_health():
    """Check health of all watchers."""
    print("\nChecking watcher health...")
    print()

    db = Database()
    health_check = HealthCheck(db)

    report = health_check.report()
    print(report)
    print()

    db.close()


def main():
    """Main entry point for watcher installation."""
    parser = argparse.ArgumentParser(
        description="Install and manage Digital FTE watchers"
    )
    parser.add_argument(
        "--action",
        choices=["start", "stop", "status"],
        default="start",
        help="Action to perform (default: start)"
    )
    parser.add_argument(
        "--watcher",
        choices=["gmail", "whatsapp", "linkedin", "all"],
        default="all",
        help="Which watcher to manage (default: all)"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Digital FTE Watcher Manager")
    print("=" * 60)
    print()

    if args.action == "status":
        check_health()
        return

    if args.action == "stop":
        stop_watchers()
        return

    # Start watchers
    if args.action == "start":
        watchers_to_start = []

        if args.watcher in ("gmail", "all"):
            watchers_to_start.append(("gmail", "watchers/gmail_watcher/watcher.py"))

        if args.watcher in ("whatsapp", "all"):
            watchers_to_start.append(("whatsapp", "watchers/whatsapp_watcher/watcher.py"))

        if args.watcher in ("linkedin", "all"):
            watchers_to_start.append(("linkedin", "watchers/linkedin_watcher/watcher.py"))

        success_count = 0
        for watcher_name, script_path in watchers_to_start:
            if start_watcher(watcher_name, script_path):
                success_count += 1
            time.sleep(1)  # Brief delay between starts

        print()
        print(f"Started {success_count}/{len(watchers_to_start)} watchers")
        print()

        # Wait a moment for watchers to initialize
        print("Waiting for watchers to initialize...")
        time.sleep(3)

        # Check health
        check_health()

        print("=" * 60)
        print("Watchers are running in the background")
        print("Use --action status to check health")
        print("Use --action stop to stop all watchers")
        print("=" * 60)


if __name__ == "__main__":
    main()
