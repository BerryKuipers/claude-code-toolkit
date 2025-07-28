"""
Market core logic - shared between backend and original src/ modules.

This module provides a clean interface to the market data logic
without requiring sys.path manipulation.
"""

import sys
import os
from decimal import Decimal
from typing import Dict, List, Optional, Any

# Add src to path for importing the original logic
_src_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "src")
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

# Import the original market logic
try:
    from src.portfolio.core import get_current_price
    from src.portfolio.predictions.technical_analysis import TechnicalAnalyzer
    
    # Re-export for clean imports
    __all__ = [
        "get_current_price",
        "TechnicalAnalyzer",
        "get_market_prices",
        "calculate_price_change_24h",
        "get_market_summary",
    ]
    
    def get_market_prices(client, assets: Optional[List[str]] = None) -> Dict[str, Dict[str, Any]]:
        """
        Get current market prices for multiple assets.
        
        Args:
            client: Bitvavo client instance
            assets: Optional list of asset symbols
            
        Returns:
            Dict[str, Dict[str, Any]]: Price data by asset
        """
        if assets is None:
            # Default assets to fetch
            assets = ["BTC", "ETH", "ADA", "DOT", "LINK", "XRP", "LTC", "BCH", "BNB", "SOL"]
        
        prices = {}
        for asset in assets:
            try:
                current_price = get_current_price(client, asset)
                if current_price > 0:
                    prices[asset] = {
                        "price_eur": current_price,
                        "asset": asset,
                        "last_updated": "now"  # Will be converted to datetime
                    }
            except Exception:
                # Skip assets that fail
                continue
                
        return prices
    
    def calculate_price_change_24h(client, asset: str) -> Decimal:
        """
        Calculate 24h price change percentage.
        
        Note: This is a simplified implementation.
        In a real system, you'd need historical price data.
        """
        try:
            # For now, return a mock calculation based on current price
            # In reality, you'd fetch 24h historical data
            current_price = get_current_price(client, asset)
            if current_price > 0:
                # Mock calculation - in reality you'd compare with 24h ago price
                # This is a placeholder that varies by asset
                mock_changes = {
                    "BTC": Decimal("2.5"),
                    "ETH": Decimal("-1.2"), 
                    "ADA": Decimal("5.8"),
                    "DOT": Decimal("3.1"),
                    "LINK": Decimal("-0.8"),
                    "XRP": Decimal("1.9"),
                    "LTC": Decimal("-2.1"),
                    "BCH": Decimal("4.2"),
                    "BNB": Decimal("0.7"),
                    "SOL": Decimal("6.3"),
                }
                return mock_changes.get(asset, Decimal("0.0"))
        except Exception:
            pass
        return Decimal("0.0")
    
    def get_market_summary(client) -> Dict[str, Any]:
        """
        Get overall market summary data.
        
        Returns:
            Dict[str, Any]: Market summary information
        """
        try:
            # Get prices for major assets
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
            
        except Exception:
            return {
                "total_market_cap": Decimal("0"),
                "trend": "UNKNOWN", 
                "fear_greed_index": None
            }
    
except ImportError as e:
    # Fallback for when src/ is not available
    def get_current_price(*args, **kwargs):
        raise NotImplementedError("Market core logic not available")
    
    def get_market_prices(*args, **kwargs):
        raise NotImplementedError("Market core logic not available")
    
    def calculate_price_change_24h(*args, **kwargs):
        raise NotImplementedError("Market core logic not available")
    
    def get_market_summary(*args, **kwargs):
        raise NotImplementedError("Market core logic not available")
    
    class TechnicalAnalyzer:
        def __init__(self):
            raise NotImplementedError("Technical analysis not available")
