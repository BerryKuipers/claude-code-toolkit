"""
Market core logic - Clean Architecture implementation.

This module provides market data functionality using the crypto_portfolio package
and Clean Architecture patterns.
"""

import sys
import os
import logging
from decimal import Decimal
from typing import Dict, List, Optional, Any

# Add project root to Python path for portfolio_core imports
_current_file = os.path.abspath(__file__)
_backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(_current_file)))  # backend/app/shared -> backend
_project_root = os.path.dirname(_backend_dir)  # backend -> crypto_insight

if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

logger = logging.getLogger(__name__)

# Get settings for API credentials
from ..core.config import get_settings

# Import from the working crypto_portfolio package
logger.info("🔄 Importing market data from crypto_portfolio package...")
print("🔄 Importing market data from crypto_portfolio package...")

from crypto_portfolio.core.bitvavo_client import BitvavoClient
from crypto_portfolio.core.exceptions import (
    PortfolioException,
    BitvavoAPIException,
)

logger.info("✅ Successfully imported crypto_portfolio package for market data")
print("✅ Successfully imported crypto_portfolio package for market data")

# Create market data service using crypto_portfolio
class MarketDataService:
    """Market data service using the crypto_portfolio package."""
    def __init__(self):
        settings = get_settings()
        self.bitvavo_client = BitvavoClient(
            api_key=settings.bitvavo_api_key,
            api_secret=settings.bitvavo_api_secret
        )

# Create service instance
_market_service = MarketDataService()

def get_current_price(client, asset: str) -> Decimal:
    """Get current price for an asset."""
    try:
        market = f"{asset}-EUR"
        ticker = _market_service.bitvavo_client.get_ticker_price(market)
        return Decimal(str(ticker.get("price", "0")))
    except Exception as e:
        logger.error(f"Error getting price for {asset}: {e}")
        return Decimal("0")

def get_market_prices(client, assets: Optional[List[str]] = None) -> Dict[str, Dict[str, any]]:
    """Get current market prices for multiple assets."""
    if not assets:
        assets = ["BTC", "ETH", "ADA", "DOT", "LINK", "UNI", "AAVE", "SUSHI"]

    prices = {}
    for asset in assets:
        try:
            current_price = get_current_price(client, asset)
            if current_price > 0:
                prices[asset] = {
                    "price_eur": current_price,
                    "asset": asset,
                    "last_updated": "now"
                }
        except Exception as e:
            logger.error(f"Error getting price for {asset}: {e}")
            # Skip assets that fail
            continue

    return prices

def calculate_price_change_24h(client, asset: str) -> Decimal:
    """Calculate 24-hour price change for an asset."""
    try:
        market = f"{asset}-EUR"
        ticker_24h = _market_service.bitvavo_client.get_ticker_24h(market)

        current_price = Decimal(str(ticker_24h.get("last", "0")))
        open_price = Decimal(str(ticker_24h.get("open", "0")))

        if open_price > 0:
            change_24h = current_price - open_price
            change_24h_percent = (change_24h / open_price) * 100
        else:
            change_24h_percent = Decimal("0")

        return change_24h_percent
    except Exception as e:
        logger.error(f"Error calculating 24h change for {asset}: {e}")
        return Decimal("0")

def get_market_summary(client) -> Dict[str, Any]:
    """Get overall market summary with key metrics."""
    try:
        major_assets = ["BTC", "ETH", "ADA", "DOT", "LINK"]
        prices = get_market_prices(client, major_assets)

        if not prices:
            return {
                "total_market_cap": Decimal("0"),
                "trend": "UNKNOWN",
                "fear_greed_index": None
            }

        # Calculate simple market trend based on major assets
        positive_changes = 0
        total_assets = len(prices)

        for asset in prices:
            change = calculate_price_change_24h(client, asset)
            if change > 0:
                positive_changes += 1

        # Determine trend
        if positive_changes / total_assets > 0.6:
            trend = "BULLISH"
        elif positive_changes / total_assets < 0.4:
            trend = "BEARISH"
        else:
            trend = "NEUTRAL"

        return {
            "total_market_cap": Decimal("2500000000000.00"),  # Mock for now
            "trend": trend,
            "fear_greed_index": 65 if trend == "BULLISH" else 35 if trend == "BEARISH" else 50
        }
    except Exception as e:
        logger.error(f"Error getting market summary: {e}")
        return {
            "total_market_cap": Decimal("0"),
            "trend": "UNKNOWN",
            "fear_greed_index": None
        }

class TechnicalAnalyzer:
    """Technical analysis service."""
    def __init__(self):
        self.market_service = _market_service
    
    def analyze_asset(self, asset: str) -> Dict[str, Any]:
        """Analyze an asset technically."""
        try:
            price_data = calculate_price_change_24h(asset)
            return {
                "asset": asset,
                "trend": "bullish" if price_data["change_24h_percent"] > 0 else "bearish",
                "strength": abs(float(price_data["change_24h_percent"])),
                "recommendation": "hold"
            }
        except Exception as e:
            return {"asset": asset, "error": str(e)}

# Re-export for clean imports
__all__ = [
    "get_current_price",
    "TechnicalAnalyzer", 
    "get_market_prices",
    "calculate_price_change_24h",
    "get_market_summary",
]
