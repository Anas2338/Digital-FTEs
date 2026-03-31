"""Rate limiter for MCP server tools using token bucket algorithm.

Enforces rate limits per tool:
- Gmail: 100 requests per day
- LinkedIn: 100 requests per day
- WhatsApp: 1000 requests per day
"""

from datetime import datetime, timedelta
from typing import Dict, Optional
import threading


class TokenBucket:
    """Token bucket for rate limiting."""

    def __init__(self, capacity: int, refill_rate: float):
        """Initialize token bucket.

        Args:
            capacity: Maximum number of tokens (requests per period)
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.last_refill = datetime.utcnow()
        self.lock = threading.Lock()

    def consume(self, tokens: int = 1) -> bool:
        """Attempt to consume tokens.

        Args:
            tokens: Number of tokens to consume

        Returns:
            True if tokens consumed, False if insufficient tokens
        """
        with self.lock:
            self._refill()

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    def _refill(self):
        """Refill tokens based on elapsed time."""
        now = datetime.utcnow()
        elapsed = (now - self.last_refill).total_seconds()
        tokens_to_add = elapsed * self.refill_rate

        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now

    def get_available_tokens(self) -> int:
        """Get number of available tokens.

        Returns:
            Number of available tokens
        """
        with self.lock:
            self._refill()
            return int(self.tokens)

    def get_retry_after(self) -> int:
        """Get seconds until next token available.

        Returns:
            Seconds to wait
        """
        with self.lock:
            self._refill()
            if self.tokens >= 1:
                return 0

            tokens_needed = 1 - self.tokens
            seconds = tokens_needed / self.refill_rate
            return int(seconds) + 1


class RateLimiter:
    """Rate limiter for MCP server tools."""

    def __init__(self):
        """Initialize rate limiter with tool-specific limits."""
        # Rate limits: (capacity, period_seconds)
        self.limits = {
            "send-email": (100, 86400),      # 100 per day
            "linkedin-post": (100, 86400),   # 100 per day
            "whatsapp-send": (1000, 86400),  # 1000 per day
        }

        # Create token buckets
        self.buckets: Dict[str, TokenBucket] = {}
        for tool, (capacity, period) in self.limits.items():
            refill_rate = capacity / period  # tokens per second
            self.buckets[tool] = TokenBucket(capacity, refill_rate)

    def check_rate_limit(self, tool: str) -> tuple[bool, Optional[int]]:
        """Check if request is within rate limit.

        Args:
            tool: Tool name

        Returns:
            Tuple of (allowed, retry_after_seconds)
        """
        if tool not in self.buckets:
            # Unknown tool, allow by default
            return True, None

        bucket = self.buckets[tool]
        if bucket.consume():
            return True, None
        else:
            retry_after = bucket.get_retry_after()
            return False, retry_after

    def get_remaining(self, tool: str) -> Optional[int]:
        """Get remaining requests for a tool.

        Args:
            tool: Tool name

        Returns:
            Number of remaining requests or None if tool unknown
        """
        if tool not in self.buckets:
            return None

        return self.buckets[tool].get_available_tokens()

    def get_limit(self, tool: str) -> Optional[int]:
        """Get rate limit capacity for a tool.

        Args:
            tool: Tool name

        Returns:
            Rate limit capacity or None if tool unknown
        """
        if tool not in self.limits:
            return None

        return self.limits[tool][0]

    def reset(self, tool: str):
        """Reset rate limit for a tool (for testing).

        Args:
            tool: Tool name
        """
        if tool in self.buckets:
            capacity = self.limits[tool][0]
            self.buckets[tool].tokens = capacity
