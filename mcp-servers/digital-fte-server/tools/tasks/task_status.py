"""
Task status MCP tool.

Retrieves status and progress of multi-step tasks.
"""

import sys
from pathlib import Path
from typing import Dict, Any
import json

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from watchers.shared.database import Database
from datetime import datetime


class TaskStatusTool:
    """Tool for retrieving task status."""

    def __init__(self):
        """Initialize task status tool."""
        self.db = Database()

    def execute(self, task_id: str) -> Dict[str, Any]:
        """Get status of a multi-step task."""
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("""
                SELECT * FROM multi_step_tasks WHERE id = ?
            """, (task_id,))

            task = cursor.fetchone()

            if not task:
                return {
                    "success": False,
                    "error": f"Task not found: {task_id}",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }

            steps = json.loads(task["steps"])
            completion_criteria = json.loads(task["completion_criteria"])

            return {
                "success": True,
                "task_id": task_id,
                "title": task["title"],
                "description": task["description"],
                "status": task["status"],
                "priority": task["priority"],
                "assigned_to": task["assigned_to"],
                "current_step": task["current_step_index"] + 1,
                "total_steps": len(steps),
                "steps": steps,
                "completion_criteria": completion_criteria,
                "created_at": task["created_at"],
                "updated_at": task["updated_at"],
                "completed_at": task["completed_at"],
                "summary_path": task["summary_path"],
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }

    def validate_parameters(self, task_id: str) -> bool:
        """Validate parameters."""
        if not task_id:
            raise ValueError("Task ID is required")
        return True
