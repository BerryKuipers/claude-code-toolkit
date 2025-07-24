"""
Rate limiting module for Bitvavo API calls.

This module implements clean, testable rate limiting following Uncle Bob's principles:
- Single Responsibility: Only handles rate limiting
- Open/Closed: Extensible for different APIs
- Dependency Inversion: Abstract interface for different rate limiting strategies
"""

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Protocol

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RateLimitConfig:
    """Configuration for rate limiting behavior."""

    # Rate limit thresholds
    WARNING_THRESHOLD: int = 20
    CRITICAL_THRESHOLD: int = 5

    # Sleep durations (seconds)
    NORMAL_DELAY: float = 0.2
    WARNING_DELAY: float = 1.0
    CRITICAL_DELAY: float = 15.0
    FALLBACK_DELAY: float = 2.0

    # Retry configuration
    MAX_RETRIES: int = 3
    RETRY_BACKOFF: float = 2.0


class RateLimitClient(Protocol):
    """Protocol for clients that support rate limit checking."""

    def getRemainingLimit(self) -> str:
        """Get remaining rate limit as string."""
        ...


class RateLimitStrategy(ABC):
    """Abstract strategy for rate limiting."""

    @abstractmethod
    def should_delay(self, remaining_limit: int) -> bool:
        """Determine if we should delay based on remaining limit."""
        ...

    @abstractmethod
    def get_delay_duration(self, remaining_limit: int) -> float:
        """Get the delay duration for the given remaining limit."""
        ...


class ConservativeRateLimitStrategy(RateLimitStrategy):
    """Conservative rate limiting strategy that prioritizes API stability."""

    def __init__(self, config: RateLimitConfig = RateLimitConfig()):
        self.config = config

    def should_delay(self, remaining_limit: int) -> bool:
        """Always delay to be conservative."""
        return True

    def get_delay_duration(self, remaining_limit: int) -> float:
        """Get delay duration based on remaining limit."""
        if remaining_limit <= self.config.CRITICAL_THRESHOLD:
            return self.config.CRITICAL_DELAY
        elif remaining_limit <= self.config.WARNING_THRESHOLD:
            return self.config.WARNING_DELAY
        else:
            return self.config.NORMAL_DELAY


class AggressiveRateLimitStrategy(RateLimitStrategy):
    """Aggressive strategy that only delays when necessary."""

    def __init__(self, config: RateLimitConfig = RateLimitConfig()):
        self.config = config

    def should_delay(self, remaining_limit: int) -> bool:
        """Only delay when approaching limits."""
        return remaining_limit <= self.config.WARNING_THRESHOLD

    def get_delay_duration(self, remaining_limit: int) -> float:
        """Get delay duration based on remaining limit."""
        if remaining_limit <= self.config.CRITICAL_THRESHOLD:
            return self.config.CRITICAL_DELAY
        else:
            return self.config.WARNING_DELAY


class RateLimiter:
    """
    Clean, testable rate limiter following SOLID principles.

    Responsibilities:
    - Enforce rate limits before API calls
    - Handle rate limit errors gracefully
    - Provide configurable strategies
    """

    def __init__(
        self, strategy: RateLimitStrategy = None, config: RateLimitConfig = None
    ):
        self.strategy = strategy or ConservativeRateLimitStrategy()
        self.config = config or RateLimitConfig()

    def enforce_rate_limit(self, client: RateLimitClient) -> None:
        """
        Enforce rate limit before making API call.

        Args:
            client: Client that supports rate limit checking

        Raises:
            Exception: If rate limit cannot be determined after retries
        """
        try:
            remaining = self._get_remaining_limit(client)

            if self.strategy.should_delay(remaining):
                delay = self.strategy.get_delay_duration(remaining)
                self._log_rate_limit_action(remaining, delay)
                time.sleep(delay)

        except Exception as exc:
            logger.warning(f"Rate limit check failed: {exc}")
            self._handle_rate_limit_failure()

    def _get_remaining_limit(self, client: RateLimitClient) -> int:
        """Get remaining rate limit with error handling."""
        try:
            remaining_str = client.getRemainingLimit()
            return int(remaining_str)
        except (ValueError, TypeError) as exc:
            logger.error(f"Invalid rate limit response: {remaining_str}, error: {exc}")
            raise

    def _log_rate_limit_action(self, remaining: int, delay: float) -> None:
        """Log rate limiting action with appropriate level."""
        if remaining <= self.config.CRITICAL_THRESHOLD:
            logger.warning(
                f"CRITICAL: Rate limit very low ({remaining}), sleeping {delay}s"
            )
        elif remaining <= self.config.WARNING_THRESHOLD:
            logger.info(f"Rate limit low ({remaining}), sleeping {delay}s")
        else:
            logger.debug(
                f"Conservative delay: {remaining} remaining, sleeping {delay}s"
            )

    def _handle_rate_limit_failure(self) -> None:
        """Handle failure to check rate limit."""
        logger.warning(f"Using fallback delay of {self.config.FALLBACK_DELAY}s")
        time.sleep(self.config.FALLBACK_DELAY)


# Factory function for easy instantiation
def create_rate_limiter(
    strategy_type: str = "conservative", config: Optional[RateLimitConfig] = None
) -> RateLimiter:
    """
    Factory function to create rate limiter with specified strategy.

    Args:
        strategy_type: "conservative" or "aggressive"
        config: Optional custom configuration

    Returns:
        Configured RateLimiter instance
    """
    config = config or RateLimitConfig()

    if strategy_type == "aggressive":
        strategy = AggressiveRateLimitStrategy(config)
    else:
        strategy = ConservativeRateLimitStrategy(config)

    return RateLimiter(strategy, config)


# Default instance for backward compatibility
default_rate_limiter = create_rate_limiter("conservative")
