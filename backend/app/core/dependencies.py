"""
Dependency injection setup for FastAPI.

Provides C#-like dependency injection patterns with proper service lifetimes
and interface-based dependency resolution.
"""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from ..services.interfaces import IChatService, IMarketService, IPortfolioService
from ..services.chat_service import ChatService
from ..services.market_service import MarketService
from ..services.portfolio_service import PortfolioService
from .config import Settings, get_settings


# Service factory functions with proper dependency injection

@lru_cache()
def get_portfolio_service(
    settings: Annotated[Settings, Depends(get_settings)]
) -> IPortfolioService:
    """
    Get portfolio service instance with dependency injection.
    
    Similar to C# DI container service resolution.
    Uses LRU cache for singleton-like behavior.
    
    Args:
        settings: Application settings
        
    Returns:
        IPortfolioService: Portfolio service implementation
    """
    return PortfolioService(settings)


@lru_cache()
def get_market_service(
    settings: Annotated[Settings, Depends(get_settings)]
) -> IMarketService:
    """
    Get market service instance with dependency injection.
    
    Args:
        settings: Application settings
        
    Returns:
        IMarketService: Market service implementation
    """
    return MarketService(settings)


@lru_cache()
def get_chat_service(
    settings: Annotated[Settings, Depends(get_settings)],
    portfolio_service: Annotated[IPortfolioService, Depends(get_portfolio_service)]
) -> IChatService:
    """
    Get chat service instance with dependency injection.
    
    Args:
        settings: Application settings
        portfolio_service: Portfolio service for function calling
        
    Returns:
        IChatService: Chat service implementation
    """
    return ChatService(settings, portfolio_service)


# Type aliases for cleaner dependency injection
PortfolioServiceDep = Annotated[IPortfolioService, Depends(get_portfolio_service)]
MarketServiceDep = Annotated[IMarketService, Depends(get_market_service)]
ChatServiceDep = Annotated[IChatService, Depends(get_chat_service)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
