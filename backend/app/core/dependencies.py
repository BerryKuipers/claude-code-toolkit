"""
Dependency injection setup for FastAPI using Clean Architecture.

Provides C#-like dependency injection patterns with proper service lifetimes
using the Clean Architecture dependency container.
"""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from .container import DependencyContainer, get_container
from .config import Settings, get_settings

# Clean Architecture dependency injection


@lru_cache()
def get_dependency_container(
    settings: Annotated[Settings, Depends(get_settings)],
) -> DependencyContainer:
    """
    Get Clean Architecture dependency container.

    Args:
        settings: Application settings

    Returns:
        DependencyContainer: Clean Architecture container
    """
    return get_container(settings)


def get_bitvavo_client(
    container: Annotated[DependencyContainer, Depends(get_dependency_container)],
):
    """
    Get Bitvavo client instance from Clean Architecture container.

    Args:
        container: Clean Architecture dependency container

    Returns:
        Bitvavo client implementation (cached or standard)
    """
    return container.get_bitvavo_api_client()


def get_portfolio_service(
    container: Annotated[DependencyContainer, Depends(get_dependency_container)],
):
    """
    Get portfolio service instance from Clean Architecture container.

    Args:
        container: Clean Architecture dependency container

    Returns:
        Portfolio application service
    """
    return container.get_portfolio_application_service()


def get_market_service(
    container: Annotated[DependencyContainer, Depends(get_dependency_container)],
):
    """
    Get market service instance from Clean Architecture container.

    Args:
        container: Clean Architecture dependency container

    Returns:
        Market data application service
    """
    return container.get_market_data_application_service()


def get_chat_service(
    container: Annotated[DependencyContainer, Depends(get_dependency_container)],
):
    """
    Get chat service instance from Clean Architecture container.

    Args:
        container: Clean Architecture dependency container

    Returns:
        Chat service implementation
    """
    return container.get_chat_service()


# Type aliases for cleaner dependency injection
BitvavoClientDep = Annotated[object, Depends(get_bitvavo_client)]
PortfolioServiceDep = Annotated[object, Depends(get_portfolio_service)]
MarketServiceDep = Annotated[object, Depends(get_market_service)]
ChatServiceDep = Annotated[object, Depends(get_chat_service)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
