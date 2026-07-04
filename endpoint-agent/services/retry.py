"""
KOVIRX Endpoint Agent — Retry Engine.

Exponential backoff retry engine with jitter for resilient
network communication. Prevents thundering herd on backend recovery.
"""

import logging
import random
import time
from typing import Callable, TypeVar

logger = logging.getLogger("kovirx.agent.retry")

T = TypeVar("T")


class RetryExhausted(Exception):
    """Raised when all retry attempts have been exhausted."""
    pass


def retry_with_backoff(
    func: Callable[[], T],
    max_attempts: int = 5,
    backoff_base: float = 2.0,
    backoff_max: float = 60.0,
    jitter: bool = True,
    on_retry: Callable[[int, Exception], None] | None = None,
) -> T:
    """
    Execute a function with exponential backoff retry.

    Args:
        func: Callable to execute (should raise on failure)
        max_attempts: Maximum number of attempts
        backoff_base: Base delay in seconds (doubles each attempt)
        backoff_max: Maximum delay cap in seconds
        jitter: Add random jitter to prevent thundering herd
        on_retry: Optional callback on each retry (attempt_num, exception)

    Returns:
        Result of successful function call

    Raises:
        RetryExhausted: If all attempts fail
    """
    last_exception: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            return func()
        except Exception as e:
            last_exception = e

            if attempt >= max_attempts:
                logger.error(
                    "All %d retry attempts exhausted. Last error: %s",
                    max_attempts, e,
                )
                raise RetryExhausted(
                    f"Failed after {max_attempts} attempts: {e}"
                ) from e

            # Calculate delay with exponential backoff
            delay = min(backoff_base ** (attempt - 1), backoff_max)
            if jitter:
                delay = delay * (0.5 + random.random())

            logger.warning(
                "Attempt %d/%d failed: %s. Retrying in %.1fs...",
                attempt, max_attempts, e, delay,
            )

            if on_retry:
                on_retry(attempt, e)

            time.sleep(delay)

    # Should not reach here, but satisfy type checker
    raise RetryExhausted(f"Failed after {max_attempts} attempts: {last_exception}")


class RetryPolicy:
    """
    Configurable retry policy that can be shared across multiple operations.

    Usage:
        policy = RetryPolicy(max_attempts=3, backoff_base=1.0)
        result = policy.execute(lambda: api_client.post("/telemetry", data))
    """

    def __init__(
        self,
        max_attempts: int = 5,
        backoff_base: float = 2.0,
        backoff_max: float = 60.0,
        jitter: bool = True,
    ):
        self.max_attempts = max_attempts
        self.backoff_base = backoff_base
        self.backoff_max = backoff_max
        self.jitter = jitter
        self.total_retries: int = 0
        self.total_failures: int = 0

    def execute(self, func: Callable[[], T]) -> T:
        """Execute a function with this policy's retry settings."""
        try:
            return retry_with_backoff(
                func,
                max_attempts=self.max_attempts,
                backoff_base=self.backoff_base,
                backoff_max=self.backoff_max,
                jitter=self.jitter,
                on_retry=lambda attempt, _: setattr(
                    self, "total_retries", self.total_retries + 1
                ),
            )
        except RetryExhausted:
            self.total_failures += 1
            raise
