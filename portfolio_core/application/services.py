"""
Application Services

These services orchestrate domain logic and coordinate between
different domain services. They implement use cases and handle
the application workflow.
"""

import logging
from datetime import datetime, UTC
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

from ..domain.entities import Portfolio, Asset, Trade
from ..domain.services import FIFOCalculationService, PortfolioCalculationService
from ..domain.repositories import IPortfolioRepository, IMarketDataRepository
from ..domain.value_objects import AssetSymbol, Money, AssetAmount, TradeType, Timestamp

from .dtos import (
    PortfolioSummaryDTO,
    AssetHoldingDTO,
    TradeDTO,
    ReconciliationResultDTO,
    TransferSummaryDTO,
)
from .commands import (
    CalculatePortfolioCommand,
    RefreshPortfolioDataCommand,
    ReconcilePortfolioCommand,
)
from .queries import (
    GetPortfolioSummaryQuery,
    GetAssetHoldingsQuery,
    GetTradeHistoryQuery,
)

logger = logging.getLogger(__name__)


class PortfolioApplicationService:
    """
    Portfolio application service.
    
    Orchestrates portfolio operations and coordinates between domain services.
    This is the main entry point for all portfolio-related use cases.
    """
    
    def __init__(
        self,
        portfolio_repository: IPortfolioRepository,
        market_data_repository: IMarketDataRepository,
        fifo_service: FIFOCalculationService,
        portfolio_calculation_service: PortfolioCalculationService,
    ):
        """Initialize with required dependencies."""
        self.portfolio_repository = portfolio_repository
        self.market_data_repository = market_data_repository
        self.fifo_service = fifo_service
        self.portfolio_calculation_service = portfolio_calculation_service
    
    async def get_portfolio_summary(self, query: GetPortfolioSummaryQuery) -> PortfolioSummaryDTO:
        """
        Get comprehensive portfolio summary.
        
        This is the main use case for getting portfolio overview information.
        """
        try:
            logger.info(f"Getting portfolio summary for portfolio {query.portfolio_id}")
            
            # Get portfolio from repository
            portfolio = await self.portfolio_repository.get_portfolio(query.portfolio_id)
            if not portfolio:
                raise ValueError(f"Portfolio {query.portfolio_id} not found")
            
            # Get all trades grouped by asset
            trades_by_asset = await self.portfolio_repository.get_all_trades(query.portfolio_id)

            # Get current prices for all assets
            asset_symbols = list(trades_by_asset.keys())
            current_prices = await self.market_data_repository.get_current_prices(asset_symbols)

            # Get deposit history for all assets to account for external transfers
            deposits_by_asset = {}
            for asset_symbol in asset_symbols:
                try:
                    deposits = await self.portfolio_repository.get_deposit_history(
                        query.portfolio_id, asset_symbol
                    )
                    deposits_by_asset[asset_symbol] = deposits
                except Exception as e:
                    logger.warning(f"Failed to get deposits for {asset_symbol}: {e}")
                    deposits_by_asset[asset_symbol] = []

            # Update portfolio with latest calculations including deposit data
            updated_portfolio = self.portfolio_calculation_service.update_portfolio_from_trades(
                portfolio, trades_by_asset, current_prices, deposits_by_asset
            )
            
            # Save updated portfolio
            await self.portfolio_repository.save_portfolio(updated_portfolio)
            
            # Convert to DTO
            return PortfolioSummaryDTO(
                total_value=updated_portfolio.get_total_value().amount,
                total_cost_basis=updated_portfolio.get_total_cost_basis().amount,
                total_realized_pnl=updated_portfolio.get_total_realized_pnl().amount,
                total_unrealized_pnl=updated_portfolio.get_total_unrealized_pnl().amount,
                total_pnl=updated_portfolio.get_total_pnl().amount,
                return_percentage=updated_portfolio.get_return_percentage(),
                asset_count=updated_portfolio.get_asset_count(),
                last_updated=datetime.now(UTC),
            )
            
        except Exception as e:
            logger.error(f"Error getting portfolio summary: {e}")
            raise
    
    async def get_asset_holdings(self, query: GetAssetHoldingsQuery) -> List[AssetHoldingDTO]:
        """Get detailed asset holdings information."""
        try:
            logger.info(f"Getting asset holdings for portfolio {query.portfolio_id}")
            
            # Get portfolio
            portfolio = await self.portfolio_repository.get_portfolio(query.portfolio_id)
            if not portfolio:
                raise ValueError(f"Portfolio {query.portfolio_id} not found")
            
            # Get trades and update portfolio (similar to summary)
            trades_by_asset = await self.portfolio_repository.get_all_trades(query.portfolio_id)
            asset_symbols = list(trades_by_asset.keys())
            current_prices = await self.market_data_repository.get_current_prices(asset_symbols)

            # Get deposit history for all assets to account for external transfers
            deposits_by_asset = {}
            for asset_symbol in asset_symbols:
                try:
                    deposits = await self.portfolio_repository.get_deposit_history(
                        query.portfolio_id, asset_symbol
                    )
                    deposits_by_asset[asset_symbol] = deposits
                except Exception as e:
                    logger.warning(f"Failed to get deposits for {asset_symbol}: {e}")
                    deposits_by_asset[asset_symbol] = []

            updated_portfolio = self.portfolio_calculation_service.update_portfolio_from_trades(
                portfolio, trades_by_asset, current_prices, deposits_by_asset
            )
            
            # Convert assets to DTOs
            holdings = []
            total_portfolio_value = updated_portfolio.get_total_value().amount
            
            for asset in updated_portfolio.assets:
                # Filter out zero balances unless explicitly requested
                # Use a very small threshold instead of exact zero to handle precision issues
                if not query.include_zero_balances:
                    # Consider amounts smaller than 0.000000001 as zero (dust threshold)
                    dust_threshold = Decimal("0.000000001")
                    if asset.holdings.amount <= dust_threshold:
                        continue
                
                # Filter by asset symbols if specified
                if query.asset_symbols and str(asset.symbol) not in query.asset_symbols:
                    continue
                
                # Filter by minimum value threshold
                current_value = asset.get_current_value().amount
                if query.min_value_threshold and current_value < Decimal(str(query.min_value_threshold)):
                    continue
                
                # Calculate portfolio percentage
                portfolio_percentage = self.portfolio_calculation_service.calculate_asset_allocation(
                    current_value, total_portfolio_value
                )
                
                holdings.append(AssetHoldingDTO(
                    symbol=str(asset.symbol),
                    amount=asset.holdings.amount,
                    cost_basis=asset.cost_basis.amount,
                    current_value=current_value,
                    current_price=asset.current_price.amount,
                    realized_pnl=asset.realized_pnl.amount,
                    unrealized_pnl=asset.get_unrealized_pnl().amount,
                    total_pnl=asset.get_total_pnl().amount,
                    return_percentage=asset.get_return_percentage(),
                    portfolio_percentage=portfolio_percentage,
                ))
            
            # Sort holdings
            if query.sort_by == "value":
                holdings.sort(key=lambda h: h.current_value, reverse=query.sort_descending)
            elif query.sort_by == "allocation":
                holdings.sort(key=lambda h: h.portfolio_percentage, reverse=query.sort_descending)
            elif query.sort_by == "pnl":
                holdings.sort(key=lambda h: h.total_pnl, reverse=query.sort_descending)
            elif query.sort_by == "symbol":
                holdings.sort(key=lambda h: h.symbol, reverse=query.sort_descending)
            
            return holdings
            
        except Exception as e:
            logger.error(f"Error getting asset holdings: {e}")
            raise
    
    async def calculate_portfolio(self, command: CalculatePortfolioCommand) -> PortfolioSummaryDTO:
        """
        Calculate portfolio P&L and holdings.
        
        This is the main calculation use case that uses the FIFO service.
        """
        try:
            logger.info(f"Calculating portfolio {command.portfolio_id}")
            
            # Force refresh data if requested
            if command.force_refresh:
                await self.refresh_portfolio_data(RefreshPortfolioDataCommand(
                    portfolio_id=command.portfolio_id
                ))
            
            # Get portfolio summary (which triggers calculation)
            summary_query = GetPortfolioSummaryQuery(
                portfolio_id=command.portfolio_id,
                include_performance_metrics=True
            )
            
            return await self.get_portfolio_summary(summary_query)
            
        except Exception as e:
            logger.error(f"Error calculating portfolio: {e}")
            raise
    
    async def refresh_portfolio_data(self, command: RefreshPortfolioDataCommand) -> bool:
        """Refresh portfolio data from external sources."""
        try:
            logger.info(f"Refreshing portfolio data for {command.portfolio_id}")
            
            # Get portfolio assets
            asset_symbols = await self.portfolio_repository.get_portfolio_assets(command.portfolio_id)
            
            if command.refresh_prices:
                # Refresh current prices (this will update the market data repository cache)
                await self.market_data_repository.get_current_prices(list(asset_symbols))
                logger.info(f"Refreshed prices for {len(asset_symbols)} assets")
            
            # Additional refresh logic can be added here
            # (e.g., refresh trades, balances, etc.)
            
            return True
            
        except Exception as e:
            logger.error(f"Error refreshing portfolio data: {e}")
            return False


class MarketDataApplicationService:
    """
    Market data application service.
    
    Handles market data operations and price management.
    """
    
    def __init__(self, market_data_repository: IMarketDataRepository):
        """Initialize with market data repository."""
        self.market_data_repository = market_data_repository
    
    async def get_current_price(self, asset_symbol: str) -> Decimal:
        """Get current price for an asset."""
        try:
            asset = AssetSymbol(asset_symbol)
            price = await self.market_data_repository.get_current_price(asset)
            return price.amount
            
        except Exception as e:
            logger.error(f"Error getting current price for {asset_symbol}: {e}")
            raise
    
    async def get_current_prices(self, asset_symbols: List[str]) -> Dict[str, Decimal]:
        """Get current prices for multiple assets."""
        try:
            assets = [AssetSymbol(symbol) for symbol in asset_symbols]
            prices = await self.market_data_repository.get_current_prices(assets)
            
            return {str(asset): price.amount for asset, price in prices.items()}
            
        except Exception as e:
            logger.error(f"Error getting current prices: {e}")
            raise
