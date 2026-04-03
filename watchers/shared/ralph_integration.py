"""
Ralph Loop Integration with MCP Tools

Demonstrates how Ralph Loop integrates with existing MCP tools
for autonomous multi-step task execution.
"""

import logging
from typing import Dict, Any

from watchers.shared.ralph_loop import RalphLoop
from watchers.shared.database import Database

logger = logging.getLogger(__name__)


class RalphIntegration:
    """
    Integrates Ralph Loop with MCP tools for autonomous execution.
    """
    
    def __init__(self):
        """Initialize Ralph Loop integration."""
        self.ralph_loop = RalphLoop()
        self.db = Database()
        self._register_actions()
    
    def _register_actions(self):
        """Register all available MCP tool actions."""
        self.ralph_loop.register_action("send_email", self._send_email_action)
        self.ralph_loop.register_action("social_post", self._social_post_action)
        self.ralph_loop.register_action("odoo_query_financials", self._odoo_query_action)
        self.ralph_loop.register_action("generate_report", self._generate_report_action)
        
        logger.info("Registered all MCP tool actions with Ralph Loop")
    
    def _send_email_action(self, **kwargs) -> Dict[str, Any]:
        """Execute send email action (delegates to MCP tool)."""
        logger.info(f"Executing send_email action: {kwargs}")
        return {"success": True, "message_id": "mock-email-id"}
    
    def _social_post_action(self, **kwargs) -> Dict[str, Any]:
        """Execute social post action (delegates to MCP tool)."""
        logger.info(f"Executing social_post action: {kwargs}")
        return {"success": True, "post_id": "mock-post-id"}
    
    def _odoo_query_action(self, **kwargs) -> Dict[str, Any]:
        """Execute Odoo query action (delegates to MCP tool)."""
        logger.info(f"Executing odoo_query_financials action: {kwargs}")
        return {"success": True, "data": {"revenue": 50000, "expenses": 30000}}
    
    def _generate_report_action(self, **kwargs) -> Dict[str, Any]:
        """Execute report generation action."""
        logger.info(f"Executing generate_report action: {kwargs}")
        return {"success": True, "report_path": "reports/financial_summary.pdf"}
    
    def create_financial_report_task(self) -> str:
        """
        Create a multi-step task for generating and sending financial report.
        
        Returns:
            Task ID
        """
        steps = [
            {
                "description": "Query financial data from Odoo",
                "action": "odoo_query_financials",
                "parameters": {"period": "last_month"},
                "validation_criteria": {"success": True}
            },
            {
                "description": "Generate financial summary report",
                "action": "generate_report",
                "parameters": {"report_type": "financial_summary"},
                "validation_criteria": {"success": True}
            },
            {
                "description": "Send report via email",
                "action": "send_email",
                "parameters": {
                    "recipient": "ceo@company.com",
                    "subject": "Monthly Financial Report",
                    "body": "Please find the monthly financial report."
                },
                "validation_criteria": {"success": True}
            }
        ]
        
        completion_criteria = {
            "all_steps_completed": True,
            "email_sent": True
        }
        
        task_id = self.ralph_loop.create_task(
            title="Generate and Send Monthly Financial Report",
            description="Autonomous task to query financials, generate report, and email to CEO",
            steps=steps,
            completion_criteria=completion_criteria,
            assigned_to="agent",
            priority="high"
        )
        
        logger.info(f"Created financial report task: {task_id}")
        return task_id
    
    def execute_autonomous_task(self, task_id: str) -> Dict[str, Any]:
        """
        Execute a task autonomously using Ralph Loop.
        
        Args:
            task_id: Task ID to execute
            
        Returns:
            Execution result
        """
        logger.info(f"Starting autonomous execution of task: {task_id}")
        
        result = self.ralph_loop.execute_task(task_id)
        
        if result["success"]:
            logger.info(
                f"Task completed successfully: {task_id}\n"
                f"Summary: {result.get('summary_path')}"
            )
        else:
            logger.error(
                f"Task failed or escalated: {task_id}\n"
                f"Status: {result.get('status')}\n"
                f"Error: {result.get('error')}"
            )
        
        return result


def demo_autonomous_execution():
    """Demonstrate autonomous multi-step task execution."""
    print("\n" + "="*60)
    print("Ralph Loop Autonomous Execution Demo")
    print("="*60)
    
    integration = RalphIntegration()
    
    print("\n1. Creating multi-step financial report task...")
    task_id = integration.create_financial_report_task()
    print(f"   Task created: {task_id}")
    
    print("\n2. Executing task autonomously...")
    result = integration.execute_autonomous_task(task_id)
    
    print("\n3. Execution result:")
    print(f"   Success: {result['success']}")
    print(f"   Status: {result.get('status')}")
    
    if result["success"]:
        print(f"   Summary: {result.get('summary_path')}")
        print("\n✓ Task completed autonomously!")
    else:
        print(f"   Error: {result.get('error')}")
        if result.get('escalated'):
            print("\n⚠ Task escalated to user for intervention")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    demo_autonomous_execution()
