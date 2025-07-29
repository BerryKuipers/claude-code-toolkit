"""
Portfolio core logic - Clean implementation using crypto_portfolio package.

This module provides a clean interface to the working crypto_portfolio package,
eliminating all duplicate code and fallback mechanisms.
"""

import sys
import os
import logging

# Add the project root to Python path
_current_file = os.path.abspath(__file__)
_backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(_current_file)))  # backend/app/shared -> backend
_project_root = os.path.dirname(_backend_dir)  # backend -> crypto_insight

# Ensure project root is in path
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

logger = logging.getLogger(__name__)

# Get settings for API credentials
from ..core.config import get_settings

# Import from the working crypto_portfolio package
logger.info("🔄 Importing from crypto_portfolio package...")
print("🔄 Importing from crypto_portfolio package...")

from crypto_portfolio.core.portfolio import PortfolioCalculator
from crypto_portfolio.core.bitvavo_client import BitvavoClient
from crypto_portfolio.core.exceptions import (
    PortfolioException,
    BitvavoAPIException,
    InvalidAPIKeyError,
    RateLimitExceededError,
)
from crypto_portfolio.models.portfolio import (
    PortfolioSummary,
    AssetHolding,
    ReconciliationResult,
)
from crypto_portfolio.services.portfolio_service import PortfolioService

logger.info("✅ Successfully imported crypto_portfolio package")
print("✅ Successfully imported crypto_portfolio package")

# Create clean aliases for the backend services
BitvavoAPIClient = BitvavoClient

# Create a properly configured PortfolioApplicationService
class PortfolioApplicationService:
    """Application service wrapper for PortfolioService."""
    def __init__(self):
        try:
            logger.info("🔧 Initializing PortfolioApplicationService...")
            settings = get_settings()

            logger.info(f"🔑 Creating BitvavoClient with API key: {settings.bitvavo_api_key[:10]}...")
            self.bitvavo_client = BitvavoClient(
                api_key=settings.bitvavo_api_key,
                api_secret=settings.bitvavo_api_secret
            )
            logger.info("✅ BitvavoClient created successfully")

            logger.info("🏗️ Creating PortfolioService...")
            self.portfolio_service = PortfolioService(self.bitvavo_client)
            logger.info("✅ PortfolioApplicationService initialized successfully")

        except Exception as e:
            logger.error(f"💥 Failed to initialize PortfolioApplicationService: {e}", exc_info=True)
            raise

    def __getattr__(self, name):
        """Delegate all method calls to the underlying portfolio service."""
        return getattr(self.portfolio_service, name)

# Create missing service classes
class PortfolioCalculationService:
    """Portfolio calculation service using the crypto_portfolio package."""
    def __init__(self):
        # Create a properly configured BitvavoClient
        settings = get_settings()
        self.bitvavo_client = BitvavoClient(
            api_key=settings.bitvavo_api_key,
            api_secret=settings.bitvavo_api_secret
        )
        self.portfolio_service = PortfolioService(self.bitvavo_client)

    def calculate_portfolio_summary(self):
        """Calculate portfolio summary."""
        return self.portfolio_service.get_portfolio_summary()

class MarketDataApplicationService:
    """Market data service using the crypto_portfolio package."""
    def __init__(self):
        settings = get_settings()
        self.bitvavo_client = BitvavoClient(
            api_key=settings.bitvavo_api_key,
            api_secret=settings.bitvavo_api_secret
        )

    def get_current_prices(self, assets=None):
        """Get current market prices."""
        # Implementation would go here
        return {}

# Create missing repository classes
class BitvavoPortfolioRepository:
    """Portfolio repository using Bitvavo API."""
    def __init__(self, bitvavo_client, data_mapper):
        self.client = bitvavo_client
        self.data_mapper = data_mapper

class BitvavoMarketDataRepository:
    """Market data repository using Bitvavo API."""
    def __init__(self, bitvavo_client, data_mapper):
        self.client = bitvavo_client
        self.data_mapper = data_mapper

class BitvavoDataMapper:
    """Data mapper for Bitvavo API responses."""
    @staticmethod
    def map_portfolio_data(data):
        """Map Bitvavo data to internal format."""
        return data

# Create simple DTO classes that match the expected interface
class PortfolioSummaryDTO:
    def __init__(self, portfolio_summary: PortfolioSummary):
        self.total_value = portfolio_summary.total_value
        self.total_cost = portfolio_summary.total_cost
        self.realized_pnl = portfolio_summary.realized_pnl
        self.unrealized_pnl = portfolio_summary.unrealized_pnl
        self.total_pnl = portfolio_summary.total_pnl
        self.total_return_percentage = portfolio_summary.total_return_percentage
        self.asset_count = portfolio_summary.asset_count
        self.last_updated = portfolio_summary.last_updated

class AssetHoldingDTO:
    def __init__(self, asset_holding: AssetHolding):
        self.asset = asset_holding.asset
        self.quantity = asset_holding.quantity
        self.current_price = asset_holding.current_price
        self.value_eur = asset_holding.value_eur
        self.cost_basis = asset_holding.cost_basis
        self.unrealized_pnl = asset_holding.unrealized_pnl
        self.realized_pnl = asset_holding.realized_pnl
        self.total_pnl = asset_holding.total_pnl
        self.return_percentage = asset_holding.return_percentage
        self.allocation_percentage = asset_holding.allocation_percentage

# Simple FIFO calculation service wrapper
class FIFOCalculationService:
    def __init__(self):
        self.calculator = PortfolioCalculator()
    
    def calculate_asset_pnl(self, trades, current_price):
        """Calculate P&L for an asset using FIFO method."""
        # Convert to the format expected by PortfolioCalculator
        trade_list = []
        for trade in trades:
            trade_dict = {
                'amount': str(trade.amount),
                'price': str(trade.price_per_unit),
                'fee': str(trade.fee),
                'side': trade.trade_type.value.lower(),
                'timestamp': str(int(trade.timestamp.timestamp()))
            }
            trade_list.append(trade_dict)
        
        return self.calculator.calculate_pnl(trade_list, float(current_price.amount))

__all__ = [
    "PortfolioApplicationService",
    "PortfolioCalculationService",
    "MarketDataApplicationService",
    "BitvavoAPIClient",
    "BitvavoPortfolioRepository",
    "BitvavoMarketDataRepository",
    "BitvavoDataMapper",
    "FIFOCalculationService",
    "PortfolioSummaryDTO",
    "AssetHoldingDTO",
    "PortfolioCalculator",
    "PortfolioService",
    "PortfolioSummary",
    "AssetHolding",
    "PortfolioException",
    "BitvavoAPIException",
]
