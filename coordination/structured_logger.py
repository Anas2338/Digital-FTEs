"""
Structured Logger for Digital FTE

Provides structured logging for coordination operations with JSON output.
Supports log aggregation and analysis.

Based on tasks.md T074 and constitution principles.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any
from enum import Enum

from coordination.logical_clock import LamportClock, LamportTimestamp


class LogLevel(Enum):
    """Log levels for structured logging."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class OperationType(Enum):
    """Types of coordination operations."""
    CLAIM_TASK = "claim_task"
    RELEASE_TASK = "release_task"
    SYNC_VAULT = "sync_vault"
    RESOLVE_CONFLICT = "resolve_conflict"
    GENERATE_DRAFT = "generate_draft"
    PROCESS_APPROVAL = "process_approval"
    EXECUTE_ACTION = "execute_action"
    HEALTH_CHECK = "health_check"
    ALERT_SENT = "alert_sent"
    RECOVERY_ACTION = "recovery_action"


class StructuredLogger:
    """
    Structured logger for coordination operations.

    Outputs JSON-formatted logs for easy parsing and aggregation.
    Includes logical timestamps for distributed system ordering.
    """

    def __init__(
        self,
        agent_id: str,
        log_file: Optional[Path] = None,
        console_output: bool = True
    ):
        """
        Initialize structured logger.

        Args:
            agent_id: Agent identifier (cloud or local)
            log_file: Optional file path for JSON logs
            console_output: Whether to also output to console
        """
        self.agent_id = agent_id
        self.log_file = log_file
        self.console_output = console_output
        self.clock = LamportClock(agent_id=agent_id)

        # Set up standard logger for console output
        if console_output:
            self.console_logger = logging.getLogger(f"structured_{agent_id}")
            self.console_logger.setLevel(logging.INFO)

    def log(
        self,
        level: LogLevel,
        operation: OperationType,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
        error: Optional[Exception] = None
    ) -> None:
        """
        Log a structured event.

        Args:
            level: Log level
            operation: Type of operation
            message: Human-readable message
            metadata: Additional structured data
            error: Exception if this is an error log
        """
        timestamp = self.clock.tick()

        log_entry = {
            "timestamp": timestamp.to_dict(),
            "wall_clock_time": datetime.now().isoformat(),
            "agent_id": self.agent_id,
            "level": level.value,
            "operation": operation.value,
            "message": message,
            "metadata": metadata or {}
        }

        if error:
            log_entry["error"] = {
                "type": type(error).__name__,
                "message": str(error),
                "traceback": self._format_traceback(error)
            }

        # Write to JSON log file
        if self.log_file:
            self._write_to_file(log_entry)

        # Write to console
        if self.console_output:
            self._write_to_console(log_entry)

    def _write_to_file(self, log_entry: Dict) -> None:
        """Write log entry to JSON file (one entry per line)."""
        try:
            if self.log_file:
                self.log_file.parent.mkdir(parents=True, exist_ok=True)
                with open(self.log_file, 'a') as f:
                    f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            # Fallback to console if file write fails
            print(f"Failed to write to log file: {e}")

    def _write_to_console(self, log_entry: Dict) -> None:
        """Write formatted log entry to console."""
        level_map = {
            LogLevel.DEBUG: logging.DEBUG,
            LogLevel.INFO: logging.INFO,
            LogLevel.WARNING: logging.WARNING,
            LogLevel.ERROR: logging.ERROR,
            LogLevel.CRITICAL: logging.CRITICAL
        }

        log_level = level_map.get(LogLevel(log_entry["level"]), logging.INFO)

        # Format: [timestamp] [agent] [operation] message
        formatted = (
            f"[{log_entry['wall_clock_time']}] "
            f"[{log_entry['agent_id']}] "
            f"[{log_entry['operation']}] "
            f"{log_entry['message']}"
        )

        if log_entry.get("metadata"):
            formatted += f" | {json.dumps(log_entry['metadata'])}"

        if log_entry.get("error"):
            formatted += f" | ERROR: {log_entry['error']['message']}"

        self.console_logger.log(log_level, formatted)

    def _format_traceback(self, error: Exception) -> Optional[str]:
        """Format exception traceback."""
        import traceback
        try:
            return ''.join(traceback.format_exception(
                type(error), error, error.__traceback__
            ))
        except Exception:
            return None

    # Convenience methods for common operations

    def log_claim(
        self,
        task_id: str,
        domain: str,
        success: bool,
        error: Optional[Exception] = None
    ) -> None:
        """Log task claim operation."""
        self.log(
            level=LogLevel.INFO if success else LogLevel.ERROR,
            operation=OperationType.CLAIM_TASK,
            message=f"{'Claimed' if success else 'Failed to claim'} task {task_id}",
            metadata={"task_id": task_id, "domain": domain, "success": success},
            error=error
        )

    def log_release(
        self,
        task_id: str,
        completed: bool,
        success: bool,
        error: Optional[Exception] = None
    ) -> None:
        """Log task release operation."""
        self.log(
            level=LogLevel.INFO if success else LogLevel.ERROR,
            operation=OperationType.RELEASE_TASK,
            message=f"{'Released' if success else 'Failed to release'} task {task_id}",
            metadata={"task_id": task_id, "completed": completed, "success": success},
            error=error
        )

    def log_sync(
        self,
        sync_type: str,
        success: bool,
        duration_seconds: float,
        error: Optional[Exception] = None
    ) -> None:
        """Log vault sync operation."""
        self.log(
            level=LogLevel.INFO if success else LogLevel.WARNING,
            operation=OperationType.SYNC_VAULT,
            message=f"Vault sync {sync_type} {'succeeded' if success else 'failed'}",
            metadata={
                "sync_type": sync_type,
                "success": success,
                "duration_seconds": duration_seconds
            },
            error=error
        )

    def log_conflict(
        self,
        file_path: str,
        resolution_strategy: str,
        success: bool,
        error: Optional[Exception] = None
    ) -> None:
        """Log conflict resolution operation."""
        self.log(
            level=LogLevel.WARNING if success else LogLevel.ERROR,
            operation=OperationType.RESOLVE_CONFLICT,
            message=f"Conflict in {file_path} {'resolved' if success else 'failed'}",
            metadata={
                "file_path": file_path,
                "resolution_strategy": resolution_strategy,
                "success": success
            },
            error=error
        )

    def log_draft_generation(
        self,
        draft_id: str,
        draft_type: str,
        success: bool,
        duration_seconds: float,
        error: Optional[Exception] = None
    ) -> None:
        """Log draft generation operation."""
        self.log(
            level=LogLevel.INFO if success else LogLevel.ERROR,
            operation=OperationType.GENERATE_DRAFT,
            message=f"Generated {draft_type} draft {draft_id}",
            metadata={
                "draft_id": draft_id,
                "draft_type": draft_type,
                "success": success,
                "duration_seconds": duration_seconds
            },
            error=error
        )

    def log_approval(
        self,
        draft_id: str,
        approval_status: str,
        success: bool,
        error: Optional[Exception] = None
    ) -> None:
        """Log approval processing operation."""
        self.log(
            level=LogLevel.INFO if success else LogLevel.ERROR,
            operation=OperationType.PROCESS_APPROVAL,
            message=f"Processed approval for {draft_id}: {approval_status}",
            metadata={
                "draft_id": draft_id,
                "approval_status": approval_status,
                "success": success
            },
            error=error
        )

    def log_action_execution(
        self,
        action_type: str,
        action_id: str,
        success: bool,
        duration_seconds: float,
        error: Optional[Exception] = None
    ) -> None:
        """Log action execution operation."""
        self.log(
            level=LogLevel.INFO if success else LogLevel.ERROR,
            operation=OperationType.EXECUTE_ACTION,
            message=f"Executed {action_type} action {action_id}",
            metadata={
                "action_type": action_type,
                "action_id": action_id,
                "success": success,
                "duration_seconds": duration_seconds
            },
            error=error
        )

    def log_health_check(
        self,
        service_type: str,
        status: str,
        response_time_seconds: Optional[float] = None,
        error: Optional[Exception] = None
    ) -> None:
        """Log health check operation."""
        self.log(
            level=LogLevel.INFO if status == "healthy" else LogLevel.WARNING,
            operation=OperationType.HEALTH_CHECK,
            message=f"Health check for {service_type}: {status}",
            metadata={
                "service_type": service_type,
                "status": status,
                "response_time_seconds": response_time_seconds
            },
            error=error
        )

    def log_alert(
        self,
        alert_type: str,
        service_type: str,
        channels: list,
        success: bool,
        error: Optional[Exception] = None
    ) -> None:
        """Log alert sent operation."""
        self.log(
            level=LogLevel.WARNING if success else LogLevel.ERROR,
            operation=OperationType.ALERT_SENT,
            message=f"Alert sent for {service_type} via {', '.join(channels)}",
            metadata={
                "alert_type": alert_type,
                "service_type": service_type,
                "channels": channels,
                "success": success
            },
            error=error
        )

    def log_recovery(
        self,
        service_type: str,
        recovery_action: str,
        success: bool,
        error: Optional[Exception] = None
    ) -> None:
        """Log recovery action operation."""
        self.log(
            level=LogLevel.INFO if success else LogLevel.ERROR,
            operation=OperationType.RECOVERY_ACTION,
            message=f"Recovery action {recovery_action} for {service_type}",
            metadata={
                "service_type": service_type,
                "recovery_action": recovery_action,
                "success": success
            },
            error=error
        )


class LogAnalyzer:
    """
    Analyzes structured logs for patterns and metrics.

    Useful for debugging and performance analysis.
    """

    def __init__(self, log_file: Path):
        """
        Initialize log analyzer.

        Args:
            log_file: Path to JSON log file
        """
        self.log_file = Path(log_file)

    def get_operation_stats(self, operation: OperationType) -> Dict:
        """
        Get statistics for a specific operation type.

        Args:
            operation: Operation type to analyze

        Returns:
            Dict with count, success rate, avg duration
        """
        entries = self._read_log_entries()
        filtered = [e for e in entries if e.get("operation") == operation.value]

        if not filtered:
            return {"count": 0, "success_rate": 0, "avg_duration": 0}

        total = len(filtered)
        successful = sum(1 for e in filtered if e.get("metadata", {}).get("success", False))
        durations = [
            e.get("metadata", {}).get("duration_seconds", 0)
            for e in filtered
            if "duration_seconds" in e.get("metadata", {})
        ]

        return {
            "count": total,
            "success_rate": (successful / total * 100) if total > 0 else 0,
            "avg_duration": sum(durations) / len(durations) if durations else 0
        }

    def get_error_summary(self, hours: int = 24) -> List[Dict]:
        """
        Get summary of errors in last N hours.

        Args:
            hours: Number of hours to look back

        Returns:
            List of error entries
        """
        entries = self._read_log_entries()
        cutoff = datetime.now() - timedelta(hours=hours)

        errors = [
            e for e in entries
            if e.get("level") in ["error", "critical"]
            and datetime.fromisoformat(e.get("wall_clock_time", "")) >= cutoff
        ]

        return errors

    def _read_log_entries(self) -> List[Dict]:
        """Read all log entries from file."""
        entries = []

        if not self.log_file.exists():
            return entries

        try:
            with open(self.log_file, 'r') as f:
                for line in f:
                    try:
                        entries.append(json.loads(line.strip()))
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"Error reading log file: {e}")

        return entries
