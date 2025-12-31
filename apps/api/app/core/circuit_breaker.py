"""
Circuit Breaker Pattern Implementation.

Protects against cascading failures when external services are down.
Implements the standard circuit breaker states:
- CLOSED: Normal operation, requests pass through
- OPEN: Service is failing, requests are rejected immediately
- HALF_OPEN: Testing if service has recovered

Usage:
    breaker = CircuitBreaker(name="copernicus", failure_threshold=5)

    try:
        result = await breaker.call(service.fetch_data, lat, lon)
    except CircuitOpenError:
        # Use fallback
        result = await fallback_service.fetch_data(lat, lon)
"""

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, TypeVar

from app.core.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"       # Normal, allowing requests
    OPEN = "open"          # Failing, rejecting requests
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitOpenError(Exception):
    """Raised when circuit is open and request is rejected."""

    def __init__(self, breaker_name: str, retry_after: int):
        self.breaker_name = breaker_name
        self.retry_after = retry_after
        super().__init__(
            f"Circuit breaker '{breaker_name}' is OPEN. Retry after {retry_after}s"
        )


@dataclass
class CircuitBreakerMetrics:
    """Metrics for circuit breaker monitoring."""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    rejected_requests: int = 0  # Rejected due to open circuit
    state_changes: int = 0
    last_state_change: datetime | None = None
    last_failure: datetime | None = None
    last_success: datetime | None = None

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_requests == 0:
            return 1.0
        return self.successful_requests / self.total_requests

    def to_dict(self) -> dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "rejected_requests": self.rejected_requests,
            "success_rate": round(self.success_rate * 100, 2),
            "state_changes": self.state_changes,
            "last_failure": self.last_failure.isoformat() if self.last_failure else None,
            "last_success": self.last_success.isoformat() if self.last_success else None,
        }


@dataclass
class CircuitBreaker:
    """
    Circuit Breaker implementation for protecting external service calls.

    Features:
    - Automatic state transitions based on failure threshold
    - Recovery timeout for testing service availability
    - Metrics collection for monitoring
    - Thread-safe operation using asyncio locks

    Attributes:
        name: Identifier for this circuit breaker
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Seconds to wait before attempting recovery
        half_open_max_calls: Number of test calls allowed in half-open state
    """

    name: str
    failure_threshold: int = field(
        default_factory=lambda: settings.CIRCUIT_FAILURE_THRESHOLD
    )
    recovery_timeout: int = field(
        default_factory=lambda: settings.CIRCUIT_RECOVERY_TIMEOUT
    )
    half_open_max_calls: int = field(
        default_factory=lambda: settings.CIRCUIT_HALF_OPEN_MAX_CALLS
    )

    # Internal state
    _state: CircuitState = field(default=CircuitState.CLOSED, init=False)
    _failure_count: int = field(default=0, init=False)
    _last_failure_time: datetime | None = field(default=None, init=False)
    _half_open_calls: int = field(default=0, init=False)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False)
    _metrics: CircuitBreakerMetrics = field(
        default_factory=CircuitBreakerMetrics, init=False
    )

    @property
    def state(self) -> CircuitState:
        """Current circuit state."""
        return self._state

    @property
    def metrics(self) -> CircuitBreakerMetrics:
        """Access metrics."""
        return self._metrics

    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed (normal operation)."""
        return self._state == CircuitState.CLOSED

    @property
    def is_open(self) -> bool:
        """Check if circuit is open (rejecting requests)."""
        return self._state == CircuitState.OPEN

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self._last_failure_time is None:
            return True

        elapsed = datetime.now() - self._last_failure_time
        return elapsed > timedelta(seconds=self.recovery_timeout)

    def _transition_to(self, new_state: CircuitState) -> None:
        """Transition to a new state with logging."""
        if self._state != new_state:
            old_state = self._state
            self._state = new_state
            self._metrics.state_changes += 1
            self._metrics.last_state_change = datetime.now()

            logger.warning(
                f"Circuit breaker '{self.name}' transitioned: "
                f"{old_state.value} -> {new_state.value}"
            )

    def _on_success(self) -> None:
        """Handle successful call."""
        self._metrics.total_requests += 1
        self._metrics.successful_requests += 1
        self._metrics.last_success = datetime.now()

        if self._state == CircuitState.HALF_OPEN:
            self._half_open_calls += 1

            if self._half_open_calls >= self.half_open_max_calls:
                # Service recovered, close circuit
                self._transition_to(CircuitState.CLOSED)
                self._failure_count = 0
                logger.info(f"Circuit breaker '{self.name}' recovered, now CLOSED")

        elif self._state == CircuitState.CLOSED:
            # Reset failure count on success
            self._failure_count = 0

    def _on_failure(self, error: Exception) -> None:
        """Handle failed call."""
        self._metrics.total_requests += 1
        self._metrics.failed_requests += 1
        self._failure_count += 1
        self._last_failure_time = datetime.now()
        self._metrics.last_failure = self._last_failure_time

        logger.warning(
            f"Circuit breaker '{self.name}' failure #{self._failure_count}: {error}"
        )

        if self._state == CircuitState.HALF_OPEN:
            # Failure during recovery test, back to open
            self._transition_to(CircuitState.OPEN)
            logger.warning(f"Circuit breaker '{self.name}' recovery failed, back to OPEN")

        elif self._failure_count >= self.failure_threshold:
            # Threshold exceeded, open circuit
            self._transition_to(CircuitState.OPEN)
            logger.error(
                f"Circuit breaker '{self.name}' OPENED after "
                f"{self._failure_count} failures"
            )

    async def call(
        self,
        func: Callable[..., T],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """
        Execute function with circuit breaker protection.

        Args:
            func: Async function to call
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Result from func

        Raises:
            CircuitOpenError: If circuit is open
            Exception: Original exception if func fails
        """
        async with self._lock:
            # Check if circuit is open
            if self._state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    # Try to recover
                    self._transition_to(CircuitState.HALF_OPEN)
                    self._half_open_calls = 0
                    logger.info(
                        f"Circuit breaker '{self.name}' attempting recovery (HALF_OPEN)"
                    )
                else:
                    # Still in cooldown
                    self._metrics.rejected_requests += 1
                    retry_after = self.recovery_timeout - int(
                        (datetime.now() - self._last_failure_time).total_seconds()
                    )
                    raise CircuitOpenError(self.name, max(1, retry_after))

        # Execute the function
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            async with self._lock:
                self._on_success()

            return result

        except Exception as e:
            async with self._lock:
                self._on_failure(e)
            raise

    def reset(self) -> None:
        """Manually reset the circuit breaker to closed state."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._half_open_calls = 0
        self._last_failure_time = None
        logger.info(f"Circuit breaker '{self.name}' manually reset to CLOSED")

    def get_status(self) -> dict[str, Any]:
        """Get current status of the circuit breaker."""
        return {
            "name": self.name,
            "state": self._state.value,
            "failure_count": self._failure_count,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
            "metrics": self._metrics.to_dict(),
        }


# ===========================================
# Pre-configured Circuit Breakers
# ===========================================

# Circuit breaker for Copernicus API
copernicus_breaker = CircuitBreaker(
    name="copernicus",
    failure_threshold=5,
    recovery_timeout=60,
    half_open_max_calls=2,
)

# Circuit breaker for PVGIS API
pvgis_breaker = CircuitBreaker(
    name="pvgis",
    failure_threshold=3,
    recovery_timeout=30,
    half_open_max_calls=3,
)

# Circuit breaker for Gemini AI
gemini_breaker = CircuitBreaker(
    name="gemini",
    failure_threshold=5,
    recovery_timeout=30,
    half_open_max_calls=2,
)


def get_all_breakers() -> dict[str, CircuitBreaker]:
    """Get all circuit breakers for monitoring."""
    return {
        "copernicus": copernicus_breaker,
        "pvgis": pvgis_breaker,
        "gemini": gemini_breaker,
    }

