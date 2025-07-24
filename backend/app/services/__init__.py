"""
Business logic services with strongly typed interfaces.

This module provides service layer implementations following SOLID principles
with clear interfaces similar to C# service patterns.
"""

from .interfaces import *
from .portfolio_service import PortfolioService
from .market_service import MarketService  
from .chat_service import ChatService

__all__ = [
    # Interfaces
    "IPortfolioService",
    "IMarketService", 
    "IChatService",
    "IBitvavoClient",
    
    # Implementations
    "PortfolioService",
    "MarketService",
    "ChatService",
]
