"""FastAPI MCP server for Digital FTE external actions.

Provides tools for sending emails, posting to LinkedIn, and sending WhatsApp messages
with input validation, rate limiting, and audit logging.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from watchers.shared.database import Database
from validator import InputValidator
from rate_limiter import RateLimiter
from tools.send_email import SendEmailTool
from tools.linkedin_post import LinkedInPostTool
from tools.whatsapp_send import WhatsAppSendTool
from approval.classifier import ActionClassifier
from approval.queue import ApprovalQueueManager
from approval.executor import ActionExecutor

app = FastAPI(
    title="Digital FTE MCP Server",
    description="Model Context Protocol server for external actions",
    version="0.1.0"
)

# Initialize components
db = Database()
validator = InputValidator()
rate_limiter = RateLimiter()
classifier = ActionClassifier()
approval_queue = ApprovalQueueManager()
executor = ActionExecutor()

# Initialize tools
tools_registry = {
    "send-email": SendEmailTool(),
    "linkedin-post": LinkedInPostTool(),
    "whatsapp-send": WhatsAppSendTool()
}


class ToolInvocation(BaseModel):
    """Tool invocation request."""
    tool: str = Field(..., description="Tool name (send-email, linkedin-post, whatsapp-send)")
    parameters: Dict[str, Any] = Field(..., description="Tool parameters")


class ToolResponse(BaseModel):
    """Tool invocation response."""
    success: bool
    action_id: Optional[str] = None
    status: str
    message: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ToolDefinition(BaseModel):
    """Tool definition for MCP protocol."""
    name: str
    description: str
    parameters: Dict[str, Any]


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "0.1.0"
    }


@app.get("/tools/list")
async def list_tools() -> List[ToolDefinition]:
    """List available tools."""
    tools = [
        ToolDefinition(
            name="send-email",
            description="Send an email via Gmail API",
            parameters={
                "type": "object",
                "properties": {
                    "recipient": {"type": "string", "format": "email"},
                    "subject": {"type": "string", "maxLength": 200},
                    "body": {"type": "string", "maxLength": 10000}
                },
                "required": ["recipient", "subject", "body"]
            }
        ),
        ToolDefinition(
            name="linkedin-post",
            description="Post an update to LinkedIn",
            parameters={
                "type": "object",
                "properties": {
                    "content": {"type": "string", "maxLength": 3000}
                },
                "required": ["content"]
            }
        ),
        ToolDefinition(
            name="whatsapp-send",
            description="Send a WhatsApp message",
            parameters={
                "type": "object",
                "properties": {
                    "recipient": {"type": "string", "pattern": "^\\+[1-9]\\d{1,14}$"},
                    "message": {"type": "string", "maxLength": 5000}
                },
                "required": ["recipient", "message"]
            }
        )
    ]
    return tools


@app.post("/tools/invoke")
async def invoke_tool(invocation: ToolInvocation) -> ToolResponse:
    """Invoke a tool with validation, rate limiting, and execution."""
    try:
        # Step 1: Validate tool exists
        if invocation.tool not in tools_registry:
            raise HTTPException(status_code=404, detail=f"Tool not found: {invocation.tool}")

        # Step 2: Validate parameters
        try:
            validated_params = validator.validate(invocation.tool, invocation.parameters)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Step 3: Check rate limits
        allowed, retry_after = rate_limiter.check_rate_limit(invocation.tool)
        if not allowed:
            return ToolResponse(
                success=False,
                status="rate_limited",
                message=f"Rate limit exceeded. Retry after {retry_after} seconds",
                error=f"Rate limit exceeded",
                result={"retry_after": retry_after}
            )

        # Step 4: Generate action ID
        action_id = f"action-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"

        # Step 5: Classify safety level using classifier
        safety_level = classifier.classify(invocation.tool, invocation.parameters)

        # Step 6: Check if action requires approval
        if classifier.requires_approval(safety_level):
            # Queue for approval (Level 2+)
            vault_path = approval_queue.queue_for_approval(
                action_id=action_id,
                action_type=invocation.tool,
                parameters=invocation.parameters,
                safety_level=safety_level
            )

            return ToolResponse(
                success=True,
                action_id=action_id,
                status="pending_approval",
                message=f"Action {invocation.tool} queued for approval (Safety Level {safety_level})",
                result={
                    "action_id": action_id,
                    "safety_level": safety_level,
                    "safety_description": classifier.get_level_description(safety_level),
                    "approval_note": vault_path,
                    "rate_limit_remaining": rate_limiter.get_remaining(invocation.tool)
                }
            )
        else:
            # Auto-execute (Level 0-1)
            db.log_action(
                action_id=action_id,
                action_type=invocation.tool,
                parameters=invocation.parameters,
                safety_level=safety_level,
                status="executing"
            )

            # Execute the tool
            tool = tools_registry[invocation.tool]
            if invocation.tool == "send-email":
                result = tool.execute(
                    validated_params["recipient"],
                    validated_params["subject"],
                    validated_params["body"]
                )
            elif invocation.tool == "linkedin-post":
                result = tool.execute(validated_params["content"])
            elif invocation.tool == "whatsapp-send":
                result = tool.execute(
                    validated_params["recipient"],
                    validated_params["message"]
                )

            # Update database with result
            db.update_action_status(
                action_id=action_id,
                status="executed" if result.get("success") else "failed",
                execution_result=result
            )

            return ToolResponse(
                success=result.get("success", False),
                action_id=action_id,
                status="executed" if result.get("success") else "failed",
                message=result.get("message", "Action executed"),
                result={
                    "action_id": action_id,
                    "safety_level": safety_level,
                    "execution_result": result
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        return ToolResponse(
            success=False,
            status="error",
            message=f"Tool invocation failed: {str(e)}",
            error=str(e)
        )


@app.post("/actions/execute")
async def execute_action(action_id: str) -> ToolResponse:
    """Execute an approved action."""
    try:
        # Execute the action using the executor
        result = executor.execute(action_id, tools_registry)

        if result.get("success"):
            return ToolResponse(
                success=True,
                action_id=action_id,
                status="executed",
                message=f"Action {action_id} executed successfully",
                result=result
            )
        else:
            return ToolResponse(
                success=False,
                action_id=action_id,
                status="failed",
                message=f"Action {action_id} execution failed",
                error=result.get("error", "Unknown error"),
                result=result
            )

    except Exception as e:
        return ToolResponse(
            success=False,
            action_id=action_id,
            status="error",
            message=f"Failed to execute action: {str(e)}",
            error=str(e)
        )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "status": "error",
            "message": exc.detail,
            "error": exc.detail
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "status": "error",
            "message": "Internal server error",
            "error": str(exc)
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
