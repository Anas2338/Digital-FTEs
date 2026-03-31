"""Conflict resolver for handling multiple tasks scheduled at the same time.

When multiple tasks are scheduled for the same time, executes them sequentially
in priority order (1 = highest priority, 10 = lowest).
"""

import sys
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.scheduler.schedule_storage import ScheduleStorage
from scripts.scheduler.task_executor import TaskExecutor


class ConflictResolver:
    """Resolver for scheduling conflicts."""

    def __init__(self):
        """Initialize conflict resolver."""
        self.storage = ScheduleStorage()
        self.executor = TaskExecutor()

    def resolve_and_execute(self, schedules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Resolve conflicts and execute tasks in priority order.

        Args:
            schedules: List of schedule dicts that are due at the same time

        Returns:
            Execution summary dict
        """
        if not schedules:
            return {
                "executed_count": 0,
                "results": []
            }

        # Sort by priority (lower number = higher priority), then by task_id
        sorted_schedules = sorted(
            schedules,
            key=lambda s: (s.get("priority", 5), s.get("task_id", ""))
        )

        results = []

        print(f"Resolving conflict: {len(schedules)} tasks scheduled for same time")
        print(f"Execution order (by priority):")
        for i, schedule in enumerate(sorted_schedules, 1):
            print(f"  {i}. {schedule['task_id']} (priority: {schedule.get('priority', 5)})")

        # Execute sequentially
        for schedule in sorted_schedules:
            task_id = schedule["task_id"]
            command = schedule["command"]

            print(f"\nExecuting: {task_id}")

            # Execute task
            result = self.executor.execute(
                task_id=task_id,
                command=command
            )

            # Record execution
            self.storage.record_execution(task_id, result)

            results.append({
                "task_id": task_id,
                "priority": schedule.get("priority", 5),
                "success": result["success"],
                "duration_seconds": result["duration_seconds"],
                "timestamp": result["timestamp"]
            })

            # Log result
            status = "[PASS]" if result["success"] else "[FAIL]"
            print(f"{status} {task_id} completed in {result['duration_seconds']:.2f}s")

        return {
            "executed_count": len(results),
            "results": results,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

    def detect_conflicts(self, time_window_minutes: int = 5) -> List[List[Dict[str, Any]]]:
        """Detect scheduling conflicts within a time window.

        Args:
            time_window_minutes: Time window to check for conflicts (default: 5)

        Returns:
            List of conflict groups (each group is a list of conflicting schedules)
        """
        schedules = self.storage.list_schedules(status="active")

        # Group schedules by next_run time (rounded to minute)
        time_groups = {}

        for schedule in schedules:
            next_run = schedule.get("next_run")
            if not next_run:
                continue

            try:
                next_run_time = datetime.fromisoformat(next_run.replace("Z", ""))
                # Round to minute
                time_key = next_run_time.strftime("%Y-%m-%d %H:%M")

                if time_key not in time_groups:
                    time_groups[time_key] = []

                time_groups[time_key].append(schedule)

            except Exception:
                continue

        # Find groups with conflicts (more than 1 task)
        conflicts = [group for group in time_groups.values() if len(group) > 1]

        return conflicts

    def get_execution_order(self, schedules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get execution order for a list of schedules.

        Args:
            schedules: List of schedule dicts

        Returns:
            Sorted list of schedules in execution order
        """
        return sorted(
            schedules,
            key=lambda s: (s.get("priority", 5), s.get("task_id", ""))
        )


if __name__ == "__main__":
    # Example usage
    resolver = ConflictResolver()

    # Detect conflicts
    conflicts = resolver.detect_conflicts()
    print(f"Scheduling conflicts detected: {len(conflicts)}")

    for i, conflict_group in enumerate(conflicts, 1):
        print(f"\nConflict {i}: {len(conflict_group)} tasks at same time")
        execution_order = resolver.get_execution_order(conflict_group)

        for j, schedule in enumerate(execution_order, 1):
            print(f"  {j}. {schedule['task_id']} (priority: {schedule.get('priority', 5)})")

    # Example: Resolve and execute conflicts
    # if conflicts:
    #     result = resolver.resolve_and_execute(conflicts[0])
    #     print(f"\nExecuted {result['executed_count']} tasks")

    print("\nConflictResolver initialized.")
