"""
Repository Interfaces

Abstract interfaces for data access following the Repository pattern
and Dependency Inversion Principle. These define contracts that
infrastructure implementations must fulfill.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Set
from uuid import UUID

from .entities import Portfolio, Trade
from .value_objects import AssetSymbol, Money, Timestamp


class IPortfolioRepository(ABC):
    """
    Portfolio repository interface.
    
    Defines the contract for portfolio data persistence and retrieval.
    Infrastructure layer will implement this interface.
    """
    
    @abstractmethod
    async def get_portfolio(self, portfolio_id: UUID) -> Optional[Portfolio]:
        """Get portfolio by ID."""
        pass
    
    @abstractmethod
    async def save_portfolio(self, portfolio: Portfolio) -> None:
        """Save portfolio."""
        pass
    
    @abstractmethod
    async def get_portfolio_assets(self, portfolio_id: UUID) -> Set[AssetSymbol]:
        """Get all asset symbols in a portfolio."""
        pass
    
    @abstractmethod
    async def get_trades_for_asset(self, portfolio_id: UUID, asset: AssetSymbol, 
                                 start_time: Optional[Timestamp] = None,
                                 end_time: Optional[Timestamp] = None) -> List[Trade]:
        """Get all trades for a specific asset in a portfolio."""
        pass
    
    @abstractmethod
    async def get_all_trades(self, portfolio_id: UUID,
                           start_time: Optional[Timestamp] = None,
                           end_time: Optional[Timestamp] = None) -> Dict[AssetSymbol, List[Trade]]:
        """Get all trades grouped by asset."""
        pass
    
    @abstractmethod
    async def add_trade(self, portfolio_id: UUID, trade: Trade) -> None:
        """Add a new trade to the portfolio."""
        pass
    
    @abstractmethod
    async def get_deposit_history(self, portfolio_id: UUID, asset: Optional[AssetSymbol] = None) -> List[Dict]:
        """Get deposit history for portfolio or specific asset."""
        pass
    
    @abstractmethod
    async def get_withdrawal_history(self, portfolio_id: UUID, asset: Optional[AssetSymbol] = None) -> List[Dict]:
        """Get withdrawal history for portfolio or specific asset."""
        pass


class IMarketDataRepository(ABC):
    """
    Market data repository interface.
    
    Defines the contract for market data retrieval from external sources.
    Infrastructure layer will implement this interface.
    """
    
    @abstractmethod
    async def get_current_price(self, asset: AssetSymbol) -> Money:
        """Get current market price for an asset."""
        pass
    
    @abstractmethod
    async def get_current_prices(self, assets: List[AssetSymbol]) -> Dict[AssetSymbol, Money]:
        """Get current market prices for multiple assets."""
        pass
    
    @abstractmethod
    async def get_historical_price(self, asset: AssetSymbol, timestamp: Timestamp) -> Money:
        """Get historical price for an asset at a specific time."""
        pass
    
    @abstractmethod
    async def get_price_history(self, asset: AssetSymbol, 
                              start_time: Timestamp, 
                              end_time: Timestamp) -> List[Dict]:
        """Get price history for an asset within a time range."""
        pass
    
    @abstractmethod
    async def is_market_open(self) -> bool:
        """Check if the market is currently open."""
        pass
    
    @abstractmethod
    async def get_supported_assets(self) -> List[AssetSymbol]:
        """Get list of supported assets."""
        pass


class ITransferRepository(ABC):
    """
    Transfer repository interface.
    
    Defines the contract for deposit/withdrawal data retrieval.
    """
    
    @abstractmethod
    async def get_deposits(self, asset: Optional[AssetSymbol] = None) -> List[Dict]:
        """Get deposit transactions."""
        pass
    
    @abstractmethod
    async def get_withdrawals(self, asset: Optional[AssetSymbol] = None) -> List[Dict]:
        """Get withdrawal transactions."""
        pass
    
    @abstractmethod
    async def analyze_transfers(self, asset: AssetSymbol) -> Dict:
        """Analyze transfer patterns for an asset."""
        pass


class IReconciliationRepository(ABC):
    """
    Reconciliation repository interface.
    
    Defines the contract for portfolio reconciliation data.
    """
    
    @abstractmethod
    async def get_actual_balances(self) -> Dict[AssetSymbol, Money]:
        """Get actual account balances from exchange."""
        pass
    
    @abstractmethod
    async def get_balance_for_asset(self, asset: AssetSymbol) -> Money:
        """Get actual balance for a specific asset."""
        pass
    
    @abstractmethod
    async def reconcile_portfolio_balances(self, assets: Optional[List[AssetSymbol]] = None) -> List[Dict]:
        """Perform portfolio reconciliation analysis."""
        pass
