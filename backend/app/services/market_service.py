"""
Market service implementation.

Provides business logic for market data operations with full type safety
and integration with existing market analysis logic.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

from ..core.config import Settings
from ..core.exceptions import AssetNotFoundException, MarketServiceException
from ..models.market import (
    MarketDataResponse,
    MarketOpportunitiesResponse,
    MarketOpportunityResponse,
    PriceResponse,
    RiskLevel,
    TechnicalAnalysisResponse,
    TechnicalIndicatorResponse,
    TrendDirection,
)
from .interfaces.market_service import IMarketService

logger = logging.getLogger(__name__)


class MarketService(IMarketService):
    """
    Market service implementation providing C#-like business logic layer.
    
    This service integrates with existing market analysis logic
    and provides strongly typed responses for the API.
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize market service with configuration.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self._market_data_cache: Optional[Dict] = None
        self._cache_timestamp: Optional[datetime] = None
        
        logger.info("Market service initialized")
    
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
        try:
            logger.info(f"Getting current prices for assets: {assets or 'all'}")
            
            # TODO: Integrate with existing Bitvavo price fetching logic
            # For now, return mock data
            
            mock_prices = {
                "BTC": PriceResponse(
                    asset="BTC",
                    price_eur=Decimal("45000.00"),
                    price_change_24h=Decimal("2.5"),
                    volume_24h=Decimal("1500000.00"),
                    last_updated=datetime.utcnow()
                ),
                "ETH": PriceResponse(
                    asset="ETH",
                    price_eur=Decimal("3000.00"),
                    price_change_24h=Decimal("-1.2"),
                    volume_24h=Decimal("800000.00"),
                    last_updated=datetime.utcnow()
                ),
                "ADA": PriceResponse(
                    asset="ADA",
                    price_eur=Decimal("0.45"),
                    price_change_24h=Decimal("5.8"),
                    volume_24h=Decimal("200000.00"),
                    last_updated=datetime.utcnow()
                )
            }
            
            if assets:
                return {asset: mock_prices[asset] for asset in assets if asset in mock_prices}
            
            return mock_prices
            
        except Exception as e:
            logger.error(f"Error getting current prices: {e}")
            raise MarketServiceException(f"Failed to get current prices: {str(e)}")
    
    async def get_market_data(self) -> MarketDataResponse:
        """
        Get comprehensive market data including prices, trends, and sentiment.
        
        Returns:
            MarketDataResponse: Complete market overview
            
        Raises:
            MarketServiceException: If market data cannot be retrieved
        """
        try:
            logger.info("Getting comprehensive market data")
            
            prices = await self.get_current_prices()
            
            # Sort by price change for top gainers/losers
            sorted_prices = sorted(prices.values(), key=lambda x: x.price_change_24h, reverse=True)
            
            return MarketDataResponse(
                prices=prices,
                market_cap_total=Decimal("2500000000000.00"),  # Mock total market cap
                market_trend=TrendDirection.BULLISH,
                fear_greed_index=65,  # Mock Fear & Greed Index
                top_gainers=sorted_prices[:2],  # Top 2 gainers
                top_losers=sorted_prices[-1:],  # Top 1 loser
                last_updated=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error getting market data: {e}")
            raise MarketServiceException(f"Failed to get market data: {str(e)}")
    
    async def get_market_opportunities(self) -> MarketOpportunitiesResponse:
        """
        Analyze current market for investment opportunities.
        
        Returns:
            MarketOpportunitiesResponse: Market opportunities analysis
            
        Raises:
            MarketServiceException: If opportunities analysis fails
        """
        try:
            logger.info("Analyzing market opportunities")
            
            # TODO: Integrate with existing prediction engine logic
            # For now, return mock opportunities
            
            opportunities = [
                MarketOpportunityResponse(
                    asset="ADA",
                    opportunity_type="Technical Breakout",
                    potential_return=Decimal("15.0"),
                    risk_level=RiskLevel.MEDIUM,
                    time_horizon="2-4 weeks",
                    reasoning="Strong technical indicators suggest upward momentum with support at €0.40",
                    confidence_score=Decimal("0.75")
                ),
                MarketOpportunityResponse(
                    asset="ETH",
                    opportunity_type="DeFi Growth",
                    potential_return=Decimal("8.0"),
                    risk_level=RiskLevel.LOW,
                    time_horizon="1-3 months",
                    reasoning="Upcoming network upgrades and DeFi adoption driving long-term value",
                    confidence_score=Decimal("0.85")
                )
            ]
            
            return MarketOpportunitiesResponse(
                opportunities=opportunities,
                market_sentiment="Cautiously Optimistic",
                analysis_summary="Market showing signs of recovery with selective opportunities in altcoins",
                last_updated=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error analyzing market opportunities: {e}")
            raise MarketServiceException(f"Failed to analyze market opportunities: {str(e)}")
    
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
        try:
            logger.info(f"Getting technical analysis for {asset}")
            
            # Check if asset exists in our price data
            prices = await self.get_current_prices([asset])
            if asset not in prices:
                raise AssetNotFoundException(asset)
            
            # TODO: Integrate with existing technical analysis logic
            # For now, return mock analysis
            
            indicators = [
                TechnicalIndicatorResponse(
                    indicator_name="RSI",
                    value=Decimal("65.5"),
                    signal="hold",
                    confidence=Decimal("0.8")
                ),
                TechnicalIndicatorResponse(
                    indicator_name="MACD",
                    value=Decimal("1.25"),
                    signal="buy",
                    confidence=Decimal("0.7")
                ),
                TechnicalIndicatorResponse(
                    indicator_name="Moving Average (50)",
                    value=Decimal("42000.00"),
                    signal="buy",
                    confidence=Decimal("0.75")
                )
            ]
            
            return TechnicalAnalysisResponse(
                asset=asset,
                trend_direction=TrendDirection.BULLISH,
                indicators=indicators,
                support_levels=[Decimal("42000.00"), Decimal("40000.00")],
                resistance_levels=[Decimal("47000.00"), Decimal("50000.00")],
                recommendation="Moderate Buy - Technical indicators suggest upward momentum",
                risk_level=RiskLevel.MEDIUM,
                analysis_timestamp=datetime.utcnow()
            )
            
        except AssetNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error getting technical analysis for {asset}: {e}")
            raise MarketServiceException(f"Failed to get technical analysis: {str(e)}")
    
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
        try:
            logger.info(f"Getting price for asset: {asset}")
            
            prices = await self.get_current_prices([asset])
            
            if asset not in prices:
                raise AssetNotFoundException(asset)
            
            return prices[asset]
            
        except AssetNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error getting asset price for {asset}: {e}")
            raise MarketServiceException(f"Failed to get asset price: {str(e)}")
    
    async def refresh_market_data(self) -> bool:
        """
        Force refresh of market data from external sources.
        
        Returns:
            bool: True if refresh was successful
            
        Raises:
            MarketServiceException: If data refresh fails
        """
        try:
            logger.info("Refreshing market data from external sources")
            
            # TODO: Integrate with existing market data fetching logic
            # Clear cache and force fresh data fetch
            
            self._market_data_cache = None
            self._cache_timestamp = None
            
            # Mock successful refresh
            return True
            
        except Exception as e:
            logger.error(f"Error refreshing market data: {e}")
            raise MarketServiceException(f"Failed to refresh market data: {str(e)}")
