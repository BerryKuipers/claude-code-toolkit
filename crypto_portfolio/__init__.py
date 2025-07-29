"""
Crypto Portfolio Analysis Package

A unified, solid module structure for cryptocurrency portfolio analysis
with FIFO P&L calculations, Bitvavo API integration, and comprehensive
business logic.

This package provides a single source of truth for all portfolio operations,
eliminating import path issues and duplicate code.
"""

__version__ = "1.0.0"
__author__ = "Berry Kuipers"

# Core portfolio functionality
from .core.portfolio import PortfolioCalculator
from .core.bitvavo_client import BitvavoClient
from .core.exceptions import (
    PortfolioException,
    BitvavoAPIException,
    InvalidAPIKeyError,
    RateLimitExceededError,
)

# Data models
from .models.portfolio import (
    PurchaseLot,
    TransferSummary,
    PortfolioSummary,
    AssetHolding,
    ReconciliationResult,
)

# Services
from .services.portfolio_service import PortfolioService
from .services.market_service import MarketService

__all__ = [
    # Core classes
    "PortfolioCalculator",
    "BitvavoClient",
    
    # Services
    "PortfolioService", 
    "MarketService",
    
    # Models
    "PurchaseLot",
    "TransferSummary", 
    "PortfolioSummary",
    "AssetHolding",
    "ReconciliationResult",
    
    # Exceptions
    "PortfolioException",
    "BitvavoAPIException", 
    "InvalidAPIKeyError",
    "RateLimitExceededError",
]
