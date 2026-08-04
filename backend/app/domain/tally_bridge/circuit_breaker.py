import time
from app.domain.tally_bridge.models import CircuitBreakerState


class ExponentialBackoffCircuitBreaker:
    """Protects legacy Tally XML server from overload during outages."""

    def __init__(self, failure_threshold: int = 3, cooldown_seconds: int = 60):
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED
        self.last_failure_time = 0.0

    def can_execute(self) -> bool:
        """Check if we are allowed to send an HTTP request to Tally port 9000."""
        now = time.time()
        if self.state == CircuitBreakerState.OPEN:
            if now - self.last_failure_time > self.cooldown_seconds:
                # Cooldown expired -> let's test one request!
                self.state = CircuitBreakerState.HALF_OPEN
                return True
            return False  # Still cooling down; trip circuit
        return True

    def record_success(self):
        """Tally answered! Reset failures and close circuit."""
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED

    def record_failure(self):
        """Tally crashed or timed out."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN