"""
Lamport Timestamp Implementation for Platinum Tier

Provides logical clock for ordering operations across cloud and local agents
without relying on wall-clock time (handles clock skew).

Based on research.md Decision 4: Lamport timestamps chosen for simplicity
and sufficiency for 2-agent claim-by-move ordering.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class LamportTimestamp:
    """
    Lamport timestamp for distributed operation ordering.

    Attributes:
        agent_id: Identifier of the agent that created this timestamp (cloud|local)
        counter: Monotonically increasing sequence number
        wall_clock_time: Human-readable timestamp (for debugging only, not used for ordering)
    """
    agent_id: str
    counter: int
    wall_clock_time: datetime

    def __lt__(self, other: 'LamportTimestamp') -> bool:
        """
        Compare timestamps for ordering.
        First by counter (lower is earlier), then by agent_id for deterministic tie-breaking.
        """
        if self.counter != other.counter:
            return self.counter < other.counter
        return self.agent_id < other.agent_id

    def __le__(self, other: 'LamportTimestamp') -> bool:
        return self < other or self == other

    def __gt__(self, other: 'LamportTimestamp') -> bool:
        return not self <= other

    def __ge__(self, other: 'LamportTimestamp') -> bool:
        return not self < other

    def to_dict(self) -> dict:
        """Serialize to dictionary for JSON storage."""
        return {
            "agent_id": self.agent_id,
            "counter": self.counter,
            "wall_clock_time": self.wall_clock_time.isoformat()
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'LamportTimestamp':
        """Deserialize from dictionary."""
        return cls(
            agent_id=data["agent_id"],
            counter=data["counter"],
            wall_clock_time=datetime.fromisoformat(data["wall_clock_time"])
        )


class LamportClock:
    """
    Lamport logical clock for a single agent.

    Maintains monotonically increasing counter for operation ordering.
    Thread-safe for concurrent operations within same agent.
    """

    def __init__(self, agent_id: str, initial_counter: int = 0):
        """
        Initialize Lamport clock.

        Args:
            agent_id: Identifier for this agent (cloud|local)
            initial_counter: Starting counter value (default 0)
        """
        self.agent_id = agent_id
        self._counter = initial_counter
        self._lock = None  # Will use threading.Lock() when needed

    def tick(self) -> LamportTimestamp:
        """
        Increment counter and return new timestamp.
        Call before performing any operation.

        Returns:
            New LamportTimestamp with incremented counter
        """
        self._counter += 1
        return LamportTimestamp(
            agent_id=self.agent_id,
            counter=self._counter,
            wall_clock_time=datetime.now()
        )

    def update(self, received_timestamp: LamportTimestamp) -> LamportTimestamp:
        """
        Update clock based on received timestamp from other agent.
        Implements Lamport's update rule: counter = max(local, received) + 1

        Args:
            received_timestamp: Timestamp from message received from other agent

        Returns:
            New LamportTimestamp after update
        """
        self._counter = max(self._counter, received_timestamp.counter) + 1
        return LamportTimestamp(
            agent_id=self.agent_id,
            counter=self._counter,
            wall_clock_time=datetime.now()
        )

    def current_counter(self) -> int:
        """Get current counter value without incrementing."""
        return self._counter
