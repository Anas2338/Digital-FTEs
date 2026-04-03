"""
Task Breakdown Logic

Decomposes complex user tasks into executable subtasks.
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class TaskBreakdown:
    """
    Breaks down complex tasks into executable steps.
    """
    
    def __init__(self):
        """Initialize task breakdown."""
        self.task_templates = {
            "financial_report": self._breakdown_financial_report,
            "social_media_campaign": self._breakdown_social_campaign,
            "email_followup": self._breakdown_email_followup
        }
    
    def breakdown_task(
        self,
        task_description: str,
        task_type: str = "generic"
    ) -> List[Dict[str, Any]]:
        """
        Break down a task into executable steps.
        
        Args:
            task_description: Natural language task description
            task_type: Type of task (financial_report, social_media_campaign, etc.)
            
        Returns:
            List of step dictionaries
        """
        if task_type in self.task_templates:
            return self.task_templates[task_type](task_description)
        else:
            return self._breakdown_generic_task(task_description)
    
    def _breakdown_financial_report(self, description: str) -> List[Dict[str, Any]]:
        """Break down financial report generation task."""
        return [
            {
                "description": "Query financial data from Odoo",
                "action": "odoo_query_financials",
                "parameters": {
                    "period": "last_month"
                },
                "validation_criteria": {
                    "success": True
                }
            },
            {
                "description": "Generate financial summary report",
                "action": "generate_report",
                "parameters": {
                    "report_type": "financial_summary"
                },
                "validation_criteria": {
                    "success": True
                }
            },
            {
                "description": "Send report via email",
                "action": "send_email",
                "parameters": {
                    "subject": "Monthly Financial Report",
                    "body": "Please find attached the monthly financial report."
                },
                "validation_criteria": {
                    "success": True
                }
            }
        ]
    
    def _breakdown_social_campaign(self, description: str) -> List[Dict[str, Any]]:
        """Break down social media campaign task."""
        return [
            {
                "description": "Create social media post content",
                "action": "draft_content",
                "parameters": {
                    "content_type": "social_post"
                },
                "validation_criteria": {
                    "success": True
                }
            },
            {
                "description": "Post to social media platforms",
                "action": "social_post",
                "parameters": {
                    "platforms": ["facebook", "twitter", "instagram"]
                },
                "validation_criteria": {
                    "success": True
                }
            },
            {
                "description": "Monitor engagement metrics",
                "action": "social_get_engagement",
                "parameters": {},
                "validation_criteria": {
                    "success": True
                }
            }
        ]
    
    def _breakdown_email_followup(self, description: str) -> List[Dict[str, Any]]:
        """Break down email follow-up task."""
        return [
            {
                "description": "Check for pending emails",
                "action": "check_emails",
                "parameters": {
                    "filter": "needs_followup"
                },
                "validation_criteria": {
                    "success": True
                }
            },
            {
                "description": "Draft follow-up email",
                "action": "draft_email",
                "parameters": {
                    "template": "followup"
                },
                "validation_criteria": {
                    "success": True
                }
            },
            {
                "description": "Send follow-up email",
                "action": "send_email",
                "parameters": {},
                "validation_criteria": {
                    "success": True
                }
            }
        ]
    
    def _breakdown_generic_task(self, description: str) -> List[Dict[str, Any]]:
        """Break down generic task (placeholder for LLM-based breakdown)."""
        return [
            {
                "description": description,
                "action": "execute_generic",
                "parameters": {
                    "task_description": description
                },
                "validation_criteria": {
                    "success": True
                }
            }
        ]
