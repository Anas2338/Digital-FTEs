"""Missed schedule handler for catching up on missed executions.

Checks for schedules that should have run while the system was offline
and executes them if within the 24-hour catch-up window.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.scheduler.schedule_storage import ScheduleStorage
from scripts.scheduler.task_executor import TaskExecutor


class MissedScheduleHandler:
    """Handler for missed schedule execution."""

    def __init__(self, catchup_window_hours: int = 24):
        """Initialize missed schedule handler.

        Args:
            catchup_window_hours: Hours within which to catch up missed schedules
        """
        self.catchup_window_hours = catchup_window_hours
        self.storage = ScheduleStorage()
        self.executor = TaskExecutor()

    def check_and_execute_missed(self) -> Dict[str, Any]:
        """Check for missed schedules and execute them.

        Returns:
            Summary dict with executed and skipped tasks
        """
        now = datetime.utcnow()
        catchup_cutoff = now - timedelta(hours=self.catchup_window_hours)

        executed = []
        skipped = []

        # Get all active schedules
        schedules = self.storage.list_schedules(status="active")

        for schedule in schedules:
            task_id = schedule["task_id"]
            last_run = schedule.get("last_run")
            next_run = schedule.get("next_run")

            # Skip if no next_run defined
            if not next_run:
                continue

            try:
                next_run_time = datetime.fromisoformat(next_run.replace("Z", ""))

                # Check if schedule was missed
                if next_run_time < now:
                    # Schedule is overdue

                    # Check if within catchup window
                    if next_run_time >= catchup_cutoff:
                        # Within catchup window - execute
                        print(f"Executing missed schedule: {task_id} "
                              f"(was due at {next_run_time.isoformat()})")

                        result = self.executor.execute(
                            task_id=task_id,
                            command=schedule["command"]
                        )

                        # Record execution
                        self.storage.record_execution(task_id, result)

                        executed.append({
                            "task_id": task_id,
                            "scheduled_time": next_run,
                            "executed_time": datetime.utcnow().isoformat() + "Z",
                            "success": result["success"]
                        })

                    else:
                        # Outside catchup window - skip
                        print(f"Skipping missed schedule: {task_id} "
                              f"(was due at {next_run_time.isoformat()}, "
                              f"outside {self.catchup_window_hours}h window)")

                        # Update next_run to prevent repeated skips
                        self.storage.update_schedule(
                            task_id,
                            next_run=self.storage._calculate_next_run(schedule["schedule"])
                        )

                        skipped.append({
                            "task_id": task_id,
                            "scheduled_time": next_run,
                            "reason": "outside_catchup_window"
                        })

            except Exception as e:
                print(f"Error processing missed schedule {task_id}: {e}")
                continue

        return {
            "executed_count": len(executed),
            "skipped_count": len(skipped),
            "executed": executed,
            "skipped": skipped,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

    def get_missed_schedules(self) -> List[Dict[str, Any]]:
        """Get list of missed schedules without executing them.

        Returns:
            List of missed schedule dicts
        """
        now = datetime.utcnow()
        catchup_cutoff = now - timedelta(hours=self.catchup_window_hours)

        missed = []

        schedules = self.storage.list_schedules(status="active")

        for schedule in schedules:
            next_run = schedule.get("next_run")

            if not next_run:
                continue

            try:
                next_run_time = datetime.fromisoformat(next_run.replace("Z", ""))

                if next_run_time < now:
                    within_window = next_run_time >= catchup_cutoff

                    missed.append({
                        "task_id": schedule["task_id"],
                        "scheduled_time": next_run,
                        "hours_overdue": (now - next_run_time).total_seconds() / 3600,
                        "within_catchup_window": within_window,
                        "command": schedule["command"]
                    })

            except Exception:
                continue

        return missed


if __name__ == "__main__":
    # Example usage
    handler = MissedScheduleHandler()

    # Check for missed schedules
    missed = handler.get_missed_schedules()
    print(f"Missed schedules: {len(missed)}")
    for schedule in missed:
        print(f"  {schedule['task_id']}: {schedule['hours_overdue']:.1f}h overdue "
              f"(catchup: {schedule['within_catchup_window']})")

    # Execute missed schedules
    # result = handler.check_and_execute_missed()
    # print(f"Executed: {result['executed_count']}, Skipped: {result['skipped_count']}")

    print("MissedScheduleHandler initialized.")
