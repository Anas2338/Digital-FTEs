"""
Error Handling Module

Provides error detection and retry logic with exponential backoff for Gmail API operations.
"""

import time
from typing import Callable, Any, Optional
from googleapiclient.errors import HttpError


class GmailErrorHandler:
    """Handler for Gmail API errors with retry logic."""

    @staticmethod
    def is_transient_error(error: Exception) -> bool:
        """
        Determine if an error is transient and should be retried.

        Args:
            error: Exception to check

        Returns:
            True if error is transient, False otherwise
        """
        # Network errors
        if isinstance(error, (ConnectionError, TimeoutError)):
            return True

        # HTTP errors from Gmail API
        if isinstance(error, HttpError):
            status_code = error.resp.status
            # Transient HTTP status codes
            transient_codes = [429, 500, 502, 503, 504]
            return status_code in transient_codes

        return False

    @staticmethod
    def exponential_backoff_retry(
        func: Callable,
        *args,
        max_retries: int = 3,
        base_delay: float = 1.0,
        **kwargs
    ) -> Any:
        """
        Execute function with exponential backoff retry on transient errors.

        Args:
            func: Function to execute
            *args: Positional arguments for func
            max_retries: Maximum number of retry attempts (default: 3)
            base_delay: Base delay in seconds (default: 1.0)
            **kwargs: Keyword arguments for func

        Returns:
            Result from successful function execution

        Raises:
            Exception: If all retries exhausted or non-transient error
        """
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)

            except Exception as e:
                last_error = e

                # Check if error is transient
                if not GmailErrorHandler.is_transient_error(e):
                    # Non-transient error, don't retry
                    raise

                # Last attempt exhausted
                if attempt == max_retries:
                    raise Exception(
                        f"Max retries ({max_retries}) exhausted. Last error: {e}"
                    )

                # Calculate delay: 1s, 2s, 4s
                delay = base_delay * (2 ** attempt)
                print(f"[WARN] Transient error (attempt {attempt + 1}/{max_retries + 1}): {e}")
                print(f"[INFO] Retrying in {delay}s...")
                time.sleep(delay)

        # Should not reach here, but raise last error if it does
        raise last_error


def retry_on_transient_error(max_retries: int = 3, base_delay: float = 1.0):
    """
    Decorator for automatic retry with exponential backoff on transient errors.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds

    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            return GmailErrorHandler.exponential_backoff_retry(
                func,
                *args,
                max_retries=max_retries,
                base_delay=base_delay,
                **kwargs
            )
        return wrapper
    return decorator
