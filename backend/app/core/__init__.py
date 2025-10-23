"""
Core configuration and dependency injection module.

This module provides strongly typed configuration management and dependency
injection patterns similar to C# ASP.NET Core.
"""

from .config import Settings, get_settings
from .exceptions import *

# Import dependencies only when explicitly needed to avoid circular imports
def get_dependencies():
    """Lazy import of dependencies to avoid circular imports."""
    from .dependencies import get_chat_service, get_market_service, get_portfolio_service
    return get_chat_service, get_market_service, get_portfolio_service

__all__ = [
    # Configuration
    "Settings",
    "get_settings",
    # Dependencies (lazy loaded)
    "get_dependencies",
    # Exceptions
    "APIException",
    "PortfolioServiceException",
    "MarketServiceException",
    "ChatServiceException",
    "AssetNotFoundException",
    "ConversationNotFoundException",
    "FunctionNotFoundException",
    "InvalidRequestException",
    "RateLimitExceededError",
    "BitvavoAPIException",
]
