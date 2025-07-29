"""
Portfolio service for high-level portfolio operations.

Provides business logic for portfolio analysis, combining the core
calculation engine with API data retrieval.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Set

from ..core.bitvavo_client import BitvavoClient
from ..core.portfolio import PortfolioCalculator
from ..core.exceptions import PortfolioException, BitvavoAPIException
from ..models.portfolio import (
    AssetHolding,
    PortfolioSummary,
    TransferSummary,
    ReconciliationResult,
)

logger = logging.getLogger(__name__)


class PortfolioService:
    """
    High-level portfolio service.
    
    Combines the core portfolio calculation engine with API data retrieval
    to provide comprehensive portfolio analysis functionality.
    """
    
    def __init__(self, bitvavo_client: BitvavoClient):
        """
        Initialize the portfolio service.
        
        Args:
            bitvavo_client: Configured Bitvavo API client
        """
        self.bitvavo_client = bitvavo_client
        self.calculator = PortfolioCalculator()
        self._cache: Dict[str, any] = {}
        self._cache_timestamp: Optional[datetime] = None
        # Longer cache for portfolio holdings (30 minutes) since they don't change frequently
        self._cache_ttl_seconds = 1800  # 30 minutes
        # Separate cache for balance data with longer TTL
        self._balance_cache: Dict[str, any] = {}
        self._balance_cache_timestamp: Optional[datetime] = None
        self._balance_cache_ttl_seconds = 3600  # 1 hour for balance data
        
    def _is_cache_valid(self) -> bool:
        """Check if the cache is still valid."""
        if not self._cache_timestamp:
            return False
        return (datetime.utcnow() - self._cache_timestamp).total_seconds() < self._cache_ttl_seconds

    def _is_balance_cache_valid(self) -> bool:
        """Check if the balance cache is still valid."""
        if not self._balance_cache_timestamp:
            return False
        return (datetime.utcnow() - self._balance_cache_timestamp).total_seconds() < self._balance_cache_ttl_seconds
    
    def _clear_cache(self) -> None:
        """Clear the cache."""
        self._cache.clear()
        self._cache_timestamp = None
    
    def get_portfolio_assets(self) -> Set[str]:
        """
        Get all assets in the portfolio with non-zero balances.
        
        Returns:
            Set of asset symbols
            
        Raises:
            PortfolioException: If unable to retrieve assets
        """
        try:
            # Use longer balance cache for portfolio assets since they don't change frequently
            if self._is_balance_cache_valid() and "assets" in self._balance_cache:
                return self._balance_cache["assets"]

            balances = self.bitvavo_client.get_balance()
            assets = set()

            for balance in balances:
                symbol = balance.get("symbol", "")
                available = Decimal(str(balance.get("available", "0")))
                in_order = Decimal(str(balance.get("inOrder", "0")))

                if available + in_order > 0:
                    assets.add(symbol)

            # Cache with longer TTL for balance data
            self._balance_cache["assets"] = assets
            self._balance_cache_timestamp = datetime.utcnow()

            return assets
            
        except BitvavoAPIException as e:
            raise PortfolioException(f"Failed to get portfolio assets: {e}") from e
        except Exception as e:
            raise PortfolioException(f"Unexpected error getting portfolio assets: {e}") from e
    
    def get_asset_trades(self, asset: str) -> List[Dict[str, str]]:
        """
        Get all trades for a specific asset.
        
        Args:
            asset: Asset symbol (e.g., 'BTC')
            
        Returns:
            List of trade dictionaries
            
        Raises:
            PortfolioException: If unable to retrieve trades
        """
        try:
            cache_key = f"trades_{asset}"
            if self._is_cache_valid() and cache_key in self._cache:
                return self._cache[cache_key]
            
            market = f"{asset}-EUR"
            trades = []
            
            # Get all trades for this market
            all_trades = self.bitvavo_client.get_trades(market)
            
            # Convert to the format expected by the calculator
            for trade in all_trades:
                trades.append({
                    "side": trade.get("side", ""),
                    "amount": str(trade.get("amount", "0")),
                    "price": str(trade.get("price", "0")),
                    "fee": str(trade.get("fee", "0")),
                    "timestamp": str(trade.get("timestamp", "0")),
                })
            
            # Sort by timestamp (oldest first for FIFO)
            trades.sort(key=lambda x: int(x.get("timestamp", "0")))
            
            self._cache[cache_key] = trades
            self._cache_timestamp = datetime.utcnow()
            
            return trades
            
        except BitvavoAPIException as e:
            raise PortfolioException(f"Failed to get trades for {asset}: {e}") from e
        except Exception as e:
            raise PortfolioException(f"Unexpected error getting trades for {asset}: {e}") from e
    
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
    
    def calculate_asset_pnl(self, asset: str) -> Dict[str, Decimal]:
        """
        Calculate P&L for a specific asset.
        
        Args:
            asset: Asset symbol
            
        Returns:
            Dictionary with P&L metrics
            
        Raises:
            PortfolioException: If calculation fails
        """
        try:
            trades = self.get_asset_trades(asset)
            current_price = self.get_current_price(asset)
            
            return self.calculator.calculate_pnl(trades, current_price)
            
        except Exception as e:
            raise PortfolioException(f"Failed to calculate P&L for {asset}: {e}") from e
    
    def get_portfolio_summary(self) -> PortfolioSummary:
        """
        Get comprehensive portfolio summary.
        
        Returns:
            PortfolioSummary with complete portfolio metrics
            
        Raises:
            PortfolioException: If unable to generate summary
        """
        try:
            assets = self.get_portfolio_assets()
            asset_pnl_data = {}
            
            for asset in assets:
                try:
                    pnl_data = self.calculate_asset_pnl(asset)
                    if pnl_data.get("amount", Decimal("0")) > 0:  # Only include assets with holdings
                        asset_pnl_data[asset] = pnl_data
                except Exception as e:
                    logger.warning(f"Error calculating P&L for {asset}: {e}")
                    continue
            
            totals = self.calculator.calculate_portfolio_totals(asset_pnl_data)
            
            return PortfolioSummary(
                total_value=totals["total_value"],
                total_cost=totals["total_cost"],
                realized_pnl=totals["total_realized_pnl"],
                unrealized_pnl=totals["total_unrealized_pnl"],
                total_pnl=totals["total_pnl"],
                total_return_percentage=totals["total_return_percentage"],
                asset_count=totals["asset_count"],
                last_updated=datetime.utcnow(),
            )
            
        except Exception as e:
            raise PortfolioException(f"Failed to get portfolio summary: {e}") from e
    
    def refresh_data(self) -> bool:
        """
        Force refresh of all cached data.
        
        Returns:
            True if refresh was successful
        """
        try:
            self._clear_cache()
            # Test connection by getting assets
            self.get_portfolio_assets()
            return True
        except Exception as e:
            logger.error(f"Failed to refresh portfolio data: {e}")
            return False
