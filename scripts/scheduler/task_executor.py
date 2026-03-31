"""Task executor with retry logic and exponential backoff.

Executes scheduled tasks with:
- 3 retry attempts on failure
- Exponential backoff: 1s, 2s, 4s
- Error logging and status tracking
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import subprocess
import time
import traceback

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from watchers.shared.database import Database


class TaskExecutor:
    """Executor for scheduled tasks with retry logic."""

    def __init__(self, max_retries: int = 3):
        """Initialize task executor.

        Args:
            max_retries: Maximum retry attempts (default: 3)
        """
        self.max_retries = max_retries
        self.backoff_delays = [1, 2, 4]  # Exponential backoff in seconds
        self.db = Database()

    def execute(self, task_id: str, command: str,
               working_dir: Optional[str] = None) -> Dict[str, Any]:
        """Execute a task with retry logic.

        Args:
            task_id: Task identifier
            command: Command to execute
            working_dir: Optional working directory

        Returns:
            Execution result dict
        """
        start_time = datetime.utcnow()
        attempt = 0
        last_error = None

        while attempt < self.max_retries:
            attempt += 1

            try:
                # Execute command
                result = self._execute_command(command, working_dir)

                if result["success"]:
                    # Success - log and return
                    duration = (datetime.utcnow() - start_time).total_seconds()

                    execution_result = {
                        "success": True,
                        "task_id": task_id,
                        "attempt": attempt,
                        "duration_seconds": duration,
                        "output": result.get("output", ""),
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }

                    self._log_execution(task_id, execution_result)

                    return execution_result

                else:
                    # Command failed
                    last_error = result.get("error", "Unknown error")

                    if attempt < self.max_retries:
                        # Retry with backoff
                        delay = self.backoff_delays[attempt - 1]
                        print(f"Task {task_id} failed (attempt {attempt}/{self.max_retries}). "
                              f"Retrying in {delay}s...")
                        time.sleep(delay)
                    else:
                        # Max retries exceeded
                        break

            except Exception as e:
                last_error = str(e)
                print(f"Task {task_id} exception (attempt {attempt}/{self.max_retries}): {e}")

                if attempt < self.max_retries:
                    delay = self.backoff_delays[attempt - 1]
                    time.sleep(delay)
                else:
                    break

        # All retries failed
        duration = (datetime.utcnow() - start_time).total_seconds()

        execution_result = {
            "success": False,
            "task_id": task_id,
            "attempts": attempt,
            "duration_seconds": duration,
            "error": last_error,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        self._log_execution(task_id, execution_result)

        return execution_result

    def _execute_command(self, command: str,
                        working_dir: Optional[str] = None) -> Dict[str, Any]:
        """Execute a shell command.

        Args:
            command: Command to execute
            working_dir: Optional working directory

        Returns:
            Execution result dict
        """
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )

            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else None,
                "return_code": result.returncode
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Command timed out after 1 hour"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Execution failed: {str(e)}"
            }

    def _log_execution(self, task_id: str, result: Dict[str, Any]):
        """Log execution result to database.

        Args:
            task_id: Task identifier
            result: Execution result
        """
        try:
            # Log to database (using actions table for now)
            action_id = f"scheduled-{task_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

            self.db.log_action(
                action_id=action_id,
                action_type="scheduled_task",
                parameters={"task_id": task_id},
                safety_level=0,  # Scheduled tasks are pre-approved
                status="executed" if result["success"] else "failed"
            )

            # Update with execution result
            self.db.update_action_status(
                action_id=action_id,
                status="executed" if result["success"] else "failed",
                execution_result=result
            )

        except Exception as e:
            print(f"Error logging execution: {e}")

    def execute_python_function(self, task_id: str, func: Callable,
                                *args, **kwargs) -> Dict[str, Any]:
        """Execute a Python function with retry logic.

        Args:
            task_id: Task identifier
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Execution result dict
        """
        start_time = datetime.utcnow()
        attempt = 0
        last_error = None

        while attempt < self.max_retries:
            attempt += 1

            try:
                # Execute function
                result = func(*args, **kwargs)

                # Success
                duration = (datetime.utcnow() - start_time).total_seconds()

                execution_result = {
                    "success": True,
                    "task_id": task_id,
                    "attempt": attempt,
                    "duration_seconds": duration,
                    "result": str(result),
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }

                self._log_execution(task_id, execution_result)

                return execution_result

            except Exception as e:
                last_error = str(e)
                print(f"Task {task_id} exception (attempt {attempt}/{self.max_retries}): {e}")
                traceback.print_exc()

                if attempt < self.max_retries:
                    delay = self.backoff_delays[attempt - 1]
                    time.sleep(delay)
                else:
                    break

        # All retries failed
        duration = (datetime.utcnow() - start_time).total_seconds()

        execution_result = {
            "success": False,
            "task_id": task_id,
            "attempts": attempt,
            "duration_seconds": duration,
            "error": last_error,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        self._log_execution(task_id, execution_result)

        return execution_result


if __name__ == "__main__":
    # Example usage
    executor = TaskExecutor()

    # Example: Execute shell command
    result = executor.execute(
        task_id="test-task",
        command="echo 'Hello from scheduled task'"
    )

    print(f"Execution result:")
    print(f"  Success: {result['success']}")
    print(f"  Attempts: {result.get('attempt', result.get('attempts'))}")
    print(f"  Duration: {result['duration_seconds']}s")

    if result['success']:
        print(f"  Output: {result.get('output', '')}")
    else:
        print(f"  Error: {result.get('error', '')}")
