"""
Dependency injection setup for FastAPI.

Provides C#-like dependency injection patterns with proper service lifetimes
and interface-based dependency resolution using the Service Factory pattern.
"""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from ..services.interfaces import (
    IBitvavoClient,
    IChatService,
    IMarketService,
    IPortfolioService,
)
from ..services.service_factory import ServiceFactory
from .config import Settings, get_settings

# Service factory functions with proper dependency injection

@lru_cache()
def get_service_factory(
    settings: Annotated[Settings, Depends(get_settings)]
) -> ServiceFactory:
    """
    Get service factory instance with dependency injection.

    Args:
        settings: Application settings

    Returns:
        ServiceFactory: Service factory for creating services
    """
    return ServiceFactory(settings)


def get_bitvavo_client(
    factory: Annotated[ServiceFactory, Depends(get_service_factory)]
) -> IBitvavoClient:
    """
    Get Bitvavo client instance via service factory.

    Args:
        factory: Service factory

    Returns:
        IBitvavoClient: Bitvavo client implementation
    """
    return factory.get_bitvavo_client()


def get_portfolio_service(
    factory: Annotated[ServiceFactory, Depends(get_service_factory)]
) -> IPortfolioService:
    """
    Get portfolio service instance via service factory.

    Args:
        factory: Service factory

    Returns:
        IPortfolioService: Portfolio service implementation
    """
    return factory.get_portfolio_service()


def get_market_service(
    factory: Annotated[ServiceFactory, Depends(get_service_factory)]
) -> IMarketService:
    """
    Get market service instance via service factory.

    Args:
        factory: Service factory

    Returns:
        IMarketService: Market service implementation
    """
    return factory.get_market_service()


def get_chat_service(
    factory: Annotated[ServiceFactory, Depends(get_service_factory)]
) -> IChatService:
    """
    Get chat service instance via service factory.

    Args:
        factory: Service factory

    Returns:
        IChatService: Chat service implementation
    """
    return factory.get_chat_service()


# Type aliases for cleaner dependency injection
BitvavoClientDep = Annotated[IBitvavoClient, Depends(get_bitvavo_client)]
PortfolioServiceDep = Annotated[IPortfolioService, Depends(get_portfolio_service)]
MarketServiceDep = Annotated[IMarketService, Depends(get_market_service)]
ChatServiceDep = Annotated[IChatService, Depends(get_chat_service)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
