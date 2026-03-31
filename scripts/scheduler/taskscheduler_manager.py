"""Task Scheduler manager for Windows systems.

Manages scheduled tasks using Windows Task Scheduler XML import/export.
"""

import subprocess
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from datetime import datetime
import tempfile
import os


class TaskSchedulerManager:
    """Manager for Windows Task Scheduler tasks."""

    def __init__(self, task_folder: str = "\\Digital-FTE"):
        """Initialize Task Scheduler manager.

        Args:
            task_folder: Task folder path in Task Scheduler
        """
        self.task_folder = task_folder
        self._ensure_folder_exists()

    def _ensure_folder_exists(self):
        """Ensure the Digital-FTE task folder exists."""
        try:
            # Check if folder exists
            result = subprocess.run(
                ['schtasks', '/Query', '/FO', 'LIST', '/TN', self.task_folder],
                capture_output=True,
                text=True,
                check=False
            )

            # If folder doesn't exist, create it (requires admin)
            if result.returncode != 0:
                print(f"Note: Task folder {self.task_folder} will be created on first task add")

        except Exception as e:
            print(f"Warning: Could not check task folder: {e}")

    def add_task(self, schedule: str, command: str, task_id: str) -> bool:
        """Add a scheduled task to Task Scheduler.

        Args:
            schedule: Cron expression (converted to Windows schedule)
            command: Command to execute
            task_id: Unique task identifier

        Returns:
            True if added successfully
        """
        try:
            # Convert cron to Windows schedule
            trigger_xml = self._cron_to_trigger_xml(schedule)

            # Generate task XML
            task_xml = self._generate_task_xml(command, trigger_xml, task_id)

            # Write XML to temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
                f.write(task_xml)
                xml_path = f.name

            try:
                # Import task using schtasks
                task_name = f"{self.task_folder}\\{task_id}"

                result = subprocess.run(
                    ['schtasks', '/Create', '/TN', task_name, '/XML', xml_path, '/F'],
                    capture_output=True,
                    text=True,
                    check=False
                )

                if result.returncode == 0:
                    return True
                else:
                    print(f"Error creating task: {result.stderr}")
                    return False

            finally:
                # Clean up temp file
                os.unlink(xml_path)

        except Exception as e:
            print(f"Error adding Task Scheduler task: {e}")
            return False

    def remove_task(self, task_id: str) -> bool:
        """Remove a scheduled task from Task Scheduler.

        Args:
            task_id: Task identifier

        Returns:
            True if removed successfully
        """
        try:
            task_name = f"{self.task_folder}\\{task_id}"

            result = subprocess.run(
                ['schtasks', '/Delete', '/TN', task_name, '/F'],
                capture_output=True,
                text=True,
                check=False
            )

            return result.returncode == 0

        except Exception as e:
            print(f"Error removing Task Scheduler task: {e}")
            return False

    def list_tasks(self) -> List[Dict[str, Any]]:
        """List all Digital FTE scheduled tasks.

        Returns:
            List of task dicts
        """
        try:
            result = subprocess.run(
                ['schtasks', '/Query', '/FO', 'CSV', '/V', '/TN', f"{self.task_folder}\\*"],
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode != 0:
                return []

            tasks = []
            lines = result.stdout.strip().split('\n')

            # Skip header
            for line in lines[1:]:
                # Parse CSV (basic parsing, may need improvement for complex cases)
                parts = line.split(',')

                if len(parts) >= 2:
                    task_name = parts[0].strip('"')
                    task_id = task_name.replace(f"{self.task_folder}\\", '')

                    tasks.append({
                        "task_id": task_id,
                        "schedule": "See Task Scheduler",  # Would need XML export to get schedule
                        "command": "See Task Scheduler",
                        "platform": "taskscheduler"
                    })

            return tasks

        except Exception as e:
            print(f"Error listing Task Scheduler tasks: {e}")
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
        # For Task Scheduler, easiest approach is remove and re-add
        if schedule or command:
            # Would need to export XML, modify, and re-import
            # For now, just return False (not implemented)
            print("Task update not fully implemented for Task Scheduler")
            return False

        return False

    def _cron_to_trigger_xml(self, cron_expression: str) -> str:
        """Convert cron expression to Windows Task Scheduler trigger XML.

        Args:
            cron_expression: Cron expression (e.g., "0 9 * * 1")

        Returns:
            Trigger XML fragment
        """
        parts = cron_expression.split()

        if len(parts) != 5:
            raise ValueError("Invalid cron expression")

        minute, hour, day_of_month, month, day_of_week = parts

        # Simple conversion for common patterns
        # Full cron-to-Windows conversion is complex, this handles basic cases

        if day_of_week != '*':
            # Weekly schedule
            days_map = {'0': 'Sunday', '1': 'Monday', '2': 'Tuesday',
                       '3': 'Wednesday', '4': 'Thursday', '5': 'Friday', '6': 'Saturday'}
            day_name = days_map.get(day_of_week, 'Monday')

            return f"""
      <CalendarTrigger>
        <StartBoundary>2026-01-01T{hour.zfill(2)}:{minute.zfill(2)}:00</StartBoundary>
        <ScheduleByWeek>
          <DaysOfWeek>
            <{day_name} />
          </DaysOfWeek>
          <WeeksInterval>1</WeeksInterval>
        </ScheduleByWeek>
      </CalendarTrigger>
"""
        elif day_of_month != '*':
            # Monthly schedule
            return f"""
      <CalendarTrigger>
        <StartBoundary>2026-01-01T{hour.zfill(2)}:{minute.zfill(2)}:00</StartBoundary>
        <ScheduleByMonth>
          <DaysOfMonth>
            <Day>{day_of_month}</Day>
          </DaysOfMonth>
          <Months>
            <January /><February /><March /><April /><May /><June />
            <July /><August /><September /><October /><November /><December />
          </Months>
        </ScheduleByMonth>
      </CalendarTrigger>
"""
        else:
            # Daily schedule
            return f"""
      <CalendarTrigger>
        <StartBoundary>2026-01-01T{hour.zfill(2)}:{minute.zfill(2)}:00</StartBoundary>
        <ScheduleByDay>
          <DaysInterval>1</DaysInterval>
        </ScheduleByDay>
      </CalendarTrigger>
"""

    def _generate_task_xml(self, command: str, trigger_xml: str, task_id: str) -> str:
        """Generate Windows Task Scheduler XML.

        Args:
            command: Command to execute
            trigger_xml: Trigger XML fragment
            task_id: Task identifier

        Returns:
            Complete task XML
        """
        # Split command into executable and arguments
        parts = command.split(None, 1)
        executable = parts[0] if parts else command
        arguments = parts[1] if len(parts) > 1 else ""

        return f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>Digital FTE scheduled task: {task_id}</Description>
  </RegistrationInfo>
  <Triggers>
{trigger_xml}
  </Triggers>
  <Principals>
    <Principal id="Author">
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT1H</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{executable}</Command>
      <Arguments>{arguments}</Arguments>
    </Exec>
  </Actions>
</Task>
"""

    def validate_schedule(self, schedule: str) -> bool:
        """Validate cron expression format.

        Args:
            schedule: Cron expression

        Returns:
            True if valid
        """
        # Basic validation: 5 fields
        parts = schedule.split()
        return len(parts) == 5


if __name__ == "__main__":
    # Example usage
    manager = TaskSchedulerManager()

    # Example: List tasks
    tasks = manager.list_tasks()
    print(f"Scheduled tasks: {len(tasks)}")
    for task in tasks:
        print(f"  {task['task_id']}")

    print("TaskSchedulerManager initialized.")
