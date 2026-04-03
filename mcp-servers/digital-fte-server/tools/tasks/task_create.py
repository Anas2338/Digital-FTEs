"""
Task creation MCP tool.

Creates multi-step tasks for autonomous execution.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from watchers.shared.ralph_loop import RalphLoop
from datetime import datetime


class TaskCreateTool:
    """Tool for creating multi-step tasks."""

    def __init__(self):
        """Initialize task create tool."""
        self.ralph_loop = RalphLoop()

    def execute(
        self,
        title: str,
        description: str,
        steps: List[Dict[str, Any]],
        completion_criteria: Dict[str, Any],
        assigned_to: str = "agent",
        priority: str = "medium",
        parent_task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new multi-step task."""
        try:
            task_id = self.ralph_loop.create_task(
                title=title,
                description=description,
                steps=steps,
                completion_criteria=completion_criteria,
                assigned_to=assigned_to,
                priority=priority,
                parent_task_id=parent_task_id
            )

            return {
                "success": True,
                "task_id": task_id,
                "status": "pending",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }

    def validate_parameters(
        self,
        title: str,
        description: str,
        steps: List[Dict[str, Any]],
        completion_criteria: Dict[str, Any]
    ) -> bool:
        """Validate task parameters."""
        if not title or len(title) > 200:
            raise ValueError("Title must be 1-200 characters")

        if not description:
            raise ValueError("Description is required")

        if not steps or len(steps) == 0:
            raise ValueError("At least one step is required")

        for i, step in enumerate(steps):
            if "description" not in step:
                raise ValueError(f"Step {i+1} missing description")
            if "action" not in step:
                raise ValueError(f"Step {i+1} missing action")
            if "parameters" not in step:
                raise ValueError(f"Step {i+1} missing parameters")

        if not completion_criteria:
            raise ValueError("Completion criteria is required")

        return True
