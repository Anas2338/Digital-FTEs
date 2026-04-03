"""Action executor for approved actions.

Executes approved actions and updates their status in the database and vault.
Integrates with comprehensive audit logging for compliance and transparency.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from watchers.shared.database import Database
from watchers.shared.vault_writer import VaultWriter
from watchers.shared.audit_logger import AuditLogger


class ActionExecutor:
    """Executor for approved actions with audit logging."""

    def __init__(self):
        """Initialize action executor."""
        self.db = Database()
        self.vault_writer = VaultWriter()
        self.audit_logger = AuditLogger()

    def execute(self, action_id: str, tools_registry: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an approved action with audit logging.

        Args:
            action_id: Action identifier
            tools_registry: Registry of available tools

        Returns:
            Execution result dict
        """
        # Get action details from database
        pending_actions = self.db.get_pending_actions()
        action = None
        for a in pending_actions:
            if a["action_id"] == action_id:
                action = a
                break

        if not action:
            return {
                "success": False,
                "error": f"Action {action_id} not found or not approved"
            }

        # Check if action is approved
        if action["status"] != "approved":
            return {
                "success": False,
                "error": f"Action {action_id} is not approved (status: {action['status']})"
            }

        # Get the tool
        action_type = action["action_type"]
        if action_type not in tools_registry:
            # Log failed execution attempt
            self.audit_logger.log_action(
                action_type="execute",
                action_name=action_type,
                parameters=action["parameters"],
                error_message=f"Tool {action_type} not found",
                safety_level=action["safety_level"]
            )

            return {
                "success": False,
                "error": f"Tool {action_type} not found"
            }

        tool = tools_registry[action_type]

        try:
            # Execute the tool
            parameters = action["parameters"]

            # Call appropriate tool method based on action type
            if action_type == "send-email":
                result = tool.execute(
                    parameters["recipient"],
                    parameters["subject"],
                    parameters["body"]
                )
            elif action_type == "linkedin-post":
                result = tool.execute(parameters["content"])
            elif action_type == "whatsapp-send":
                result = tool.execute(
                    parameters["recipient"],
                    parameters["message"]
                )
            else:
                result = {"success": False, "error": "Unknown action type"}

            # Log successful execution to audit trail
            if result.get("success"):
                self.audit_logger.log_action(
                    action_type="execute",
                    action_name=action_type,
                    parameters=parameters,
                    result=result,
                    reasoning=f"Approved action executed successfully",
                    user_approval=action.get("audit_trail", [{}])[-1].get("approver"),
                    safety_level=action["safety_level"]
                )
            else:
                # Log failed execution
                self.audit_logger.log_action(
                    action_type="execute",
                    action_name=action_type,
                    parameters=parameters,
                    result=result,
                    error_message=result.get("error", "Execution failed"),
                    user_approval=action.get("audit_trail", [{}])[-1].get("approver"),
                    safety_level=action["safety_level"]
                )

            # Update database with execution result
            self.db.update_action_status(
                action_id=action_id,
                status="executed" if result.get("success") else "failed",
                execution_result=result
            )

            # Move approval note from /Approvals to /Done
            self._move_approval_note(action_id, "Done", result)

            return result

        except Exception as e:
            # Log exception to audit trail
            self.audit_logger.log_action(
                action_type="execute",
                action_name=action_type,
                parameters=action["parameters"],
                error_message=f"Execution exception: {str(e)}",
                user_approval=action.get("audit_trail", [{}])[-1].get("approver"),
                safety_level=action["safety_level"]
            )

            # Update database with failure
            self.db.update_action_status(
                action_id=action_id,
                status="failed",
                execution_result={"success": False, "error": str(e)}
            )

            return {
                "success": False,
                "error": f"Execution failed: {str(e)}"
            }

    def _move_approval_note(self, action_id: str, target_folder: str,
                           execution_result: Dict[str, Any]):
        """Move approval note to target folder and append execution result.

        Args:
            action_id: Action identifier
            target_folder: Target folder (Done, Failed)
            execution_result: Execution result to append
        """
        try:
            approvals_dir = Path(self.vault_writer.vault_path) / "Approvals"
            for note_file in approvals_dir.glob("*.md"):
                content = note_file.read_text(encoding="utf-8")
                if action_id in content:
                    # Move to target folder
                    target_path = Path(self.vault_writer.vault_path) / target_folder / note_file.name
                    note_file.rename(target_path)

                    # Append execution result
                    from datetime import datetime
                    with open(target_path, "a", encoding="utf-8") as f:
                        f.write(f"\n\n## Execution Result\n\n")
                        f.write(f"**Status**: {'Success' if execution_result.get('success') else 'Failed'}\n")
                        f.write(f"**Timestamp**: {datetime.utcnow().isoformat()}Z\n")
                        if execution_result.get("success"):
                            f.write(f"**Result**: {execution_result}\n")
                        else:
                            f.write(f"**Error**: {execution_result.get('error', 'Unknown error')}\n")
                    break

        except Exception as e:
            print(f"Error moving approval note: {e}")
