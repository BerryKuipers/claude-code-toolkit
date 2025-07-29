"""
Cached Bitvavo API client for development.

This client wraps the regular Bitvavo client with local database caching
to reduce API calls and provide resilience during development.
"""

import logging
from typing import List, Dict, Any, Optional


from .bitvavo_client import BitvavoAPIClient
from ..core.database import get_dev_cache
from ..core.exceptions import BitvavoAPIException, RateLimitExceededError
from ..core.config import Settings

logger = logging.getLogger(__name__)


class CachedBitvavoAPIClient:
    """
    Bitvavo API client with local database caching for development.
    
    This client provides:
    - Automatic caching of API responses in SQLite
    - Fallback to cached data when API is unavailable
    - Configurable TTL for different data types
    - Development-friendly error handling
    """
    
    def __init__(self, settings: Settings, enable_cache: bool = True):
        """Initialize cached client."""
        self.settings = settings
        self.enable_cache = enable_cache
        self.api_client = BitvavoAPIClient(settings)
        self.cache = get_dev_cache() if enable_cache else None
        
        logger.info(f"CachedBitvavoAPIClient initialized (cache: {'enabled' if enable_cache else 'disabled'})")
    
    async def get_balance(self) -> List[Dict[str, Any]]:
        """
        Get account balance with caching.
        
        Returns cached data if API is unavailable or rate limited.
        """
        # Try cache first if enabled
        if self.enable_cache:
            cached_holdings = self.cache.get_cached_portfolio_holdings()
            if cached_holdings:
                logger.info("🔄 Using cached portfolio holdings (API call avoided)")
                return cached_holdings
        
        # Try API call
        try:
            logger.info("📡 Fetching fresh portfolio holdings from Bitvavo API")
            balance_data = await self.api_client.get_balance()
            
            # Cache the successful response
            if self.enable_cache and balance_data:
                self.cache.cache_portfolio_holdings(balance_data, ttl_hours=1)
                logger.info("💾 Portfolio holdings cached successfully")
            
            return balance_data
            
        except (RateLimitExceededError, BitvavoAPIException) as e:
            logger.warning(f"API call failed: {e}")
            
            # Fallback to cache if available
            if self.enable_cache:
                cached_holdings = self.cache.get_cached_portfolio_holdings()
                if cached_holdings:
                    logger.info("🔄 Falling back to cached portfolio holdings due to API error")
                    return cached_holdings
                else:
                    logger.error("No cached data available for fallback")
            
            # Re-raise if no cache available
            raise
    
    async def get_ticker_price(self, market: str) -> Dict[str, Any]:
        """
        Get ticker price with caching.
        
        Args:
            market: Market symbol (e.g., 'BTC-EUR')
            
        Returns:
            Ticker data with price information
        """
        asset_symbol = market.split('-')[0]
        
        # Try cache first if enabled
        if self.enable_cache:
            cached_price = self.cache.get_cached_market_price(asset_symbol)
            if cached_price:
                logger.debug(f"🔄 Using cached price for {asset_symbol}: €{cached_price}")
                return {"price": cached_price}
        
        # Try API call
        try:
            logger.debug(f"📡 Fetching fresh price for {market} from Bitvavo API")
            ticker_data = await self.api_client.get_ticker_price(market)
            
            # Cache the successful response
            if self.enable_cache and ticker_data and "price" in ticker_data:
                self.cache.cache_market_price(
                    asset_symbol, 
                    str(ticker_data["price"]), 
                    market, 
                    ttl_minutes=5
                )
                logger.debug(f"💾 Price cached for {asset_symbol}: €{ticker_data['price']}")
            
            return ticker_data
            
        except (RateLimitExceededError, BitvavoAPIException) as e:
            logger.warning(f"Price API call failed for {market}: {e}")
            
            # Fallback to cache if available
            if self.enable_cache:
                cached_price = self.cache.get_cached_market_price(asset_symbol)
                if cached_price:
                    logger.info(f"🔄 Falling back to cached price for {asset_symbol}: €{cached_price}")
                    return {"price": cached_price}
                else:
                    logger.error(f"No cached price available for {asset_symbol}")
            
            # Re-raise if no cache available
            raise
    
    async def get_trades(self, market: str, limit: int = 1000, start: Optional[int] = None,
                        end: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get trade history with caching.

        Args:
            market: Market symbol (e.g., 'BTC-EUR')
            limit: Maximum number of trades to return
            start: Start timestamp for trade history (optional)
            end: End timestamp for trade history (optional)

        Returns:
            List of trade data
        """
        asset_symbol = market.split('-')[0]
        
        # Try cache first if enabled
        if self.enable_cache:
            cached_trades = self.cache.get_cached_trade_history(asset_symbol)
            if cached_trades:
                logger.info(f"🔄 Using cached trades for {asset_symbol} ({len(cached_trades)} trades)")
                return cached_trades[:limit]  # Respect limit
        
        # Try API call
        try:
            logger.info(f"📡 Fetching fresh trades for {market} from Bitvavo API")
            trades_data = await self.api_client.get_trades(market, limit, start, end)
            
            # Cache the successful response
            if self.enable_cache and trades_data:
                self.cache.cache_trade_history(asset_symbol, trades_data, ttl_hours=24)
                logger.info(f"💾 Trades cached for {asset_symbol}: {len(trades_data)} trades")
            
            return trades_data
            
        except (RateLimitExceededError, BitvavoAPIException) as e:
            logger.warning(f"Trades API call failed for {market}: {e}")
            
            # Fallback to cache if available
            if self.enable_cache:
                cached_trades = self.cache.get_cached_trade_history(asset_symbol)
                if cached_trades:
                    logger.info(f"🔄 Falling back to cached trades for {asset_symbol} ({len(cached_trades)} trades)")
                    return cached_trades[:limit]  # Respect limit
                else:
                    logger.error(f"No cached trades available for {asset_symbol}")
            
            # Re-raise if no cache available
            raise
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for monitoring."""
        if not self.enable_cache:
            return {"cache_enabled": False}
        
        stats = self.cache.get_cache_stats()
        stats["cache_enabled"] = True
        return stats
    
    def clear_expired_cache(self):
        """Clear expired cache entries."""
        if self.enable_cache:
            self.cache.clear_expired_cache()
            logger.info("Expired cache entries cleared")
    
    def force_refresh_cache(self):
        """Force refresh all cached data on next API call."""
        if self.enable_cache:
            # Clear all cache to force refresh
            with self.cache._get_connection() as conn:
                cursor = conn.cursor()
                tables = ['portfolio_holdings', 'market_prices', 'trade_history']
                for table in tables:
                    cursor.execute(f"DELETE FROM {table}")
                conn.commit()
            
            logger.info("All cache cleared - next API calls will fetch fresh data")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check API and cache health.
        
        Returns:
            Health status information
        """
        health = {
            "api_available": False,
            "cache_enabled": self.enable_cache,
            "cache_stats": {},
            "last_error": None
        }
        
        # Test API availability
        try:
            await self.api_client.get_ticker_price("BTC-EUR")
            health["api_available"] = True
            logger.info("✅ Bitvavo API is available")
        except Exception as e:
            health["last_error"] = str(e)
            logger.warning(f"❌ Bitvavo API unavailable: {e}")
        
        # Get cache stats
        if self.enable_cache:
            health["cache_stats"] = self.get_cache_stats()
        
        return health


def create_cached_bitvavo_client(settings: Settings) -> CachedBitvavoAPIClient:
    """
    Factory function to create cached Bitvavo client.
    
    Args:
        settings: Application settings
        
    Returns:
        Configured cached client
    """
    # Enable cache for development, can be controlled via settings
    enable_cache = getattr(settings, 'enable_dev_cache', True)
    
    client = CachedBitvavoAPIClient(settings, enable_cache=enable_cache)
    
    # Clear expired cache on startup
    if enable_cache:
        client.clear_expired_cache()
    
    return client
