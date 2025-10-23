"""
Market service implementation.

Provides business logic for market data operations with full type safety
and integration with existing market analysis logic.
"""

import logging
from datetime import datetime, UTC
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
from .base_service import BaseService
from .interfaces.bitvavo_client import IBitvavoClient
from .interfaces.market_service import IMarketService
from ..shared.market_core import (
    get_market_prices,
    calculate_price_change_24h,
    get_market_summary,
    TechnicalAnalyzer,
)


class MarketService(BaseService, IMarketService):
    """
    Market service implementation providing C#-like business logic layer.

    This service integrates with existing market analysis logic
    and provides strongly typed responses for the API.
    """

    def __init__(self, settings: Settings, bitvavo_client: IBitvavoClient):
        """
        Initialize market service with dependencies.

        Args:
            settings: Application settings
            bitvavo_client: Bitvavo client for API operations
        """
        super().__init__(settings, "MarketService")
        self.bitvavo_client = bitvavo_client
        self._market_data_cache: Optional[Dict] = None
        self._cache_timestamp: Optional[datetime] = None

    async def get_current_prices(
        self, assets: Optional[List[str]] = None
    ) -> Dict[str, PriceResponse]:
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
            self.logger.info(f"Getting current prices for assets: {assets or 'all'}")

            # Get Bitvavo client instance
            client = self.bitvavo_client._get_client()

            # Use real market data from existing logic
            market_prices = get_market_prices(client, assets)

            # Convert to PriceResponse objects
            price_responses = {}
            for asset, price_data in market_prices.items():
                try:
                    # Calculate 24h change
                    price_change_24h = calculate_price_change_24h(client, asset)

                    # Mock volume for now (would need separate API call)
                    volume_24h = Decimal("1000000.00")  # Placeholder

                    price_responses[asset] = PriceResponse(
                        asset=asset,
                        price_eur=price_data["price_eur"],
                        price_change_24h=price_change_24h,
                        volume_24h=volume_24h,
                        last_updated=datetime.now(UTC),
                    )
                except Exception as e:
                    self.logger.warning(f"Error processing price for {asset}: {e}")
                    continue

            return price_responses

        except Exception as e:
            self.logger.error(f"Error getting current prices: {e}")
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
            self.logger.info("Getting comprehensive market data")

            # Get real price data
            prices = await self.get_current_prices()

            # Get market summary from real data
            client = self.bitvavo_client._get_client()
            market_summary = get_market_summary(client)

            # Sort by price change for top gainers/losers
            sorted_prices = sorted(
                prices.values(), key=lambda x: x.price_change_24h, reverse=True
            )

            # Convert trend string to enum
            trend_mapping = {
                "BULLISH": TrendDirection.BULLISH,
                "BEARISH": TrendDirection.BEARISH,
                "NEUTRAL": TrendDirection.NEUTRAL,
                "UNKNOWN": TrendDirection.NEUTRAL,
            }

            return MarketDataResponse(
                prices=prices,
                market_cap_total=market_summary["total_market_cap"],
                market_trend=trend_mapping.get(market_summary["trend"], TrendDirection.NEUTRAL),
                fear_greed_index=market_summary["fear_greed_index"],
                top_gainers=sorted_prices[:3] if len(sorted_prices) >= 3 else sorted_prices,
                top_losers=sorted_prices[-2:] if len(sorted_prices) >= 2 else [],
                last_updated=datetime.now(UTC),
            )

        except Exception as e:
            self.logger.error(f"Error getting market data: {e}")
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
            self.logger.info("Analyzing market opportunities")

            # Analyze real market data for opportunities
            prices = await self.get_current_prices()

            opportunities = []

            # Handle case when no prices are available
            if not prices:
                return MarketOpportunitiesResponse(
                    opportunities=[],
                    market_sentiment="Unknown",
                    analysis_summary="No market data available for analysis",
                    last_updated=datetime.now(UTC),
                )

            # Find opportunities based on real price movements
            for asset, price_data in prices.items():
                price_change = price_data.price_change_24h
                current_price = price_data.price_eur

                # Strong positive momentum opportunity
                if price_change > 5:
                    opportunities.append(MarketOpportunityResponse(
                        asset=asset,
                        opportunity_type="Momentum Play",
                        potential_return=price_change * Decimal("1.5"),  # Projected continuation
                        risk_level=RiskLevel.MEDIUM,
                        time_horizon="1-2 weeks",
                        reasoning=f"Strong 24h gain of {price_change}% suggests continued momentum at €{current_price}",
                        confidence_score=Decimal("0.75"),
                    ))

                # Oversold opportunity
                elif price_change < -5:
                    opportunities.append(MarketOpportunityResponse(
                        asset=asset,
                        opportunity_type="Oversold Bounce",
                        potential_return=abs(price_change) * Decimal("0.8"),  # Recovery potential
                        risk_level=RiskLevel.HIGH,
                        time_horizon="2-4 weeks",
                        reasoning=f"24h decline of {price_change}% may present buying opportunity at €{current_price}",
                        confidence_score=Decimal("0.65"),
                    ))

            # Determine market sentiment based on overall price movements
            positive_moves = sum(1 for p in prices.values() if p.price_change_24h > 0)
            total_assets = len(prices)

            if positive_moves / total_assets > 0.6:
                sentiment = "Bullish"
                summary = f"Market showing strength with {positive_moves}/{total_assets} assets in the green"
            elif positive_moves / total_assets < 0.4:
                sentiment = "Bearish"
                summary = f"Market under pressure with {total_assets - positive_moves}/{total_assets} assets declining"
            else:
                sentiment = "Mixed"
                summary = f"Market showing mixed signals with {positive_moves}/{total_assets} assets positive"

            return MarketOpportunitiesResponse(
                opportunities=opportunities[:5],  # Limit to top 5 opportunities
                market_sentiment=sentiment,
                analysis_summary=summary,
                last_updated=datetime.now(UTC),
            )

        except Exception as e:
            self.logger.error(f"Error analyzing market opportunities: {e}")
            raise MarketServiceException(
                f"Failed to analyze market opportunities: {str(e)}"
            )

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
            self.logger.info(f"Getting technical analysis for {asset}")

            # Check if asset exists in our price data
            prices = await self.get_current_prices([asset])
            if asset not in prices:
                raise AssetNotFoundException(asset)

            # Use real price data for technical analysis
            current_price = prices[asset].price_eur
            price_change = prices[asset].price_change_24h

            # Simple technical analysis based on real price data
            if price_change > 5:
                trend_direction = TrendDirection.BULLISH
                recommendation = "Buy - Strong positive momentum"
                risk_level = RiskLevel.MEDIUM
                rsi_signal = "buy"
            elif price_change < -5:
                trend_direction = TrendDirection.BEARISH
                recommendation = "Sell - Strong negative momentum"
                risk_level = RiskLevel.HIGH
                rsi_signal = "sell"
            else:
                trend_direction = TrendDirection.NEUTRAL
                recommendation = "Hold - Neutral momentum"
                risk_level = RiskLevel.LOW
                rsi_signal = "hold"

            # Calculate support/resistance based on current price
            support_levels = [
                current_price * Decimal("0.95"),  # 5% below
                current_price * Decimal("0.90"),  # 10% below
            ]
            resistance_levels = [
                current_price * Decimal("1.05"),  # 5% above
                current_price * Decimal("1.10"),  # 10% above
            ]

            # Create indicators based on real data
            indicators = [
                TechnicalIndicatorResponse(
                    indicator_name="Price Change 24h",
                    value=price_change,
                    signal=rsi_signal,
                    confidence=Decimal("0.8"),
                ),
                TechnicalIndicatorResponse(
                    indicator_name="Current Price",
                    value=current_price,
                    signal=rsi_signal,
                    confidence=Decimal("0.9"),
                ),
                TechnicalIndicatorResponse(
                    indicator_name="Trend Analysis",
                    value=Decimal(str(abs(price_change))),
                    signal=rsi_signal,
                    confidence=Decimal("0.75"),
                ),
            ]

            return TechnicalAnalysisResponse(
                asset=asset,
                trend_direction=trend_direction,
                indicators=indicators,
                support_levels=support_levels,
                resistance_levels=resistance_levels,
                recommendation=recommendation,
                risk_level=risk_level,
                analysis_timestamp=datetime.now(UTC),
            )

        except AssetNotFoundException:
            raise
        except Exception as e:
            self.logger.error(f"Error getting technical analysis for {asset}: {e}")
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
            self.logger.info(f"Getting price for asset: {asset}")

            prices = await self.get_current_prices([asset])

            if asset not in prices:
                raise AssetNotFoundException(asset)

            return prices[asset]

        except AssetNotFoundException:
            raise
        except Exception as e:
            self.logger.error(f"Error getting asset price for {asset}: {e}")
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
            self.logger.info("Refreshing market data from external sources")

            # Clear cache and force fresh data fetch from Bitvavo
            self._market_data_cache = None
            self._cache_timestamp = None

            # Test connection by fetching a sample price
            try:
                client = self.bitvavo_client._get_client()
                test_prices = get_market_prices(client, ["BTC"])

                if test_prices:
                    self.logger.info("Market data refresh successful")
                    return True
                else:
                    self.logger.warning("Market data refresh returned no data")
                    return False

            except Exception as e:
                self.logger.error(f"Market data refresh failed: {e}")
                return False

        except Exception as e:
            self.logger.error(f"Error refreshing market data: {e}")
            raise MarketServiceException(f"Failed to refresh market data: {str(e)}")
