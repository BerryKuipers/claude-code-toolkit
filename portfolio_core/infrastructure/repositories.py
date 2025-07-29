"""
Repository Implementations

Concrete implementations of domain repository interfaces.
These handle all external data access and API interactions.
"""

import logging
from typing import Dict, List, Optional, Set
from uuid import UUID

from ..domain.entities import Portfolio, Trade
from ..domain.repositories import IPortfolioRepository, IMarketDataRepository
from ..domain.value_objects import AssetSymbol, Money, Timestamp

from .clients import BitvavoAPIClient
from .mappers import BitvavoDataMapper

logger = logging.getLogger(__name__)


class BitvavoPortfolioRepository(IPortfolioRepository):
    """
    Portfolio repository implementation using Bitvavo API.
    
    This repository handles all portfolio data access through the Bitvavo API,
    providing a clean interface to the domain layer.
    """
    
    def __init__(self, bitvavo_client: BitvavoAPIClient, data_mapper: BitvavoDataMapper):
        """Initialize with Bitvavo client and data mapper."""
        self.bitvavo_client = bitvavo_client
        self.data_mapper = data_mapper
        self._portfolio_cache: Dict[UUID, Portfolio] = {}
    
    async def get_portfolio(self, portfolio_id: UUID) -> Optional[Portfolio]:
        """Get portfolio by ID."""
        # For now, return a default portfolio since we're using Bitvavo as single source
        # In a real implementation, this might be stored in a database
        if portfolio_id in self._portfolio_cache:
            return self._portfolio_cache[portfolio_id]
        
        # Create default portfolio
        portfolio = Portfolio(id=portfolio_id, name="Bitvavo Portfolio")
        self._portfolio_cache[portfolio_id] = portfolio
        return portfolio
    
    async def save_portfolio(self, portfolio: Portfolio) -> None:
        """Save portfolio."""
        # Cache the portfolio
        self._portfolio_cache[portfolio.id] = portfolio
        logger.debug(f"Saved portfolio {portfolio.id} to cache")
    
    async def get_portfolio_assets(self, portfolio_id: UUID) -> Set[AssetSymbol]:
        """Get all asset symbols in a portfolio."""
        try:
            # Get balance data from Bitvavo
            balance_data = await self.bitvavo_client.get_balance()
            
            # Map to asset amounts and extract symbols
            asset_amounts = self.data_mapper.map_balance_data_to_amounts(balance_data)
            
            return set(asset_amounts.keys())
            
        except Exception as e:
            logger.error(f"Failed to get portfolio assets: {e}")
            return set()
    
    async def get_trades_for_asset(self, portfolio_id: UUID, asset: AssetSymbol, 
                                 start_time: Optional[Timestamp] = None,
                                 end_time: Optional[Timestamp] = None) -> List[Trade]:
        """Get all trades for a specific asset in a portfolio."""
        try:
            market = f"{asset.symbol}-EUR"
            
            # Prepare parameters
            start_ts = start_time.value if start_time else None
            end_ts = end_time.value if end_time else None
            
            # Get trades from Bitvavo
            trades_data = await self.bitvavo_client.get_trades(
                market=market,
                limit=1000,
                start=start_ts,
                end=end_ts
            )
            
            # Map to domain entities
            trades = self.data_mapper.map_trades_list_to_domain(trades_data)
            
            # Sort by timestamp (oldest first for FIFO)
            trades.sort(key=lambda t: t.timestamp.value)
            
            return trades
            
        except Exception as e:
            logger.error(f"Failed to get trades for asset {asset}: {e}")
            return []
    
    async def get_all_trades(self, portfolio_id: UUID,
                           start_time: Optional[Timestamp] = None,
                           end_time: Optional[Timestamp] = None) -> Dict[AssetSymbol, List[Trade]]:
        """Get all trades grouped by asset."""
        try:
            # Get all assets in portfolio
            assets = await self.get_portfolio_assets(portfolio_id)
            
            # Get trades for each asset
            trades_by_asset = {}
            for asset in assets:
                trades = await self.get_trades_for_asset(portfolio_id, asset, start_time, end_time)
                if trades:  # Only include assets with trades
                    trades_by_asset[asset] = trades
            
            return trades_by_asset
            
        except Exception as e:
            logger.error(f"Failed to get all trades: {e}")
            return {}
    
    async def add_trade(self, portfolio_id: UUID, trade: Trade) -> None:
        """Add a new trade to the portfolio."""
        # This would typically involve posting to an API or database
        # For Bitvavo, trades are created through their trading interface
        # This method is here for completeness but may not be implemented
        logger.warning("Adding trades through API not implemented for Bitvavo")
        raise NotImplementedError("Adding trades through repository not supported")
    
    async def get_deposit_history(self, portfolio_id: UUID, asset: Optional[AssetSymbol] = None) -> List[Dict]:
        """Get deposit history for portfolio or specific asset."""
        try:
            symbol = asset.symbol if asset else None
            deposit_data = await self.bitvavo_client.get_deposit_history(symbol)
            return deposit_data
            
        except Exception as e:
            logger.error(f"Failed to get deposit history: {e}")
            return []
    
    async def get_withdrawal_history(self, portfolio_id: UUID, asset: Optional[AssetSymbol] = None) -> List[Dict]:
        """Get withdrawal history for portfolio or specific asset."""
        try:
            symbol = asset.symbol if asset else None
            withdrawal_data = await self.bitvavo_client.get_withdrawal_history(symbol)
            return withdrawal_data
            
        except Exception as e:
            logger.error(f"Failed to get withdrawal history: {e}")
            return []


class BitvavoMarketDataRepository(IMarketDataRepository):
    """
    Market data repository implementation using Bitvavo API.
    
    Handles all market data retrieval with caching and error handling.
    """
    
    def __init__(self, bitvavo_client: BitvavoAPIClient, data_mapper: BitvavoDataMapper):
        """Initialize with Bitvavo client and data mapper."""
        self.bitvavo_client = bitvavo_client
        self.data_mapper = data_mapper
        self._price_cache: Dict[str, Money] = {}
    
    async def get_current_price(self, asset: AssetSymbol) -> Money:
        """Get current market price for an asset."""
        try:
            # Check cache first
            cache_key = asset.symbol
            if cache_key in self._price_cache:
                return self._price_cache[cache_key]
            
            market = f"{asset.symbol}-EUR"
            ticker_data = await self.bitvavo_client.get_ticker_price(market)
            
            # Map to domain Money object
            price = self.data_mapper.map_ticker_data_to_price(ticker_data)
            
            # Cache the price
            self._price_cache[cache_key] = price
            
            return price
            
        except Exception as e:
            logger.error(f"Failed to get current price for {asset}: {e}")
            # Return zero price as fallback
            return Money(0, "EUR")
    
    async def get_current_prices(self, assets: List[AssetSymbol]) -> Dict[AssetSymbol, Money]:
        """Get current market prices for multiple assets."""
        prices = {}
        
        for asset in assets:
            try:
                price = await self.get_current_price(asset)
                prices[asset] = price
            except Exception as e:
                logger.warning(f"Failed to get price for {asset}: {e}")
                prices[asset] = Money(0, "EUR")
        
        return prices
    
    async def get_historical_price(self, asset: AssetSymbol, timestamp: Timestamp) -> Money:
        """Get historical price for an asset at a specific time."""
        # Historical price retrieval would require additional Bitvavo API calls
        # This is a placeholder implementation
        logger.warning("Historical price retrieval not implemented")
        return Money(0, "EUR")
    
    async def get_price_history(self, asset: AssetSymbol, 
                              start_time: Timestamp, 
                              end_time: Timestamp) -> List[Dict]:
        """Get price history for an asset within a time range."""
        # Price history retrieval would require additional Bitvavo API calls
        # This is a placeholder implementation
        logger.warning("Price history retrieval not implemented")
        return []
    
    async def is_market_open(self) -> bool:
        """Check if the market is currently open."""
        # Crypto markets are always open
        return True
    
    async def get_supported_assets(self) -> List[AssetSymbol]:
        """Get list of supported assets."""
        # This would require querying Bitvavo's markets endpoint
        # For now, return common assets
        common_assets = ["BTC", "ETH", "ADA", "DOT", "LINK", "LTC", "XRP"]
        return [AssetSymbol(symbol) for symbol in common_assets]


class InMemoryPortfolioRepository(IPortfolioRepository):
    """
    In-memory portfolio repository for testing and development.
    
    This repository stores all data in memory and is useful for testing
    and development scenarios where external API access is not needed.
    """
    
    def __init__(self):
        """Initialize empty in-memory storage."""
        self._portfolios: Dict[UUID, Portfolio] = {}
        self._trades: Dict[UUID, Dict[AssetSymbol, List[Trade]]] = {}
    
    async def get_portfolio(self, portfolio_id: UUID) -> Optional[Portfolio]:
        """Get portfolio by ID."""
        return self._portfolios.get(portfolio_id)
    
    async def save_portfolio(self, portfolio: Portfolio) -> None:
        """Save portfolio."""
        self._portfolios[portfolio.id] = portfolio
    
    async def get_portfolio_assets(self, portfolio_id: UUID) -> Set[AssetSymbol]:
        """Get all asset symbols in a portfolio."""
        if portfolio_id not in self._trades:
            return set()
        return set(self._trades[portfolio_id].keys())
    
    async def get_trades_for_asset(self, portfolio_id: UUID, asset: AssetSymbol, 
                                 start_time: Optional[Timestamp] = None,
                                 end_time: Optional[Timestamp] = None) -> List[Trade]:
        """Get all trades for a specific asset in a portfolio."""
        if portfolio_id not in self._trades:
            return []
        
        trades = self._trades[portfolio_id].get(asset, [])
        
        # Filter by time range if specified
        if start_time or end_time:
            filtered_trades = []
            for trade in trades:
                if start_time and trade.timestamp < start_time:
                    continue
                if end_time and trade.timestamp > end_time:
                    continue
                filtered_trades.append(trade)
            trades = filtered_trades
        
        return sorted(trades, key=lambda t: t.timestamp.value)
    
    async def get_all_trades(self, portfolio_id: UUID,
                           start_time: Optional[Timestamp] = None,
                           end_time: Optional[Timestamp] = None) -> Dict[AssetSymbol, List[Trade]]:
        """Get all trades grouped by asset."""
        if portfolio_id not in self._trades:
            return {}
        
        result = {}
        for asset in self._trades[portfolio_id]:
            trades = await self.get_trades_for_asset(portfolio_id, asset, start_time, end_time)
            if trades:
                result[asset] = trades
        
        return result
    
    async def add_trade(self, portfolio_id: UUID, trade: Trade) -> None:
        """Add a new trade to the portfolio."""
        if portfolio_id not in self._trades:
            self._trades[portfolio_id] = {}
        
        if trade.asset not in self._trades[portfolio_id]:
            self._trades[portfolio_id][trade.asset] = []
        
        self._trades[portfolio_id][trade.asset].append(trade)
    
    async def get_deposit_history(self, portfolio_id: UUID, asset: Optional[AssetSymbol] = None) -> List[Dict]:
        """Get deposit history for portfolio or specific asset."""
        try:
            if asset:
                # Get deposits for specific asset
                deposits = await self.bitvavo_client.get_deposit_history(asset.symbol)
                return deposits
            else:
                # Get deposits for all assets
                deposits = await self.bitvavo_client.get_deposit_history()
                return deposits
        except Exception as e:
            logger.error(f"Failed to get deposit history: {e}")
            return []

    async def get_withdrawal_history(self, portfolio_id: UUID, asset: Optional[AssetSymbol] = None) -> List[Dict]:
        """Get withdrawal history for portfolio or specific asset."""
        try:
            if asset:
                # Get withdrawals for specific asset
                withdrawals = await self.bitvavo_client.get_withdrawal_history(asset.symbol)
                return withdrawals
            else:
                # Get withdrawals for all assets
                withdrawals = await self.bitvavo_client.get_withdrawal_history()
                return withdrawals
        except Exception as e:
            logger.error(f"Failed to get withdrawal history: {e}")
            return []

