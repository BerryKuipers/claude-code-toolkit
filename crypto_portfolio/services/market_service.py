"""
Market service for price and market data operations.

Provides market data functionality with proper caching and error handling.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

from ..core.bitvavo_client import BitvavoClient
from ..core.exceptions import PortfolioException, BitvavoAPIException

logger = logging.getLogger(__name__)


class MarketService:
    """
    Market data service.
    
    Provides market data functionality including price retrieval,
    market summaries, and price change calculations.
    """
    
    def __init__(self, bitvavo_client: BitvavoClient):
        """
        Initialize the market service.
        
        Args:
            bitvavo_client: Configured Bitvavo API client
        """
        self.bitvavo_client = bitvavo_client
        self._cache: Dict[str, any] = {}
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl_seconds = 60  # 1 minute for market data
        
    def _is_cache_valid(self) -> bool:
        """Check if the cache is still valid."""
        if not self._cache_timestamp:
            return False
        return (datetime.utcnow() - self._cache_timestamp).total_seconds() < self._cache_ttl_seconds
    
    def get_current_price(self, asset: str) -> Decimal:
        """
        Get current price for an asset.
        
        Args:
            asset: Asset symbol (e.g., 'BTC')
            
        Returns:
            Current price in EUR
            
        Raises:
            PortfolioException: If unable to retrieve price
        """
        try:
            cache_key = f"price_{asset}"
            if self._is_cache_valid() and cache_key in self._cache:
                return self._cache[cache_key]
            
            market = f"{asset}-EUR"
            ticker = self.bitvavo_client.get_ticker_price(market)
            price = Decimal(str(ticker.get("price", "0")))
            
            self._cache[cache_key] = price
            self._cache_timestamp = datetime.utcnow()
            
            return price
            
        except BitvavoAPIException as e:
            raise PortfolioException(f"Failed to get price for {asset}: {e}") from e
        except Exception as e:
            raise PortfolioException(f"Unexpected error getting price for {asset}: {e}") from e
    
    def get_multiple_prices(self, assets: List[str]) -> Dict[str, Decimal]:
        """
        Get current prices for multiple assets.
        
        Args:
            assets: List of asset symbols
            
        Returns:
            Dictionary mapping asset symbols to prices
        """
        prices = {}
        for asset in assets:
            try:
                prices[asset] = self.get_current_price(asset)
            except Exception as e:
                logger.warning(f"Failed to get price for {asset}: {e}")
                prices[asset] = Decimal("0")
        
        return prices
    
    def clear_cache(self) -> None:
        """Clear the price cache."""
        self._cache.clear()
        self._cache_timestamp = None
