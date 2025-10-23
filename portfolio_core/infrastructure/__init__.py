"""
Infrastructure Layer

This layer contains implementations of repository interfaces and external
service integrations. It handles all external dependencies and data access.

Following Clean Architecture:
- Repository Implementations: Concrete implementations of domain repository interfaces
- External Service Clients: API clients for external services (Bitvavo, etc.)
- Data Mappers: Convert between domain entities and external data formats
- Configuration: Infrastructure-specific configuration
"""

from .repositories import (
    BitvavoPortfolioRepository,
    BitvavoMarketDataRepository,
    InMemoryPortfolioRepository,
)
from .clients import BitvavoAPIClient
from .mappers import BitvavoDataMapper

__all__ = [
    # Repository Implementations
    "BitvavoPortfolioRepository",
    "BitvavoMarketDataRepository", 
    "InMemoryPortfolioRepository",
    
    # External Clients
    "BitvavoAPIClient",
    
    # Data Mappers
    "BitvavoDataMapper",
]
