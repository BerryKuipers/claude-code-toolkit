"""
Bitvavo API client using Decorator Pattern.

This client decorates any Bitvavo client implementation with intelligent caching
to reduce API calls and provide resilience during development.
"""

import logging
from typing import List, Dict, Any, Optional, Union

from portfolio_core.infrastructure.clients import BitvavoAPIClient
from ..core.database import get_dev_cache
from ..core.exceptions import BitvavoAPIException, RateLimitExceededError
from ..core.config import Settings

logger = logging.getLogger(__name__)


class BitvavoClientDecorator:
    """
    Decorator for Bitvavo API client that adds intelligent caching.
    
    Uses the Decorator Pattern to wrap any BitvavoAPIClient implementation
    with caching capabilities without duplicating API logic.
    
    Benefits:
    - No code duplication - delegates all API calls to wrapped client
    - Interface compatibility - same methods as underlying client
    - Transparent caching - cache logic is separate from API logic
    - Easy testing - can wrap real or mock clients
    """
    
    def __init__(self, base_client: BitvavoAPIClient, enable_cache: bool = True):
        """
        Initialize cached client using Decorator Pattern.
        
        Args:
            base_client: The actual BitvavoAPIClient to wrap
            enable_cache: Whether to enable caching functionality
        """
        self._client = base_client  # Composition over inheritance
        self.enable_cache = enable_cache
        self.cache = get_dev_cache() if enable_cache else None
        
        logger.info(f"BitvavoClientDecorator initialized (cache: {'enabled' if enable_cache else 'disabled'})")
    
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
            balance_data = await self._client.get_balance()

            # Debug logging to see what we got
            logger.info(f"🔍 Bitvavo API returned {len(balance_data) if balance_data else 0} balance entries")
            if balance_data:
                logger.info(f"🔍 First few balance entries: {balance_data[:3]}")
            else:
                logger.warning("⚠️ Bitvavo API returned empty balance data")

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
            ticker_data = await self._client.get_ticker_price(market)
            
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
            trades_data = await self._client.get_trades(market, limit, start, end)
            
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

    async def get_deposit_history(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get deposit history with caching.

        Args:
            symbol: Optional asset symbol to filter by

        Returns:
            List of deposit data
        """
        # Try cache first if enabled
        if self.enable_cache:
            cached_deposits = self.cache.get_cached_deposit_history(symbol)
            if cached_deposits:
                scope = f"for {symbol}" if symbol else "for all assets"
                logger.info(f"🔄 Using cached deposit history {scope} ({len(cached_deposits)} deposits)")
                return cached_deposits

        try:
            logger.info(f"📡 Fetching deposit history from Bitvavo API{f' for {symbol}' if symbol else ''}")
            deposit_data = await self._client.get_deposit_history(symbol)

            # Cache the successful response
            if self.enable_cache and deposit_data is not None:
                self.cache.cache_deposit_history(deposit_data, symbol, ttl_hours=24)
                scope = f"for {symbol}" if symbol else "for all assets"
                logger.info(f"💾 Deposit history cached {scope}: {len(deposit_data)} deposits")

            return deposit_data

        except (RateLimitExceededError, BitvavoAPIException) as e:
            logger.warning(f"Deposit history API call failed: {e}")
            # Try to return cached data even if expired as fallback
            if self.enable_cache:
                # TODO: Add fallback to expired cache if needed
                pass
            return []

    async def get_withdrawal_history(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get withdrawal history with caching.

        Args:
            symbol: Optional asset symbol to filter by

        Returns:
            List of withdrawal data
        """
        # Try cache first if enabled
        if self.enable_cache:
            cached_withdrawals = self.cache.get_cached_withdrawal_history(symbol)
            if cached_withdrawals:
                scope = f"for {symbol}" if symbol else "for all assets"
                logger.info(f"🔄 Using cached withdrawal history {scope} ({len(cached_withdrawals)} withdrawals)")
                return cached_withdrawals

        try:
            logger.info(f"📡 Fetching withdrawal history from Bitvavo API{f' for {symbol}' if symbol else ''}")
            withdrawal_data = await self._client.get_withdrawal_history(symbol)

            # Cache the successful response
            if self.enable_cache and withdrawal_data is not None:
                self.cache.cache_withdrawal_history(withdrawal_data, symbol, ttl_hours=24)
                scope = f"for {symbol}" if symbol else "for all assets"
                logger.info(f"💾 Withdrawal history cached {scope}: {len(withdrawal_data)} withdrawals")

            return withdrawal_data

        except (RateLimitExceededError, BitvavoAPIException) as e:
            logger.warning(f"Withdrawal history API call failed: {e}")
            # Try to return cached data even if expired as fallback
            if self.enable_cache:
                # TODO: Add fallback to expired cache if needed
                pass
            return []

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
                tables = ['portfolio_holdings', 'market_prices', 'trade_history', 'deposit_history', 'withdrawal_history', 'crypto_news']
                for table in tables:
                    cursor.execute(f"DELETE FROM {table}")
                conn.commit()
            
            logger.info("All cache cleared - next API calls will fetch fresh data")
    
    async def get_multiple_ticker_prices(self, markets: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Get ticker prices for multiple markets with rate-limited parallel execution.

        This method respects the existing rate limiting by using a semaphore to control
        concurrency and ensuring proper delays between API calls.

        Args:
            markets: List of market symbols (e.g., ['BTC-EUR', 'ETH-EUR'])

        Returns:
            Dict mapping market symbols to ticker data
        """
        import asyncio

        logger.info(f"🚀 Fetching prices for {len(markets)} markets with rate-limited parallel execution")

        # 🛡️ RATE LIMITING: Use semaphore to limit concurrent requests
        # Bitvavo allows ~10 requests per second, so we limit to 3 concurrent to be safe
        max_concurrent = min(3, len(markets))  # Never exceed 3 concurrent requests
        semaphore = asyncio.Semaphore(max_concurrent)

        async def rate_limited_price_fetch(market: str):
            """Fetch price with rate limiting and proper error handling."""
            async with semaphore:
                try:
                    asset_symbol = market.split('-')[0]

                    # 🕐 RATE LIMITING: Respect the underlying client's rate limiting
                    # The base client already handles rate limiting, but we add extra safety
                    if hasattr(self._client, '_rate_limit'):
                        # Let the base client handle its own rate limiting
                        pass
                    else:
                        # Fallback delay if base client doesn't have rate limiting
                        await asyncio.sleep(0.2)

                    result = await self.get_ticker_price(asset_symbol)
                    logger.debug(f"✅ Got price for {market}: €{result.get('price', 'N/A')}")
                    return market, result

                except (RateLimitExceededError, BitvavoAPIException) as e:
                    logger.warning(f"API call failed for {market}: {e}")

                    # Try cache fallback
                    asset_symbol = market.split('-')[0]
                    if self.enable_cache:
                        cached_price = self.cache.get_cached_market_price(asset_symbol)
                        if cached_price:
                            logger.info(f"🔄 Using cached price for {market}: €{cached_price}")
                            return market, {"price": cached_price}

                    return market, None

                except Exception as e:
                    logger.error(f"Unexpected error fetching price for {market}: {e}")
                    return market, None

        # Execute all requests with rate limiting
        tasks = [rate_limited_price_fetch(market) for market in markets]
        completed_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        results = {}
        successful_count = 0

        for result in completed_results:
            if isinstance(result, Exception):
                logger.error(f"Task failed with exception: {result}")
                continue

            market, price_data = result
            if price_data is not None:
                results[market] = price_data
                successful_count += 1

        logger.info(f"🎉 Rate-limited parallel fetch completed: {successful_count}/{len(markets)} successful")
        logger.info(f"⚡ Used max {max_concurrent} concurrent requests with proper rate limiting")

        return results

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
            await self._client.get_ticker_price("BTC-EUR")
            health["api_available"] = True
            logger.info("✅ Bitvavo API is available")
        except Exception as e:
            health["last_error"] = str(e)
            logger.warning(f"❌ Bitvavo API unavailable: {e}")

        # Get cache stats
        if self.enable_cache:
            health["cache_stats"] = self.get_cache_stats()

        return health


def create_bitvavo_client(settings: Settings, enable_cache: bool = True) -> Union[BitvavoAPIClient, BitvavoClientDecorator]:
    """
    Factory function to create Bitvavo client with optional caching.
    
    Args:
        settings: Application settings
        enable_cache: Whether to wrap with cache decorator
        
    Returns:
        BitvavoAPIClient (cached or standard)
    """
    # Create base client
    base_client = BitvavoAPIClient(
        api_key=settings.bitvavo_api_key,
        api_secret=settings.bitvavo_api_secret,
        rate_limit_delay=settings.bitvavo_rate_limit_delay
    )
    
    # Wrap with cache decorator if requested
    if enable_cache:
        cached_client = BitvavoClientDecorator(base_client, enable_cache=True)
        # Clear expired cache on startup
        cached_client.clear_expired_cache()
        return cached_client
    
    return base_client
