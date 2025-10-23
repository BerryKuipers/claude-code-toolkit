"""
Service interfaces providing C#-like interface contracts.

These interfaces define the contracts for business logic services,
enabling dependency injection and testability.
"""

from .bitvavo_client import IBitvavoClient
from .chat_service import IChatService
from .market_service import IMarketService
from .portfolio_service import IPortfolioService

__all__ = [
    "IPortfolioService",
    "IMarketService",
    "IChatService",
    "IBitvavoClient",
]
