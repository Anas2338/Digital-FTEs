"""Task completion workflow manager.

Handles the complete lifecycle of task completion:
- Validate all success criteria met
- Update task status to completed
- Move task from /Needs_Action to /Done
- Move associated Plan.md to /Done
- Update Dashboard.md with completion summary
- Log completion metrics
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import yaml
import re
import shutil

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from claude.skills.reasoning_plan.plan_executor import PlanExecutor
from claude.skills.reasoning_plan.criteria_validator import SuccessCriteriaValidator
from claude.skills.reasoning_plan.config import VAULT_DIRS


class TaskCompletionWorkflow:
    """Manager for task completion workflow."""

    def __init__(self, vault_path: str = "obsidian-vault"):
        """Initialize task completion workflow.

        Args:
            vault_path: Path to Obsidian vault
        """
        self.vault_path = Path(vault_path)
        self.needs_action_dir = self.vault_path / VAULT_DIRS["needs_action"]
        self.done_dir = self.vault_path / VAULT_DIRS["done"]
        self.dashboard_path = self.vault_path / VAULT_DIRS["dashboard"]

        self.executor = PlanExecutor(str(vault_path))
        self.validator = SuccessCriteriaValidator(str(vault_path))

        # Ensure directories exist
        self.needs_action_dir.mkdir(parents=True, exist_ok=True)
        self.done_dir.mkdir(parents=True, exist_ok=True)

    def complete_task(self, task_file_path: str,
                     plan_file_path: Optional[str] = None,
                     force: bool = False) -> Dict[str, Any]:
        """Complete a task and move to /Done.

        Args:
            task_file_path: Path to task file
            plan_file_path: Optional path to plan file
            force: Force completion without validation

        Returns:
            Completion result dict
        """
        task_path = Path(task_file_path)

        if not task_path.exists():
            return {
                "success": False,
                "error": f"Task file not found: {task_file_path}"
            }

        # Validate completion if plan exists and not forced
        if plan_file_path and not force:
            validation = self.validator.validate_all_criteria(plan_file_path)

            if not validation["ready_for_completion"]:
                return {
                    "success": False,
                    "error": "Task not ready for completion",
                    "validation": validation,
                    "suggestion": "Complete remaining success criteria or use force=True"
                }

        # Update task status
        self._update_task_status(task_file_path, "completed")

        # Move task to /Done
        done_task_path = self._move_to_done(task_path)

        # Move plan to /Done if exists
        done_plan_path = None
        if plan_file_path:
            plan_path = Path(plan_file_path)
            if plan_path.exists():
                done_plan_path = self._move_to_done(plan_path)
                # Update plan status
                if done_plan_path:
                    self.executor.update_plan_status(str(done_plan_path), "completed")

        # Calculate metrics
        metrics = self._calculate_completion_metrics(
            task_file_path, plan_file_path
        )

        # Update Dashboard.md
        self._update_dashboard(task_path.stem, metrics)

        return {
            "success": True,
            "task_path": str(done_task_path),
            "plan_path": str(done_plan_path) if done_plan_path else None,
            "metrics": metrics,
            "completed_at": datetime.utcnow().isoformat() + "Z"
        }

    def _update_task_status(self, task_file_path: str, status: str):
        """Update task status in frontmatter.

        Args:
            task_file_path: Path to task file
            status: New status
        """
        try:
            content = Path(task_file_path).read_text(encoding='utf-8')

            # Parse frontmatter
            match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
            if match:
                frontmatter = yaml.safe_load(match.group(1))
                task_content = match.group(2)

                frontmatter["status"] = status
                frontmatter["completed_at"] = datetime.utcnow().isoformat() + "Z"

                # Rebuild content
                new_content = f"---\n{yaml.dump(frontmatter, default_flow_style=False)}---\n{task_content}"
                Path(task_file_path).write_text(new_content, encoding='utf-8')

        except Exception as e:
            print(f"Error updating task status: {e}")

    def _move_to_done(self, file_path: Path) -> Path:
        """Move file to /Done directory.

        Args:
            file_path: Path to file

        Returns:
            New path in /Done directory
        """
        done_path = self.done_dir / file_path.name

        # Handle name conflicts
        if done_path.exists():
            timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
            stem = done_path.stem
            suffix = done_path.suffix
            done_path = self.done_dir / f"{stem}-{timestamp}{suffix}"

        # Move file
        shutil.move(str(file_path), str(done_path))

        return done_path

    def _calculate_completion_metrics(self, task_file_path: str,
                                     plan_file_path: Optional[str]) -> Dict[str, Any]:
        """Calculate completion metrics.

        Args:
            task_file_path: Path to task file
            plan_file_path: Optional path to plan file

        Returns:
            Metrics dict
        """
        metrics = {
            "had_plan": plan_file_path is not None,
            "completion_time": None,
            "total_steps": 0,
            "reevaluation_count": 0
        }

        if plan_file_path and Path(plan_file_path).exists():
            try:
                plan = self.executor.load_plan(plan_file_path)

                # Calculate completion time
                created = datetime.fromisoformat(
                    plan["frontmatter"]["created"].replace("Z", "")
                )
                completed = datetime.utcnow()
                duration = completed - created

                metrics["completion_time"] = str(duration)
                metrics["completion_hours"] = round(duration.total_seconds() / 3600, 2)
                metrics["total_steps"] = len(plan["steps"])
                metrics["reevaluation_count"] = plan["frontmatter"].get("reevaluation_count", 0)
                metrics["complexity_score"] = plan["frontmatter"].get("complexity_score")

            except Exception as e:
                print(f"Error calculating metrics: {e}")

        return metrics

    def _update_dashboard(self, task_name: str, metrics: Dict[str, Any]):
        """Update Dashboard.md with completion summary.

        Args:
            task_name: Task name
            metrics: Completion metrics
        """
        try:
            # Read or create dashboard
            if self.dashboard_path.exists():
                content = self.dashboard_path.read_text(encoding='utf-8')
            else:
                content = "# Dashboard\n\n## Completed Tasks\n\n"

            # Add completion entry
            timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M')
            entry = f"- **{task_name}** - Completed {timestamp}"

            if metrics.get("had_plan"):
                entry += f" ({metrics.get('total_steps', 0)} steps"
                if metrics.get("completion_hours"):
                    entry += f", {metrics['completion_hours']}h"
                if metrics.get("reevaluation_count", 0) > 0:
                    entry += f", {metrics['reevaluation_count']} re-evaluations"
                entry += ")"

            entry += "\n"

            # Insert after "## Completed Tasks" header
            if "## Completed Tasks" in content:
                content = content.replace(
                    "## Completed Tasks\n\n",
                    f"## Completed Tasks\n\n{entry}"
                )
            else:
                content += f"\n## Completed Tasks\n\n{entry}"

            # Write back
            self.dashboard_path.write_text(content, encoding='utf-8')

        except Exception as e:
            print(f"Error updating dashboard: {e}")

    def list_pending_tasks(self) -> list[Dict[str, Any]]:
        """List all pending tasks in /Needs_Action.

        Returns:
            List of task dicts
        """
        tasks = []

        if not self.needs_action_dir.exists():
            return tasks

        for task_file in self.needs_action_dir.glob("*.md"):
            # Skip plan files
            if "-plan.md" in task_file.name:
                continue

            try:
                content = task_file.read_text(encoding='utf-8')

                # Parse frontmatter
                match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
                if match:
                    frontmatter = yaml.safe_load(match.group(1))

                    # Check for associated plan
                    plan_file = task_file.parent / f"{task_file.stem}-plan.md"
                    has_plan = plan_file.exists()

                    tasks.append({
                        "name": task_file.stem,
                        "path": str(task_file),
                        "status": frontmatter.get("status", "unknown"),
                        "has_plan": has_plan,
                        "plan_path": str(plan_file) if has_plan else None,
                        "created": frontmatter.get("created")
                    })

            except Exception as e:
                print(f"Error reading task {task_file}: {e}")
                continue

        return tasks

    def get_completion_stats(self) -> Dict[str, Any]:
        """Get completion statistics.

        Returns:
            Stats dict
        """
        stats = {
            "total_completed": 0,
            "with_plan": 0,
            "without_plan": 0,
            "avg_completion_hours": 0,
            "total_reevaluations": 0
        }

        if not self.done_dir.exists():
            return stats

        completion_times = []
        reevaluations = []

        for task_file in self.done_dir.glob("*.md"):
            # Skip plan files
            if "-plan.md" in task_file.name:
                continue

            stats["total_completed"] += 1

            # Check for associated plan
            plan_file = task_file.parent / f"{task_file.stem}-plan.md"
            if plan_file.exists():
                stats["with_plan"] += 1

                try:
                    plan = self.executor.load_plan(str(plan_file))

                    # Track completion time
                    if "created" in plan["frontmatter"]:
                        created = datetime.fromisoformat(
                            plan["frontmatter"]["created"].replace("Z", "")
                        )
                        # Estimate completed time from file modification
                        completed = datetime.fromtimestamp(plan_file.stat().st_mtime)
                        duration_hours = (completed - created).total_seconds() / 3600
                        completion_times.append(duration_hours)

                    # Track re-evaluations
                    reevaluation_count = plan["frontmatter"].get("reevaluation_count", 0)
                    reevaluations.append(reevaluation_count)
                    stats["total_reevaluations"] += reevaluation_count

                except Exception:
                    pass
            else:
                stats["without_plan"] += 1

        # Calculate averages
        if completion_times:
            stats["avg_completion_hours"] = round(
                sum(completion_times) / len(completion_times), 2
            )

        if reevaluations:
            stats["avg_reevaluations"] = round(
                sum(reevaluations) / len(reevaluations), 2
            )

        return stats


if __name__ == "__main__":
    # Example usage
    workflow = TaskCompletionWorkflow()

    # Example: List pending tasks
    pending = workflow.list_pending_tasks()
    print(f"Pending tasks: {len(pending)}")
    for task in pending:
        print(f"  - {task['name']} (has plan: {task['has_plan']})")

    # Example: Get completion stats
    stats = workflow.get_completion_stats()
    print(f"\nCompletion stats:")
    print(f"  Total completed: {stats['total_completed']}")
    print(f"  With plan: {stats['with_plan']}")
    print(f"  Avg completion time: {stats['avg_completion_hours']}h")

    # Example: Complete a task
    # result = workflow.complete_task(
    #     "obsidian-vault/Needs_Action/oauth-task.md",
    #     "obsidian-vault/Needs_Action/oauth-task-plan.md"
    # )
    # print(f"Task completed: {result['success']}")
