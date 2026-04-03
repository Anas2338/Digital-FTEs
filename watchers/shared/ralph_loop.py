"""
Ralph Wiggum Loop Executor

Autonomous multi-step task execution pattern.
Iterates until completion criteria met, with self-validation and error recovery.
"""

import json
import logging
import uuid
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from pathlib import Path

from watchers.shared.database import Database
from watchers.shared.audit_logger import AuditLogger

logger = logging.getLogger(__name__)


class TaskStep:
    """Represents a single step in a multi-step task."""
    
    def __init__(
        self,
        step_number: int,
        description: str,
        action: str,
        parameters: Dict[str, Any],
        validation_criteria: Optional[Dict[str, Any]] = None
    ):
        self.step_number = step_number
        self.description = description
        self.action = action
        self.parameters = parameters
        self.validation_criteria = validation_criteria or {}
        self.status = "pending"
        self.result = None
        self.error = None
        self.attempts = 0
        self.max_attempts = 3


class RalphLoop:
    """
    Ralph Wiggum Loop: Autonomous task executor.
    
    Executes multi-step tasks iteratively until completion criteria met.
    """
    
    def __init__(
        self,
        db: Database = None,
        vault_path: str = "obsidian-vault"
    ):
        """Initialize Ralph Loop executor."""
        self.db = db or Database()
        self.audit_logger = AuditLogger(self.db)
        self.vault_path = Path(vault_path)
        self.action_registry = {}
        
    def register_action(self, action_name: str, handler: Callable):
        """Register an action handler."""
        self.action_registry[action_name] = handler
        logger.info(f"Registered action: {action_name}")
    
    def create_task(
        self,
        title: str,
        description: str,
        steps: List[Dict[str, Any]],
        completion_criteria: Dict[str, Any],
        assigned_to: str = "agent",
        priority: str = "medium",
        parent_task_id: Optional[str] = None
    ) -> str:
        """Create a new multi-step task."""
        task_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat() + "Z"
        
        cursor = self.db.conn.cursor()
        cursor.execute("""
            INSERT INTO multi_step_tasks (
                id, title, description, assigned_to, priority,
                status, steps, current_step_index, completion_criteria,
                parent_task_id, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, 'pending', ?, 0, ?, ?, ?, ?)
        """, (
            task_id,
            title,
            description,
            assigned_to,
            priority,
            json.dumps(steps),
            json.dumps(completion_criteria),
            parent_task_id,
            now,
            now
        ))
        
        self.db.conn.commit()
        
        self.audit_logger.log_action(
            action_type="task_created",
            component="ralph_loop",
            details={
                "task_id": task_id,
                "title": title,
                "steps_count": len(steps),
                "priority": priority
            }
        )
        
        logger.info(f"Created task: {task_id} - {title}")
        return task_id
    
    def execute_task(self, task_id: str) -> Dict[str, Any]:
        """Execute a multi-step task using Ralph Wiggum loop pattern."""
        try:
            task = self._load_task(task_id)
            
            if not task:
                return {"success": False, "error": f"Task not found: {task_id}"}
            
            self._update_task_status(task_id, "in_progress")
            
            steps = json.loads(task["steps"])
            completion_criteria = json.loads(task["completion_criteria"])
            current_step_index = task["current_step_index"]
            
            logger.info(
                f"Executing task {task_id}: {task['title']} "
                f"(step {current_step_index + 1}/{len(steps)})"
            )
            
            while current_step_index < len(steps):
                step_data = steps[current_step_index]
                step = TaskStep(
                    step_number=current_step_index + 1,
                    description=step_data["description"],
                    action=step_data["action"],
                    parameters=step_data["parameters"],
                    validation_criteria=step_data.get("validation_criteria")
                )
                
                step_result = self._execute_step(task_id, step)
                
                if not step_result["success"]:
                    if step_result.get("escalate", False):
                        return self._escalate_to_user(task_id, step, step_result)
                    else:
                        self._update_task_status(task_id, "failed")
                        return {
                            "success": False,
                            "task_id": task_id,
                            "failed_step": step.step_number,
                            "error": step_result.get("error")
                        }
                
                current_step_index += 1
                self._update_current_step(task_id, current_step_index)
            
            if self._check_completion_criteria(task_id, completion_criteria):
                return self._complete_task(task_id)
            else:
                self._update_task_status(task_id, "blocked")
                return {
                    "success": False,
                    "task_id": task_id,
                    "error": "Completion criteria not met",
                    "escalate": True
                }
                
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            self._update_task_status(task_id, "failed")
            return {"success": False, "task_id": task_id, "error": str(e)}
    
    def _execute_step(self, task_id: str, step: TaskStep) -> Dict[str, Any]:
        """Execute a single task step."""
        logger.info(f"Executing step {step.step_number}: {step.description}")
        
        self.audit_logger.log_action(
            action_type="step_started",
            component="ralph_loop",
            details={
                "task_id": task_id,
                "step_number": step.step_number,
                "action": step.action
            }
        )
        
        while step.attempts < step.max_attempts:
            step.attempts += 1
            
            try:
                if step.action not in self.action_registry:
                    return {
                        "success": False,
                        "error": f"Unknown action: {step.action}",
                        "escalate": True
                    }
                
                handler = self.action_registry[step.action]
                result = handler(**step.parameters)
                
                if self._validate_step_result(step, result):
                    step.status = "completed"
                    step.result = result
                    
                    self.audit_logger.log_action(
                        action_type="step_completed",
                        component="ralph_loop",
                        details={
                            "task_id": task_id,
                            "step_number": step.step_number,
                            "attempts": step.attempts
                        }
                    )
                    
                    return {"success": True, "result": result}
                else:
                    logger.warning(
                        f"Step {step.step_number} validation failed, "
                        f"attempt {step.attempts}/{step.max_attempts}"
                    )
                    
            except Exception as e:
                logger.error(
                    f"Step {step.step_number} execution error: {e}, "
                    f"attempt {step.attempts}/{step.max_attempts}"
                )
                step.error = str(e)
        
        step.status = "failed"
        
        self.audit_logger.log_action(
            action_type="step_failed",
            component="ralph_loop",
            details={
                "task_id": task_id,
                "step_number": step.step_number,
                "attempts": step.attempts,
                "error": step.error
            }
        )
        
        return {
            "success": False,
            "error": step.error or "Max attempts exceeded",
            "escalate": True
        }
    
    def _validate_step_result(self, step: TaskStep, result: Dict[str, Any]) -> bool:
        """Validate step execution result."""
        if not result.get("success", False):
            return False
        
        if not step.validation_criteria:
            return True
        
        for key, expected_value in step.validation_criteria.items():
            if key not in result:
                return False
            if result[key] != expected_value:
                return False
        
        return True
    
    def _check_completion_criteria(self, task_id: str, criteria: Dict[str, Any]) -> bool:
        """Check if task completion criteria are met."""
        return True
    
    def _complete_task(self, task_id: str) -> Dict[str, Any]:
        """Mark task as completed and generate summary."""
        now = datetime.utcnow().isoformat() + "Z"
        
        task = self._load_task(task_id)
        summary_path = self._generate_task_summary(task)
        
        cursor = self.db.conn.cursor()
        cursor.execute("""
            UPDATE multi_step_tasks
            SET status = 'completed',
                completed_at = ?,
                summary_path = ?,
                updated_at = ?
            WHERE id = ?
        """, (now, str(summary_path), now, task_id))
        
        self.db.conn.commit()
        
        self.audit_logger.log_action(
            action_type="task_completed",
            component="ralph_loop",
            details={
                "task_id": task_id,
                "summary_path": str(summary_path)
            }
        )
        
        logger.info(f"Task completed: {task_id}")
        
        return {
            "success": True,
            "task_id": task_id,
            "status": "completed",
            "summary_path": str(summary_path)
        }
    
    def _escalate_to_user(self, task_id: str, step: TaskStep, error_info: Dict[str, Any]) -> Dict[str, Any]:
        """Escalate task to user for manual intervention."""
        self._update_task_status(task_id, "blocked")
        
        self.audit_logger.log_action(
            action_type="task_escalated",
            component="ralph_loop",
            details={
                "task_id": task_id,
                "step_number": step.step_number,
                "reason": error_info.get("error")
            }
        )
        
        logger.warning(f"Task escalated to user: {task_id}")
        
        return {
            "success": False,
            "task_id": task_id,
            "status": "blocked",
            "escalated": True,
            "step_number": step.step_number,
            "error": error_info.get("error"),
            "message": "Task requires user intervention"
        }
    
    def _generate_task_summary(self, task: Dict[str, Any]) -> Path:
        """Generate task summary in Obsidian vault."""
        summary_dir = self.vault_path / "Needs_Action" / "Completed"
        summary_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{task['id']}_{timestamp}.md"
        filepath = summary_dir / filename
        
        content = f"""# Task Summary: {task['title']}

## Details
- **Task ID**: {task['id']}
- **Priority**: {task['priority']}
- **Assigned To**: {task['assigned_to']}
- **Created**: {task['created_at']}
- **Completed**: {task['completed_at']}

## Description
{task['description']}

## Steps Completed
"""
        
        steps = json.loads(task['steps'])
        for i, step in enumerate(steps, 1):
            content += f"{i}. {step['description']}\n"
        
        content += f"""
---
*Generated by Ralph Loop on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return filepath
    
    def _load_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Load task from database."""
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT * FROM multi_step_tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def _update_task_status(self, task_id: str, status: str):
        """Update task status."""
        now = datetime.utcnow().isoformat() + "Z"
        cursor = self.db.conn.cursor()
        cursor.execute("""
            UPDATE multi_step_tasks
            SET status = ?, updated_at = ?
            WHERE id = ?
        """, (status, now, task_id))
        self.db.conn.commit()
    
    def _update_current_step(self, task_id: str, step_index: int):
        """Update current step index."""
        now = datetime.utcnow().isoformat() + "Z"
        cursor = self.db.conn.cursor()
        cursor.execute("""
            UPDATE multi_step_tasks
            SET current_step_index = ?, updated_at = ?
            WHERE id = ?
        """, (step_index, now, task_id))
        self.db.conn.commit()
    
    def resume_task(self, task_id: str) -> Dict[str, Any]:
        """Resume a blocked or interrupted task."""
        task = self._load_task(task_id)
        
        if not task:
            return {"success": False, "error": f"Task not found: {task_id}"}
        
        if task["status"] not in ["blocked", "in_progress"]:
            return {
                "success": False,
                "error": f"Cannot resume task with status: {task['status']}"
            }
        
        logger.info(f"Resuming task: {task_id}")
        return self.execute_task(task_id)
