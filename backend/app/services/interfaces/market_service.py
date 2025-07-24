"""
Market service interface definition.

Defines the contract for market data and analysis operations
with full type safety and clear method signatures.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from ...models.market import (
    MarketDataResponse,
    MarketOpportunitiesResponse,
    PriceResponse,
    TechnicalAnalysisResponse,
)


class IMarketService(ABC):
    """
    Market service interface providing C#-like contract definition.
    
    This interface defines all market-related operations with strong typing
    and clear separation of concerns.
    """
    
    @abstractmethod
    async def get_current_prices(self, assets: Optional[List[str]] = None) -> Dict[str, PriceResponse]:
        """
        Get current market prices for specified assets or all tracked assets.
        
        Args:
            assets: Optional list of asset symbols to get prices for
            
        Returns:
            Dict[str, PriceResponse]: Current prices by asset symbol
            
        Raises:
            MarketServiceException: If price data cannot be retrieved
        """
        pass
    
    @abstractmethod
    async def get_market_data(self) -> MarketDataResponse:
        """
        Get comprehensive market data including prices, trends, and sentiment.
        
        Returns:
            MarketDataResponse: Complete market overview
            
        Raises:
            MarketServiceException: If market data cannot be retrieved
        """
        pass
    
    @abstractmethod
    async def get_market_opportunities(self) -> MarketOpportunitiesResponse:
        """
        Analyze current market for investment opportunities.
        
        Returns:
            MarketOpportunitiesResponse: Market opportunities analysis
            
        Raises:
            MarketServiceException: If opportunities analysis fails
        """
        pass
    
    @abstractmethod
    async def get_technical_analysis(self, asset: str) -> TechnicalAnalysisResponse:
        """
        Get technical analysis for a specific asset.
        
        Args:
            asset: Asset symbol for analysis
            
        Returns:
            TechnicalAnalysisResponse: Technical analysis results
            
        Raises:
            AssetNotFoundException: If asset is not found
            MarketServiceException: If technical analysis fails
        """
        pass
    
    @abstractmethod
    async def get_asset_price(self, asset: str) -> PriceResponse:
        """
        Get current price data for a specific asset.
        
        Args:
            asset: Asset symbol
            
        Returns:
            PriceResponse: Current price data
            
        Raises:
            AssetNotFoundException: If asset is not found
            MarketServiceException: If price data cannot be retrieved
        """
        pass
    
    @abstractmethod
    async def refresh_market_data(self) -> bool:
        """
        Force refresh of market data from external sources.
        
        Returns:
            bool: True if refresh was successful
            
        Raises:
            MarketServiceException: If data refresh fails
        """
        pass
