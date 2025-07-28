"""
Market API endpoints.

Provides strongly typed REST endpoints for market data and analysis operations
with comprehensive error handling and documentation.
"""

from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from ....core.dependencies import MarketServiceDep
from ....core.exceptions import AssetNotFoundException, MarketServiceException
from ....models.market import (
    MarketDataResponse,
    MarketOpportunitiesResponse,
    PriceResponse,
    TechnicalAnalysisResponse,
)

router = APIRouter()


@router.get(
    "/data",
    response_model=MarketDataResponse,
    summary="Get Market Data",
    description="Get comprehensive market data including prices, trends, and sentiment",
)
async def get_market_data(market_service: MarketServiceDep) -> MarketDataResponse:
    """
    Get comprehensive market data.

    Returns complete market overview including:
    - Current prices for all tracked assets
    - Market trends and sentiment indicators
    - Top gainers and losers
    - Fear & Greed Index

    Args:
        market_service: Injected market service

    Returns:
        MarketDataResponse: Complete market overview

    Raises:
        HTTPException: If market data cannot be retrieved
    """
    try:
        return await market_service.get_market_data()
    except MarketServiceException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/prices",
    response_model=Dict[str, PriceResponse],
    summary="Get Current Prices",
    description="Get current market prices for specified assets or all tracked assets",
)
async def get_current_prices(
    market_service: MarketServiceDep,
    assets: Optional[List[str]] = Query(None, description="Optional list of asset symbols"),
) -> Dict[str, PriceResponse]:
    """
    Get current market prices.

    Args:
        market_service: Injected market service
        assets: Optional list of asset symbols to get prices for

    Returns:
        Dict[str, PriceResponse]: Current prices by asset symbol

    Raises:
        HTTPException: If price data cannot be retrieved
    """
    try:
        # Convert to uppercase for consistency
        asset_list = [asset.upper() for asset in assets] if assets else None
        return await market_service.get_current_prices(asset_list)
    except MarketServiceException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/prices/{asset}",
    response_model=PriceResponse,
    summary="Get Asset Price",
    description="Get current price data for a specific asset",
)
async def get_asset_price(asset: str, market_service: MarketServiceDep) -> PriceResponse:
    """
    Get current price data for a specific asset.

    Args:
        asset: Asset symbol (e.g., 'BTC', 'ETH')
        market_service: Injected market service

    Returns:
        PriceResponse: Current price data

    Raises:
        HTTPException: If asset is not found or price data cannot be retrieved
    """
    try:
        return await market_service.get_asset_price(asset.upper())
    except AssetNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except MarketServiceException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/opportunities",
    response_model=MarketOpportunitiesResponse,
    summary="Get Market Opportunities",
    description="Analyze current market for investment opportunities",
)
async def get_market_opportunities(market_service: MarketServiceDep) -> MarketOpportunitiesResponse:
    """
    Analyze current market for investment opportunities.

    Returns analysis of potential investment opportunities including:
    - Identified opportunities with risk assessment
    - Market sentiment analysis
    - Recommended time horizons
    - Confidence scores

    Args:
        market_service: Injected market service

    Returns:
        MarketOpportunitiesResponse: Market opportunities analysis

    Raises:
        HTTPException: If opportunities analysis fails
    """
    try:
        return await market_service.get_market_opportunities()
    except MarketServiceException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/analysis/{asset}",
    response_model=TechnicalAnalysisResponse,
    summary="Get Technical Analysis",
    description="Get technical analysis for a specific asset",
)
async def get_technical_analysis(
    asset: str, market_service: MarketServiceDep
) -> TechnicalAnalysisResponse:
    """
    Get technical analysis for a specific asset.

    Returns comprehensive technical analysis including:
    - Technical indicators and signals
    - Support and resistance levels
    - Trend direction analysis
    - Trading recommendations

    Args:
        asset: Asset symbol for analysis
        market_service: Injected market service

    Returns:
        TechnicalAnalysisResponse: Technical analysis results

    Raises:
        HTTPException: If asset is not found or analysis fails
    """
    try:
        return await market_service.get_technical_analysis(asset.upper())
    except AssetNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except MarketServiceException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/refresh",
    response_model=dict,
    summary="Refresh Market Data",
    description="Force refresh of market data from external sources",
)
async def refresh_market_data(market_service: MarketServiceDep) -> dict:
    """
    Force refresh of market data from external sources.

    This endpoint triggers a fresh data pull from market data providers
    and updates the cached market data.

    Args:
        market_service: Injected market service

    Returns:
        dict: Refresh status

    Raises:
        HTTPException: If data refresh fails
    """
    try:
        success = await market_service.refresh_market_data()
        return {
            "success": success,
            "message": (
                "Market data refreshed successfully" if success else "Failed to refresh market data"
            ),
        }
    except MarketServiceException as e:
        raise HTTPException(status_code=500, detail=str(e))
