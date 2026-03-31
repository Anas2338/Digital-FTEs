"""Cron manager for Unix/Linux systems.

Manages scheduled tasks using crontab for Unix-like operating systems.
"""

import subprocess
from typing import List, Dict, Any, Optional
from datetime import datetime
import re


class CronManager:
    """Manager for crontab-based scheduled tasks."""

    def __init__(self):
        """Initialize cron manager."""
        self.comment_prefix = "# Digital-FTE:"

    def add_task(self, schedule: str, command: str, task_id: str) -> bool:
        """Add a scheduled task to crontab.

        Args:
            schedule: Cron expression (e.g., "0 9 * * 1")
            command: Command to execute
            task_id: Unique task identifier

        Returns:
            True if added successfully
        """
        try:
            # Get current crontab
            current_crontab = self._get_crontab()

            # Check if task already exists
            if self._task_exists(current_crontab, task_id):
                return False

            # Add new task with comment
            new_entry = f"{self.comment_prefix} {task_id}\n{schedule} {command}\n"
            updated_crontab = current_crontab + new_entry

            # Write updated crontab
            self._set_crontab(updated_crontab)

            return True

        except Exception as e:
            print(f"Error adding cron task: {e}")
            return False

    def remove_task(self, task_id: str) -> bool:
        """Remove a scheduled task from crontab.

        Args:
            task_id: Task identifier

        Returns:
            True if removed successfully
        """
        try:
            current_crontab = self._get_crontab()

            # Find and remove task
            lines = current_crontab.split('\n')
            updated_lines = []
            skip_next = False

            for line in lines:
                if skip_next:
                    skip_next = False
                    continue

                if f"{self.comment_prefix} {task_id}" in line:
                    skip_next = True  # Skip the cron entry line
                    continue

                updated_lines.append(line)

            updated_crontab = '\n'.join(updated_lines)
            self._set_crontab(updated_crontab)

            return True

        except Exception as e:
            print(f"Error removing cron task: {e}")
            return False

    def list_tasks(self) -> List[Dict[str, Any]]:
        """List all Digital FTE scheduled tasks.

        Returns:
            List of task dicts
        """
        try:
            current_crontab = self._get_crontab()
            tasks = []

            lines = current_crontab.split('\n')
            i = 0

            while i < len(lines):
                line = lines[i]

                # Check for Digital FTE comment
                if line.startswith(self.comment_prefix):
                    task_id = line.replace(self.comment_prefix, '').strip()

                    # Next line should be the cron entry
                    if i + 1 < len(lines):
                        cron_line = lines[i + 1]

                        # Parse cron expression and command
                        parts = cron_line.split(None, 5)
                        if len(parts) >= 6:
                            schedule = ' '.join(parts[:5])
                            command = parts[5]

                            tasks.append({
                                "task_id": task_id,
                                "schedule": schedule,
                                "command": command,
                                "platform": "cron"
                            })

                    i += 2  # Skip comment and cron line
                else:
                    i += 1

            return tasks

        except Exception as e:
            print(f"Error listing cron tasks: {e}")
            return []

    def update_task(self, task_id: str, schedule: Optional[str] = None,
                   command: Optional[str] = None) -> bool:
        """Update an existing scheduled task.

        Args:
            task_id: Task identifier
            schedule: New cron expression (optional)
            command: New command (optional)

        Returns:
            True if updated successfully
        """
        try:
            # Get current task
            tasks = self.list_tasks()
            task = next((t for t in tasks if t["task_id"] == task_id), None)

            if not task:
                return False

            # Remove old task
            self.remove_task(task_id)

            # Add updated task
            new_schedule = schedule if schedule else task["schedule"]
            new_command = command if command else task["command"]

            return self.add_task(new_schedule, new_command, task_id)

        except Exception as e:
            print(f"Error updating cron task: {e}")
            return False

    def _get_crontab(self) -> str:
        """Get current crontab contents.

        Returns:
            Crontab contents as string
        """
        try:
            result = subprocess.run(
                ['crontab', '-l'],
                capture_output=True,
                text=True,
                check=False
            )

            # crontab -l returns exit code 1 if no crontab exists
            if result.returncode == 0:
                return result.stdout
            else:
                return ""

        except FileNotFoundError:
            raise RuntimeError("crontab command not found - is cron installed?")

    def _set_crontab(self, content: str):
        """Set crontab contents.

        Args:
            content: New crontab contents
        """
        try:
            process = subprocess.Popen(
                ['crontab', '-'],
                stdin=subprocess.PIPE,
                text=True
            )
            process.communicate(input=content)

            if process.returncode != 0:
                raise RuntimeError("Failed to update crontab")

        except FileNotFoundError:
            raise RuntimeError("crontab command not found - is cron installed?")

    def _task_exists(self, crontab_content: str, task_id: str) -> bool:
        """Check if a task already exists in crontab.

        Args:
            crontab_content: Crontab contents
            task_id: Task identifier

        Returns:
            True if task exists
        """
        return f"{self.comment_prefix} {task_id}" in crontab_content

    def validate_schedule(self, schedule: str) -> bool:
        """Validate cron expression format.

        Args:
            schedule: Cron expression

        Returns:
            True if valid
        """
        # Basic validation: 5 fields separated by spaces
        parts = schedule.split()

        if len(parts) != 5:
            return False

        # Each field should be valid cron syntax
        # (numbers, ranges, lists, wildcards, steps)
        cron_field_pattern = r'^(\*|[0-9]+(-[0-9]+)?(,[0-9]+(-[0-9]+)?)*)(\/[0-9]+)?$'

        for part in parts:
            if not re.match(cron_field_pattern, part):
                return False

        return True


if __name__ == "__main__":
    # Example usage
    manager = CronManager()

    # Example: Add a task
    # manager.add_task("0 9 * * 1", "python /path/to/script.py", "weekly-report")

    # Example: List tasks
    tasks = manager.list_tasks()
    print(f"Scheduled tasks: {len(tasks)}")
    for task in tasks:
        print(f"  {task['task_id']}: {task['schedule']}")

    # Example: Remove a task
    # manager.remove_task("weekly-report")

    print("CronManager initialized.")
