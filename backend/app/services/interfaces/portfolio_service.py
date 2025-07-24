"""
Portfolio service interface definition.

Defines the contract for portfolio-related business logic operations
with full type safety and clear method signatures.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from ...models.portfolio import (
    HoldingResponse,
    PortfolioHoldingsResponse,
    PortfolioSummaryResponse,
    ReconciliationResponse,
    TransactionResponse,
)


class IPortfolioService(ABC):
    """
    Portfolio service interface providing C#-like contract definition.
    
    This interface defines all portfolio-related operations with strong typing
    and clear separation of concerns.
    """
    
    @abstractmethod
    async def get_portfolio_summary(self) -> PortfolioSummaryResponse:
        """
        Get comprehensive portfolio summary with all key metrics.
        
        Returns:
            PortfolioSummaryResponse: Complete portfolio overview
            
        Raises:
            PortfolioServiceException: If portfolio data cannot be retrieved
        """
        pass
    
    @abstractmethod
    async def get_current_holdings(self) -> List[HoldingResponse]:
        """
        Get list of all currently held assets with detailed information.
        
        Returns:
            List[HoldingResponse]: All current holdings
            
        Raises:
            PortfolioServiceException: If holdings data cannot be retrieved
        """
        pass
    
    @abstractmethod
    async def get_portfolio_holdings(self) -> PortfolioHoldingsResponse:
        """
        Get complete portfolio data including holdings and summary.
        
        Returns:
            PortfolioHoldingsResponse: Holdings with summary
            
        Raises:
            PortfolioServiceException: If portfolio data cannot be retrieved
        """
        pass
    
    @abstractmethod
    async def get_asset_performance(self, asset: str) -> HoldingResponse:
        """
        Get detailed performance data for a specific asset.
        
        Args:
            asset: Asset symbol (e.g., 'BTC', 'ETH')
            
        Returns:
            HoldingResponse: Asset performance data
            
        Raises:
            AssetNotFoundException: If asset is not found in portfolio
            PortfolioServiceException: If performance data cannot be calculated
        """
        pass
    
    @abstractmethod
    async def get_transaction_history(self, asset: Optional[str] = None) -> List[TransactionResponse]:
        """
        Get transaction history for all assets or a specific asset.
        
        Args:
            asset: Optional asset symbol to filter by
            
        Returns:
            List[TransactionResponse]: Transaction history
            
        Raises:
            PortfolioServiceException: If transaction data cannot be retrieved
        """
        pass
    
    @abstractmethod
    async def reconcile_portfolio(self, asset: Optional[str] = None) -> List[ReconciliationResponse]:
        """
        Perform portfolio reconciliation analysis.
        
        Args:
            asset: Optional asset symbol to reconcile (all assets if None)
            
        Returns:
            List[ReconciliationResponse]: Reconciliation results
            
        Raises:
            PortfolioServiceException: If reconciliation cannot be performed
        """
        pass
    
    @abstractmethod
    async def refresh_portfolio_data(self) -> bool:
        """
        Force refresh of portfolio data from exchange.
        
        Returns:
            bool: True if refresh was successful
            
        Raises:
            PortfolioServiceException: If data refresh fails
        """
        pass
