"""Input validator for MCP server tools using Pydantic.

Validates tool parameters against schemas defined in contracts/mcp-server.json.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
import re


class SendEmailParams(BaseModel):
    """Parameters for send-email tool."""
    recipient: str = Field(..., description="Recipient email address")
    subject: str = Field(..., min_length=1, max_length=200, description="Email subject")
    body: str = Field(..., min_length=1, max_length=10000, description="Email body")

    @field_validator('recipient')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email address format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, v):
            raise ValueError('Invalid email address format')
        return v


class LinkedInPostParams(BaseModel):
    """Parameters for linkedin-post tool."""
    content: str = Field(..., min_length=1, max_length=3000, description="Post content")


class WhatsAppSendParams(BaseModel):
    """Parameters for whatsapp-send tool."""
    recipient: str = Field(..., description="Recipient phone number (E.164 format)")
    message: str = Field(..., min_length=1, max_length=5000, description="Message text")

    @field_validator('recipient')
    @classmethod
    def validate_phone_number(cls, v: str) -> str:
        """Validate E.164 phone number format."""
        pattern = r'^\+[1-9]\d{1,14}$'
        if not re.match(pattern, v):
            raise ValueError('Phone number must be in E.164 format (e.g., +14155552671)')
        return v


class InputValidator:
    """Validator for MCP tool parameters."""

    def __init__(self):
        """Initialize input validator."""
        self.validators = {
            "send-email": SendEmailParams,
            "linkedin-post": LinkedInPostParams,
            "whatsapp-send": WhatsAppSendParams
        }

    def validate(self, tool: str, parameters: dict) -> BaseModel:
        """Validate parameters for a tool.

        Args:
            tool: Tool name
            parameters: Parameters dict

        Returns:
            Validated Pydantic model

        Raises:
            ValueError: If tool not found or validation fails
        """
        if tool not in self.validators:
            raise ValueError(f"Unknown tool: {tool}")

        validator_class = self.validators[tool]
        try:
            return validator_class(**parameters)
        except Exception as e:
            raise ValueError(f"Parameter validation failed: {str(e)}")

    def get_schema(self, tool: str) -> dict:
        """Get JSON schema for a tool.

        Args:
            tool: Tool name

        Returns:
            JSON schema dict
        """
        if tool not in self.validators:
            raise ValueError(f"Unknown tool: {tool}")

        return self.validators[tool].model_json_schema()
