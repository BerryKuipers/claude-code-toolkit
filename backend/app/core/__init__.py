"""
Core configuration and dependency injection module.

This module provides strongly typed configuration management and dependency
injection patterns similar to C# ASP.NET Core.
"""

from .config import Settings, get_settings
from .dependencies import get_portfolio_service, get_market_service, get_chat_service
from .exceptions import *

__all__ = [
    # Configuration
    "Settings",
    "get_settings",
    
    # Dependencies
    "get_portfolio_service",
    "get_market_service", 
    "get_chat_service",
    
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
