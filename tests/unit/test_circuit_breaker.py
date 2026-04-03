"""Unit tests for CircuitBreaker class.

Tests circuit breaker state transitions, failure tracking, and recovery logic.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mcp_servers.digital_fte_server.circuit_breaker import CircuitBreaker
from watchers.shared.database import Database


class TestCircuitBreaker:
    """Test suite for CircuitBreaker class."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create temporary database for testing."""
        db_path = tmp_path / "test.db"
        return Database(str(db_path))

    @pytest.fixture
    def circuit_breaker(self, db):
        """Create circuit breaker instance."""
        return CircuitBreaker(name="test_integration", db=db)

    def test_initial_state_is_closed(self, circuit_breaker):
        """Test that circuit breaker starts in CLOSED state."""
        assert circuit_breaker.get_state() == "CLOSED"
        assert circuit_breaker.can_execute() is True

    def test_record_success_keeps_circuit_closed(self, circuit_breaker):
        """Test that successful calls keep circuit closed."""
        circuit_breaker.record_success()
        assert circuit_breaker.get_state() == "CLOSED"
        assert circuit_breaker.can_execute() is True

    def test_record_failure_increments_error_count(self, circuit_breaker):
        """Test that failures increment error count."""
        initial_errors = circuit_breaker.error_count
        circuit_breaker.record_failure()
        assert circuit_breaker.error_count == initial_errors + 1

    def test_circuit_opens_after_threshold_failures(self, circuit_breaker):
        """Test that circuit opens after exceeding failure threshold."""
        # Record enough failures to exceed threshold (20% error rate)
        for _ in range(10):
            circuit_breaker.record_success()

        for _ in range(3):
            circuit_breaker.record_failure()

        # Error rate should be 3/13 = 23% > 20% threshold
        assert circuit_breaker.get_state() == "OPEN"
        assert circuit_breaker.can_execute() is False

    def test_circuit_transitions_to_half_open_after_timeout(self, circuit_breaker):
        """Test that circuit transitions to HALF_OPEN after recovery timeout."""
        # Open the circuit
        for _ in range(3):
            circuit_breaker.record_failure()

        assert circuit_breaker.get_state() == "OPEN"

        # Simulate time passing (mock next_recovery_at to be in the past)
        circuit_breaker.next_recovery_at = datetime.utcnow() - timedelta(seconds=1)

        # Circuit should allow execution in HALF_OPEN state
        assert circuit_breaker.can_execute() is True

    def test_half_open_success_closes_circuit(self, circuit_breaker):
        """Test that success in HALF_OPEN state closes circuit."""
        # Open the circuit
        for _ in range(3):
            circuit_breaker.record_failure()

        # Transition to HALF_OPEN
        circuit_breaker.next_recovery_at = datetime.utcnow() - timedelta(seconds=1)
        circuit_breaker.can_execute()

        # Record success should close circuit
        circuit_breaker.record_success()
        assert circuit_breaker.get_state() == "CLOSED"

    def test_half_open_failure_reopens_circuit(self, circuit_breaker):
        """Test that failure in HALF_OPEN state reopens circuit."""
        # Open the circuit
        for _ in range(3):
            circuit_breaker.record_failure()

        # Transition to HALF_OPEN
        circuit_breaker.next_recovery_at = datetime.utcnow() - timedelta(seconds=1)
        circuit_breaker.can_execute()

        # Record failure should reopen circuit
        circuit_breaker.record_failure()
        assert circuit_breaker.get_state() == "OPEN"

    def test_exponential_backoff_recovery_schedule(self, circuit_breaker):
        """Test that recovery attempts use exponential backoff."""
        # Open circuit
        for _ in range(3):
            circuit_breaker.record_failure()

        first_recovery = circuit_breaker.next_recovery_at

        # Fail recovery attempt
        circuit_breaker.next_recovery_at = datetime.utcnow() - timedelta(seconds=1)
        circuit_breaker.can_execute()
        circuit_breaker.record_failure()

        second_recovery = circuit_breaker.next_recovery_at

        # Second recovery should be later than first (exponential backoff)
        assert second_recovery > first_recovery

    def test_error_rate_calculation(self, circuit_breaker):
        """Test that error rate is calculated correctly."""
        # 2 successes, 1 failure = 33% error rate
        circuit_breaker.record_success()
        circuit_breaker.record_success()
        circuit_breaker.record_failure()

        error_rate = circuit_breaker.get_error_rate()
        assert abs(error_rate - 0.333) < 0.01

    def test_reset_circuit_breaker(self, circuit_breaker):
        """Test manual circuit breaker reset."""
        # Open circuit
        for _ in range(3):
            circuit_breaker.record_failure()

        assert circuit_breaker.get_state() == "OPEN"

        # Reset circuit
        circuit_breaker.reset()

        assert circuit_breaker.get_state() == "CLOSED"
        assert circuit_breaker.error_count == 0
        assert circuit_breaker.success_count == 0

    def test_circuit_breaker_persistence(self, db):
        """Test that circuit breaker state persists to database."""
        cb1 = CircuitBreaker(name="test_persist", db=db)

        # Record some failures
        for _ in range(3):
            cb1.record_failure()

        # Create new instance with same name
        cb2 = CircuitBreaker(name="test_persist", db=db)

        # State should be loaded from database
        assert cb2.get_state() == "OPEN"
        assert cb2.error_count == 3
