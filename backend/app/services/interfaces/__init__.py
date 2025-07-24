"""
Service interfaces providing C#-like interface contracts.

These interfaces define the contracts for business logic services,
enabling dependency injection and testability.
"""

from .portfolio_service import IPortfolioService
from .market_service import IMarketService
from .chat_service import IChatService
from .bitvavo_client import IBitvavoClient

__all__ = [
    "IPortfolioService",
    "IMarketService", 
    "IChatService",
    "IBitvavoClient",
]
