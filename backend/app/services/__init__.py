"""
Business logic services with strongly typed interfaces.

This module provides service layer implementations following SOLID principles
with clear interfaces similar to C# service patterns.
"""

from .base_service import BaseService
from .chat_service import ChatService
from .interfaces import *
from .market_service import MarketService
from .portfolio_service import PortfolioService
# ServiceFactory removed - using Clean Architecture container

__all__ = [
    # Interfaces
    "IPortfolioService",
    "IMarketService",
    "IChatService",
    "IBitvavoClient",
    # Base classes
    "BaseService",
    # Implementations
    "PortfolioService",
    "MarketService",
    "ChatService",
]
