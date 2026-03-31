"""Event logger for Digital FTE watchers.

Provides structured logging for watcher events with support for multiple
channels (Gmail, WhatsApp, LinkedIn) and event types.
"""

import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import uuid


class EventLogger:
    """Structured event logger for watcher events."""

    def __init__(self, log_dir: str = "watchers/logs"):
        """Initialize event logger.

        Args:
            log_dir: Directory for log files
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Configure logging
        self.logger = logging.getLogger("digital_fte.events")
        self.logger.setLevel(logging.INFO)

        # File handler for all events
        log_file = self.log_dir / "events.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)

        # JSON formatter
        formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": %(message)s}'
        )
        file_handler.setFormatter(formatter)

        # Avoid duplicate handlers
        if not self.logger.handlers:
            self.logger.addHandler(file_handler)

    def log_event(self, source_channel: str, event_type: str,
                  content: Dict[str, Any], event_id: Optional[str] = None) -> str:
        """Log a watcher event.

        Args:
            source_channel: Source channel (gmail, whatsapp, linkedin)
            event_type: Event type (email, message, notification)
            content: Event content
            event_id: Optional event ID (generated if not provided)

        Returns:
            Event ID
        """
        if not event_id:
            event_id = str(uuid.uuid4())

        event_data = {
            "event_id": event_id,
            "source_channel": source_channel,
            "event_type": event_type,
            "content": self._sanitize_content(content),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        self.logger.info(json.dumps(event_data))
        return event_id

    def log_error(self, source_channel: str, error_message: str,
                  error_details: Optional[Dict[str, Any]] = None):
        """Log a watcher error.

        Args:
            source_channel: Source channel
            error_message: Error message
            error_details: Optional error details
        """
        error_data = {
            "source_channel": source_channel,
            "error_message": error_message,
            "error_details": error_details or {},
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        self.logger.error(json.dumps(error_data))

    def log_health_check(self, watcher_name: str, health_status: str,
                        error_count: int = 0):
        """Log watcher health check.

        Args:
            watcher_name: Name of the watcher
            health_status: Health status (healthy, degraded, unhealthy)
            error_count: Number of consecutive errors
        """
        health_data = {
            "watcher_name": watcher_name,
            "health_status": health_status,
            "error_count": error_count,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        self.logger.info(json.dumps(health_data))

    def _sanitize_content(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize content to remove PII from logs.

        Args:
            content: Event content

        Returns:
            Sanitized content
        """
        sanitized = content.copy()

        # Redact sensitive fields
        sensitive_fields = ["password", "token", "api_key", "secret", "credential"]
        for field in sensitive_fields:
            if field in sanitized:
                sanitized[field] = "[REDACTED]"

        # Truncate long text fields
        if "body" in sanitized and isinstance(sanitized["body"], str):
            if len(sanitized["body"]) > 500:
                sanitized["body"] = sanitized["body"][:500] + "... [TRUNCATED]"

        if "message_text" in sanitized and isinstance(sanitized["message_text"], str):
            if len(sanitized["message_text"]) > 500:
                sanitized["message_text"] = sanitized["message_text"][:500] + "... [TRUNCATED]"

        return sanitized
