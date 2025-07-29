"""
Domain Layer - Core Business Logic

This layer contains the core business entities, value objects, and domain services.
It has no dependencies on external frameworks or infrastructure.

Following Uncle Bob's Clean Architecture:
- Entities: Core business objects with business rules
- Value Objects: Immutable objects that describe aspects of the domain
- Domain Services: Business logic that doesn't naturally fit in entities
- Repository Interfaces: Contracts for data access (implemented in infrastructure)
"""

from .entities import Portfolio, Asset, Trade, PurchaseLot
from .value_objects import Money, AssetSymbol, TradeType, Timestamp
from .services import PortfolioCalculationService, FIFOCalculationService
from .repositories import IPortfolioRepository, IMarketDataRepository

__all__ = [
    # Entities
    "Portfolio",
    "Asset", 
    "Trade",
    "PurchaseLot",
    
    # Value Objects
    "Money",
    "AssetSymbol",
    "TradeType", 
    "Timestamp",
    
    # Domain Services
    "PortfolioCalculationService",
    "FIFOCalculationService",
    
    # Repository Interfaces
    "IPortfolioRepository",
    "IMarketDataRepository",
]
