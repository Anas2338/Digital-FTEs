"""
Circuit Breaker Pattern Implementation for Digital FTE

Implements the circuit breaker pattern to prevent cascading failures when
external integrations (Odoo, social media APIs) become unavailable.

States:
- CLOSED: Normal operation, requests pass through
- OPEN: Integration is failing, requests are blocked
- HALF_OPEN: Testing if integration has recovered

Recovery Schedule:
- Exponential backoff: 5min, 10min, 20min, then hourly
- Health checks determine when to transition from OPEN to HALF_OPEN

Domain Context Integration:
- Tracks circuit breaker state per domain (personal/business)
- Enables domain-specific error tracking and recovery
"""

from enum import Enum
from datetime import datetime, timedelta
from typing import Optional, Callable, Any
import logging


logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, blocking requests
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreaker:
    """
    Circuit breaker for external service integrations with domain context support.

    Prevents repeated calls to failing services and implements
    exponential backoff recovery with health checks.
    """

    def __init__(
        self,
        integration_name: str,
        failure_threshold: float = 0.20,  # 20% error rate triggers OPEN
        success_threshold: int = 2,  # 2 successful calls to close circuit
        timeout_seconds: int = 30,  # Request timeout
        domain_context: Optional[str] = None  # Domain context (personal/business)
    ):
        """
        Initialize circuit breaker.

        Args:
            integration_name: Name of the integration (e.g., "odoo", "facebook")
            failure_threshold: Error rate (0.0-1.0) that triggers OPEN state
            success_threshold: Consecutive successes needed to close circuit
            timeout_seconds: Request timeout in seconds
            domain_context: Domain context for this circuit breaker
        """
        self.integration_name = integration_name
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout_seconds = timeout_seconds
        self.domain_context = domain_context

        # State tracking
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.total_requests = 0
        self.consecutive_successes = 0

        # Recovery tracking
        self.recovery_attempt = 0
        self.opened_at: Optional[datetime] = None
        self.next_retry_at: Optional[datetime] = None

        # Exponential backoff schedule (minutes)
        self.backoff_schedule = [5, 10, 20, 60]  # 5min, 10min, 20min, hourly

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function through the circuit breaker.

        Args:
            func: Function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Result of func execution

        Raises:
            CircuitBreakerOpenError: If circuit is OPEN and retry time not reached
            Exception: Any exception raised by func
        """
        # Check if circuit is OPEN
        if self.state == CircuitState.OPEN:
            if not self._should_attempt_reset():
                raise CircuitBreakerOpenError(
                    f"Circuit breaker OPEN for {self.integration_name}. "
                    f"Next retry at {self.next_retry_at}"
                )
            # Transition to HALF_OPEN for testing
            self._transition_to_half_open()

        # Execute the function
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure(e)
            raise

    def _on_success(self):
        """Handle successful request."""
        self.success_count += 1
        self.total_requests += 1
        self.consecutive_successes += 1

        logger.debug(
            f"Circuit breaker success for {self.integration_name}: "
            f"{self.consecutive_successes} consecutive successes"
        )

        # If in HALF_OPEN, check if we should close the circuit
        if self.state == CircuitState.HALF_OPEN:
            if self.consecutive_successes >= self.success_threshold:
                self._transition_to_closed()

    def _on_failure(self, exception: Exception):
        """Handle failed request."""
        self.failure_count += 1
        self.total_requests += 1
        self.consecutive_successes = 0

        logger.warning(
            f"Circuit breaker failure for {self.integration_name}: {exception}"
        )

        # Calculate error rate
        error_rate = self.failure_count / self.total_requests if self.total_requests > 0 else 0

        # If in HALF_OPEN, immediately open circuit on failure
        if self.state == CircuitState.HALF_OPEN:
            self._transition_to_open()
        # If error rate exceeds threshold, open circuit
        elif error_rate >= self.failure_threshold and self.total_requests >= 5:
            self._transition_to_open()

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.next_retry_at is None:
            return True
        return datetime.now() >= self.next_retry_at

    def _transition_to_open(self):
        """Transition circuit to OPEN state."""
        self.state = CircuitState.OPEN
        self.opened_at = datetime.now()
        self.recovery_attempt += 1

        # Calculate next retry time using exponential backoff
        backoff_minutes = self._get_backoff_minutes()
        self.next_retry_at = datetime.now() + timedelta(minutes=backoff_minutes)

        logger.error(
            f"Circuit breaker OPEN for {self.integration_name}. "
            f"Recovery attempt {self.recovery_attempt}. "
            f"Next retry at {self.next_retry_at} ({backoff_minutes} minutes)"
        )

    def _transition_to_half_open(self):
        """Transition circuit to HALF_OPEN state for testing."""
        self.state = CircuitState.HALF_OPEN
        self.consecutive_successes = 0

        logger.info(
            f"Circuit breaker HALF_OPEN for {self.integration_name}. "
            f"Testing recovery (attempt {self.recovery_attempt})"
        )

    def _transition_to_closed(self):
        """Transition circuit to CLOSED state (normal operation)."""
        self.state = CircuitState.CLOSED
        self.recovery_attempt = 0
        self.opened_at = None
        self.next_retry_at = None

        logger.info(
            f"Circuit breaker CLOSED for {self.integration_name}. "
            f"Service recovered. Resetting counters."
        )

        # Reset counters for fresh start
        self.failure_count = 0
        self.success_count = 0
        self.total_requests = 0
        self.consecutive_successes = 0

    def _get_backoff_minutes(self) -> int:
        """
        Get backoff time in minutes based on recovery attempt.

        Returns:
            Backoff time in minutes (5, 10, 20, or 60)
        """
        # Use exponential backoff schedule, capping at hourly
        index = min(self.recovery_attempt - 1, len(self.backoff_schedule) - 1)
        return self.backoff_schedule[index]

    def get_status(self) -> dict:
        """
        Get current circuit breaker status.

        Returns:
            Dictionary with status information
        """
        error_rate = self.failure_count / self.total_requests if self.total_requests > 0 else 0

        return {
            "integration_name": self.integration_name,
            "state": self.state.value,
            "error_rate": error_rate,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "total_requests": self.total_requests,
            "consecutive_successes": self.consecutive_successes,
            "recovery_attempt": self.recovery_attempt,
            "opened_at": self.opened_at.isoformat() if self.opened_at else None,
            "next_retry_at": self.next_retry_at.isoformat() if self.next_retry_at else None,
        }

    def reset(self):
        """Manually reset circuit breaker to CLOSED state."""
        logger.info(f"Manually resetting circuit breaker for {self.integration_name}")
        self._transition_to_closed()


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is OPEN and blocking requests."""
    pass
