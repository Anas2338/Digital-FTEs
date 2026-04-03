"""
Task execution MCP tool.

Executes multi-step tasks autonomously using Ralph Loop.
"""

import sys
from pathlib import Path
from typing import Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from watchers.shared.ralph_loop import RalphLoop
from datetime import datetime


class TaskExecuteTool:
    """Tool for executing multi-step tasks."""

    def __init__(self):
        """Initialize task execute tool."""
        self.ralph_loop = RalphLoop()

    def execute(self, task_id: str) -> Dict[str, Any]:
        """Execute a multi-step task."""
        try:
            result = self.ralph_loop.execute_task(task_id)
            
            result["timestamp"] = datetime.utcnow().isoformat() + "Z"
            return result

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
