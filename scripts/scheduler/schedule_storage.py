"""Schedule storage manager for Obsidian vault.

Stores scheduled task metadata in obsidian-vault/Schedules/ with YAML frontmatter:
- Cron expression
- Last run timestamp
- Next run timestamp
- Execution history
- Task status
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import yaml
import re

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class ScheduleStorage:
    """Storage manager for scheduled tasks in Obsidian vault."""

    def __init__(self, vault_path: str = "obsidian-vault"):
        """Initialize schedule storage.

        Args:
            vault_path: Path to Obsidian vault
        """
        self.vault_path = Path(vault_path)
        self.schedules_dir = self.vault_path / "Schedules"
        self.schedules_dir.mkdir(parents=True, exist_ok=True)

    def create_schedule(self, task_id: str, schedule: str, command: str,
                       description: Optional[str] = None,
                       priority: int = 5) -> str:
        """Create a new scheduled task.

        Args:
            task_id: Unique task identifier
            schedule: Cron expression
            command: Command to execute
            description: Optional task description
            priority: Task priority (1-10, default: 5)

        Returns:
            Path to created schedule file
        """
        schedule_file = self.schedules_dir / f"{task_id}.md"

        if schedule_file.exists():
            raise ValueError(f"Schedule {task_id} already exists")

        # Create schedule metadata
        frontmatter = {
            "task_id": task_id,
            "schedule": schedule,
            "command": command,
            "description": description or f"Scheduled task: {task_id}",
            "priority": priority,
            "status": "active",
            "created": datetime.utcnow().isoformat() + "Z",
            "last_run": None,
            "next_run": self._calculate_next_run(schedule),
            "execution_count": 0,
            "success_count": 0,
            "failure_count": 0
        }

        # Create content
        content = f"---\n{yaml.dump(frontmatter, default_flow_style=False)}---\n\n"
        content += f"# Scheduled Task: {task_id}\n\n"
        content += f"**Schedule**: `{schedule}`\n\n"
        content += f"**Command**: `{command}`\n\n"
        content += f"## Execution History\n\n"
        content += "No executions yet.\n"

        # Write file
        schedule_file.write_text(content, encoding='utf-8')

        return str(schedule_file)

    def update_schedule(self, task_id: str, **updates) -> bool:
        """Update schedule metadata.

        Args:
            task_id: Task identifier
            **updates: Fields to update

        Returns:
            True if updated successfully
        """
        schedule_file = self.schedules_dir / f"{task_id}.md"

        if not schedule_file.exists():
            return False

        try:
            content = schedule_file.read_text(encoding='utf-8')

            # Parse frontmatter
            match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
            if not match:
                return False

            frontmatter = yaml.safe_load(match.group(1))
            schedule_content = match.group(2)

            # Update fields
            for key, value in updates.items():
                frontmatter[key] = value

            # Rebuild content
            new_content = f"---\n{yaml.dump(frontmatter, default_flow_style=False)}---\n{schedule_content}"

            # Write back
            schedule_file.write_text(new_content, encoding='utf-8')

            return True

        except Exception as e:
            print(f"Error updating schedule: {e}")
            return False

    def record_execution(self, task_id: str, execution_result: Dict[str, Any]) -> bool:
        """Record task execution in schedule file.

        Args:
            task_id: Task identifier
            execution_result: Execution result dict

        Returns:
            True if recorded successfully
        """
        schedule_file = self.schedules_dir / f"{task_id}.md"

        if not schedule_file.exists():
            return False

        try:
            content = schedule_file.read_text(encoding='utf-8')

            # Parse frontmatter
            match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
            if not match:
                return False

            frontmatter = yaml.safe_load(match.group(1))
            schedule_content = match.group(2)

            # Update execution stats
            frontmatter["last_run"] = execution_result["timestamp"]
            frontmatter["next_run"] = self._calculate_next_run(frontmatter["schedule"])
            frontmatter["execution_count"] = frontmatter.get("execution_count", 0) + 1

            if execution_result["success"]:
                frontmatter["success_count"] = frontmatter.get("success_count", 0) + 1
            else:
                frontmatter["failure_count"] = frontmatter.get("failure_count", 0) + 1

            # Add execution to history section
            history_entry = self._format_execution_entry(execution_result)

            # Insert after "## Execution History" header
            if "## Execution History" in schedule_content:
                schedule_content = schedule_content.replace(
                    "## Execution History\n\n",
                    f"## Execution History\n\n{history_entry}\n"
                )
            else:
                schedule_content += f"\n## Execution History\n\n{history_entry}\n"

            # Rebuild content
            new_content = f"---\n{yaml.dump(frontmatter, default_flow_style=False)}---\n{schedule_content}"

            # Write back
            schedule_file.write_text(new_content, encoding='utf-8')

            return True

        except Exception as e:
            print(f"Error recording execution: {e}")
            return False

    def get_schedule(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get schedule metadata.

        Args:
            task_id: Task identifier

        Returns:
            Schedule dict or None if not found
        """
        schedule_file = self.schedules_dir / f"{task_id}.md"

        if not schedule_file.exists():
            return None

        try:
            content = schedule_file.read_text(encoding='utf-8')

            # Parse frontmatter
            match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
            if match:
                frontmatter = yaml.safe_load(match.group(1))
                frontmatter["file_path"] = str(schedule_file)
                return frontmatter

        except Exception as e:
            print(f"Error reading schedule: {e}")

        return None

    def list_schedules(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all scheduled tasks.

        Args:
            status: Optional status filter (active, paused, disabled)

        Returns:
            List of schedule dicts
        """
        schedules = []

        for schedule_file in self.schedules_dir.glob("*.md"):
            try:
                content = schedule_file.read_text(encoding='utf-8')

                # Parse frontmatter
                match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
                if match:
                    frontmatter = yaml.safe_load(match.group(1))

                    # Filter by status if specified
                    if status and frontmatter.get("status") != status:
                        continue

                    frontmatter["file_path"] = str(schedule_file)
                    schedules.append(frontmatter)

            except Exception as e:
                print(f"Error reading schedule {schedule_file}: {e}")
                continue

        return schedules

    def get_due_schedules(self) -> List[Dict[str, Any]]:
        """Get schedules that are due to run.

        Returns:
            List of due schedule dicts
        """
        now = datetime.utcnow()
        due_schedules = []

        for schedule in self.list_schedules(status="active"):
            next_run = schedule.get("next_run")

            if next_run:
                try:
                    next_run_time = datetime.fromisoformat(next_run.replace("Z", ""))

                    # Check if due (within 2-minute window)
                    if next_run_time <= now:
                        due_schedules.append(schedule)

                except Exception:
                    continue

        return due_schedules

    def delete_schedule(self, task_id: str) -> bool:
        """Delete a scheduled task.

        Args:
            task_id: Task identifier

        Returns:
            True if deleted successfully
        """
        schedule_file = self.schedules_dir / f"{task_id}.md"

        if schedule_file.exists():
            schedule_file.unlink()
            return True

        return False

    def _calculate_next_run(self, cron_expression: str) -> str:
        """Calculate next run time from cron expression.

        Args:
            cron_expression: Cron expression

        Returns:
            Next run timestamp (ISO format)
        """
        # Simplified calculation - would use croniter library in production
        # For now, estimate based on common patterns

        parts = cron_expression.split()
        if len(parts) != 5:
            return (datetime.utcnow() + timedelta(hours=1)).isoformat() + "Z"

        minute, hour, day_of_month, month, day_of_week = parts

        # Simple estimation for common patterns
        now = datetime.utcnow()

        if day_of_week != '*':
            # Weekly schedule - estimate next occurrence
            return (now + timedelta(days=7)).isoformat() + "Z"
        elif day_of_month != '*':
            # Monthly schedule
            return (now + timedelta(days=30)).isoformat() + "Z"
        else:
            # Daily schedule
            return (now + timedelta(days=1)).isoformat() + "Z"

    def _format_execution_entry(self, execution_result: Dict[str, Any]) -> str:
        """Format execution result as markdown entry.

        Args:
            execution_result: Execution result dict

        Returns:
            Markdown formatted entry
        """
        timestamp = execution_result.get("timestamp", "Unknown")
        success = execution_result.get("success", False)
        duration = execution_result.get("duration_seconds", 0)
        attempts = execution_result.get("attempt", execution_result.get("attempts", 1))

        status_icon = "[PASS]" if success else "[FAIL]"

        entry = f"### {timestamp}\n\n"
        entry += f"**Status**: {status_icon}\n"
        entry += f"**Duration**: {duration:.2f}s\n"
        entry += f"**Attempts**: {attempts}\n"

        if success:
            output = execution_result.get("output", "")
            if output:
                entry += f"**Output**: {output[:200]}...\n" if len(output) > 200 else f"**Output**: {output}\n"
        else:
            error = execution_result.get("error", "Unknown error")
            entry += f"**Error**: {error}\n"

        return entry


if __name__ == "__main__":
    # Example usage
    storage = ScheduleStorage()

    # Example: Create schedule
    # storage.create_schedule(
    #     task_id="weekly-report",
    #     schedule="0 9 * * 1",
    #     command="python scripts/generate_report.py",
    #     description="Generate weekly report every Monday at 9am"
    # )

    # Example: List schedules
    schedules = storage.list_schedules()
    print(f"Scheduled tasks: {len(schedules)}")
    for schedule in schedules:
        print(f"  {schedule['task_id']}: {schedule['schedule']}")

    # Example: Get due schedules
    due = storage.get_due_schedules()
    print(f"Due tasks: {len(due)}")

    print("ScheduleStorage initialized.")
