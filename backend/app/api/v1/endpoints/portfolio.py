"""
Portfolio API endpoints.

Provides strongly typed REST endpoints for portfolio management operations
with comprehensive error handling and documentation.
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from ....core.dependencies import PortfolioServiceDep
from ....core.exceptions import AssetNotFoundException, PortfolioServiceException
from ....models.portfolio import (
    HoldingResponse,
    PortfolioHoldingsResponse,
    PortfolioSummaryResponse,
    ReconciliationResponse,
    TransactionResponse,
)
from ....models.chat import RefreshDataResponse

router = APIRouter()


@router.get(
    "/summary",
    response_model=PortfolioSummaryResponse,
    summary="Get Portfolio Summary",
    description="Get comprehensive portfolio summary with total value, P&L, and key metrics",
)
async def get_portfolio_summary(portfolio_service: PortfolioServiceDep) -> PortfolioSummaryResponse:
    """
    Get comprehensive portfolio summary.

    Returns complete portfolio overview including:
    - Total portfolio value and cost basis
    - Realized and unrealized P&L
    - Total return percentage
    - Asset count and last update timestamp

    Args:
        portfolio_service: Injected portfolio service

    Returns:
        PortfolioSummaryResponse: Complete portfolio summary

    Raises:
        HTTPException: If portfolio data cannot be retrieved
    """
    try:
        return await portfolio_service.get_portfolio_summary()
    except PortfolioServiceException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/holdings",
    response_model=List[HoldingResponse],
    summary="Get Current Holdings",
    description="Get list of all currently held assets with detailed information",
)
async def get_current_holdings(portfolio_service: PortfolioServiceDep) -> List[HoldingResponse]:
    """
    Get all current portfolio holdings.

    Returns detailed information for each held asset including:
    - Current quantity and market value
    - Cost basis and P&L calculations
    - Portfolio allocation percentage
    - Current market price

    Args:
        portfolio_service: Injected portfolio service

    Returns:
        List[HoldingResponse]: All current holdings

    Raises:
        HTTPException: If holdings data cannot be retrieved
    """
    try:
        return await portfolio_service.get_current_holdings()
    except PortfolioServiceException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/holdings/complete",
    response_model=PortfolioHoldingsResponse,
    summary="Get Complete Portfolio Data",
    description="Get complete portfolio data including holdings and summary",
)
async def get_portfolio_holdings(
    portfolio_service: PortfolioServiceDep,
) -> PortfolioHoldingsResponse:
    """
    Get complete portfolio data including holdings and summary.

    This endpoint combines portfolio summary and holdings data
    for efficient frontend data loading.

    Args:
        portfolio_service: Injected portfolio service

    Returns:
        PortfolioHoldingsResponse: Complete portfolio data

    Raises:
        HTTPException: If portfolio data cannot be retrieved
    """
    try:
        return await portfolio_service.get_portfolio_holdings()
    except PortfolioServiceException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/performance/{asset}",
    response_model=HoldingResponse,
    summary="Get Asset Performance",
    description="Get detailed performance data for a specific asset",
)
async def get_asset_performance(
    asset: str, portfolio_service: PortfolioServiceDep
) -> HoldingResponse:
    """
    Get detailed performance data for a specific asset.

    Args:
        asset: Asset symbol (e.g., 'BTC', 'ETH')
        portfolio_service: Injected portfolio service

    Returns:
        HoldingResponse: Asset performance data

    Raises:
        HTTPException: If asset is not found or data cannot be retrieved
    """
    try:
        return await portfolio_service.get_asset_performance(asset.upper())
    except AssetNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PortfolioServiceException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/transactions",
    response_model=List[TransactionResponse],
    summary="Get Transaction History",
    description="Get transaction history for all assets or a specific asset",
)
async def get_transaction_history(
    portfolio_service: PortfolioServiceDep,
    asset: Optional[str] = Query(None, description="Optional asset symbol to filter by"),
) -> List[TransactionResponse]:
    """
    Get transaction history.

    Args:
        portfolio_service: Injected portfolio service
        asset: Optional asset symbol to filter by

    Returns:
        List[TransactionResponse]: Transaction history

    Raises:
        HTTPException: If transaction data cannot be retrieved
    """
    try:
        return await portfolio_service.get_transaction_history(asset.upper() if asset else None)
    except PortfolioServiceException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/reconciliation",
    response_model=List[ReconciliationResponse],
    summary="Portfolio Reconciliation",
    description="Perform portfolio reconciliation analysis",
)
async def reconcile_portfolio(
    portfolio_service: PortfolioServiceDep,
    asset: Optional[str] = Query(None, description="Optional asset symbol to reconcile"),
) -> List[ReconciliationResponse]:
    """
    Perform portfolio reconciliation analysis.

    Compares FIFO calculations with actual balances and provides
    explanations for any discrepancies.

    Args:
        portfolio_service: Injected portfolio service
        asset: Optional asset symbol to reconcile (all assets if None)

    Returns:
        List[ReconciliationResponse]: Reconciliation results

    Raises:
        HTTPException: If reconciliation cannot be performed
    """
    try:
        return await portfolio_service.reconcile_portfolio(asset.upper() if asset else None)
    except PortfolioServiceException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/refresh",
    response_model=RefreshDataResponse,
    summary="Refresh Portfolio Data",
    description="Force refresh of portfolio data from exchange",
)
async def refresh_portfolio_data(portfolio_service: PortfolioServiceDep) -> RefreshDataResponse:
    """
    Force refresh of portfolio data from exchange.

    This endpoint triggers a fresh data pull from Bitvavo API
    and updates the cached portfolio data.

    Args:
        portfolio_service: Injected portfolio service

    Returns:
        dict: Refresh status

    Raises:
        HTTPException: If data refresh fails
    """
    try:
        success = await portfolio_service.refresh_portfolio_data()
        return RefreshDataResponse(
            success=success,
            message=(
                "Portfolio data refreshed successfully"
                if success
                else "Failed to refresh portfolio data"
            ),
        )
    except PortfolioServiceException as e:
        raise HTTPException(status_code=500, detail=str(e))
