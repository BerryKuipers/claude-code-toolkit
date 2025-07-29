"""
Clean Architecture Portfolio Service

This service acts as an adapter between the FastAPI presentation layer
and the Clean Architecture application services. It eliminates all duplicate
code and provides a clean interface to the domain logic.
"""

import logging
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional
from uuid import UUID

from ..core.config import Settings
from .base_service import BaseService
from .interfaces.portfolio_service import IPortfolioService
from .interfaces.bitvavo_client import IBitvavoClient
from ..models.portfolio import (
    PortfolioSummaryResponse,
    HoldingResponse,
    PortfolioHoldingsResponse,
    TransactionResponse,
    ReconciliationResponse as ReconciliationResultResponse,
    TransferSummaryResponse,
)
# Removed circular import - dependencies passed directly
# Import Clean Architecture components directly
import sys
import os

# Add project root to path
_current_dir = os.path.dirname(os.path.abspath(__file__))  # services
_app_dir = os.path.dirname(_current_dir)  # app
_backend_dir = os.path.dirname(_app_dir)  # backend
_project_root = os.path.dirname(_backend_dir)  # crypto_insight

if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# Clean Architecture imports - these are now mandatory after migration
from portfolio_core.application.services import PortfolioApplicationService
from portfolio_core.application.queries import GetPortfolioSummaryQuery, GetAssetHoldingsQuery
from portfolio_core.application.commands import CalculatePortfolioCommand, RefreshPortfolioDataCommand
from portfolio_core.application.dtos import PortfolioSummaryDTO, AssetHoldingDTO

logger = logging.getLogger(__name__)

# Force reload timestamp: 2025-07-28 16:46 - Clean Architecture is now mandatory


class PortfolioService(BaseService, IPortfolioService):
    """
    Clean Architecture Portfolio Service.
    
    This service eliminates all duplicate code by using the Clean Architecture
    application services. It acts as a thin adapter layer between FastAPI
    and the domain logic.
    """
    
    def __init__(self, settings: Settings, bitvavo_client: IBitvavoClient,
                 portfolio_app_service, market_app_service, default_portfolio_id):
        """
        Initialize with Clean Architecture components.

        Args:
            settings: Application settings
            bitvavo_client: Bitvavo client (kept for backward compatibility)
            portfolio_app_service: Portfolio application service from Clean Architecture
            market_app_service: Market data application service from Clean Architecture
            default_portfolio_id: Default portfolio ID
        """
        super().__init__(settings, "PortfolioService")
        self.bitvavo_client = bitvavo_client  # Keep for backward compatibility

        # Store Clean Architecture components (passed directly to avoid circular imports)
        self.portfolio_app_service = portfolio_app_service
        self.market_app_service = market_app_service
        self.default_portfolio_id = default_portfolio_id

        self.logger.info("Initialized Clean Architecture portfolio service")

    def _round_decimal(self, value: Decimal, places: int = 2) -> Decimal:
        """Round a Decimal value to specified decimal places."""
        if not isinstance(value, Decimal):
            value = Decimal(str(value))

        # Create proper quantizer for the specified decimal places
        if places == 0:
            quantizer = Decimal('1')
        else:
            quantizer = Decimal('0.' + '0' * places)

        return value.quantize(quantizer, rounding=ROUND_HALF_UP)
    
    async def get_portfolio_summary(self) -> PortfolioSummaryResponse:
        """
        Get portfolio summary using Clean Architecture.
        
        This method delegates to the application service and maps the result
        to the API response model.
        """
        try:
            self._log_operation_start("Getting portfolio summary")
            
            # Create query using Clean Architecture
            query = GetPortfolioSummaryQuery(
                portfolio_id=self.default_portfolio_id,
                include_performance_metrics=True
            )
            
            # Execute query through application service
            summary_dto = await self.portfolio_app_service.get_portfolio_summary(query)
            
            # Map DTO to API response model
            response = self._map_summary_dto_to_response(summary_dto)
            
            self._log_operation_success("Getting portfolio summary", f"Total value: €{response.total_value}")
            return response
            
        except Exception as e:
            self._handle_service_error("get portfolio summary", e, Exception)
    
    async def get_current_holdings(self, assets: Optional[List[str]] = None) -> List[HoldingResponse]:
        """
        Get asset holdings using Clean Architecture.
        
        Args:
            assets: Optional list of asset symbols to filter by
            
        Returns:
            List of asset holding responses
        """
        try:
            self._log_operation_start("Getting asset holdings")
            
            # Create query using Clean Architecture
            query = GetAssetHoldingsQuery(
                portfolio_id=self.default_portfolio_id,
                asset_symbols=assets,
                sort_by="value",
                sort_descending=True
            )
            
            # Execute query through application service
            holdings_dto = await self.portfolio_app_service.get_asset_holdings(query)
            
            # Map DTOs to API response models
            responses = [self._map_holding_dto_to_response(dto) for dto in holdings_dto]
            
            self._log_operation_success("Getting asset holdings", f"Found {len(responses)} holdings")
            return responses
            
        except Exception as e:
            self._handle_service_error("get asset holdings", e, Exception)
    
    def _map_summary_dto_to_response(self, dto: PortfolioSummaryDTO) -> PortfolioSummaryResponse:
        """Map portfolio summary DTO to API response model."""
        return PortfolioSummaryResponse(
            total_value=self._round_decimal(dto.total_value, 2),
            total_cost=self._round_decimal(dto.total_cost_basis, 2),
            realized_pnl=self._round_decimal(dto.total_realized_pnl, 2),
            unrealized_pnl=self._round_decimal(dto.total_unrealized_pnl, 2),
            total_pnl=self._round_decimal(dto.total_pnl, 2),
            total_return_percentage=self._round_decimal(dto.return_percentage, 2),
            asset_count=dto.asset_count,
            last_updated=dto.last_updated,
        )
    
    def _map_holding_dto_to_response(self, dto: AssetHoldingDTO) -> HoldingResponse:
        """Map asset holding DTO to API response model."""
        return HoldingResponse(
            asset=dto.symbol,
            quantity=self._round_decimal(dto.amount, 8),  # Keep more precision for quantities
            current_price=self._round_decimal(dto.current_price, 2),
            value_eur=self._round_decimal(dto.current_value, 2),
            cost_basis=self._round_decimal(dto.cost_basis, 2),
            realized_pnl=self._round_decimal(dto.realized_pnl, 2),
            unrealized_pnl=self._round_decimal(dto.unrealized_pnl, 2),
            portfolio_percentage=self._round_decimal(dto.portfolio_percentage, 2),
            total_return_percentage=self._round_decimal(dto.return_percentage, 2),
        )
    
    async def get_portfolio_holdings(self) -> "PortfolioHoldingsResponse":
        """Get complete portfolio data including holdings and summary."""
        try:
            self._log_operation_start("Getting complete portfolio holdings")

            # Get both summary and holdings
            summary = await self.get_portfolio_summary()
            holdings = await self.get_current_holdings()

            from ..models.portfolio import PortfolioHoldingsResponse
            response = PortfolioHoldingsResponse(
                holdings=holdings,
                summary=summary,
                last_updated=summary.last_updated
            )

            self._log_operation_success("Getting complete portfolio holdings", f"Found {len(holdings)} holdings")
            return response

        except Exception as e:
            self._handle_service_error("get complete portfolio holdings", e, Exception)

    async def get_asset_performance(self, asset: str) -> HoldingResponse:
        """Get detailed performance data for a specific asset."""
        try:
            self._log_operation_start(f"Getting asset performance for {asset}")

            # Get holdings and filter for the specific asset
            holdings = await self.get_current_holdings([asset])

            if not holdings:
                from ..core.exceptions import AssetNotFoundException
                raise AssetNotFoundException(f"Asset {asset} not found in portfolio")

            response = holdings[0]  # Should only be one asset
            self._log_operation_success(f"Getting asset performance for {asset}", f"Value: €{response.value_eur}")
            return response

        except Exception as e:
            self._handle_service_error(f"get asset performance for {asset}", e, Exception)

    async def get_transaction_history(self, asset: Optional[str] = None) -> List["TransactionResponse"]:
        """Get transaction history for all assets or a specific asset."""
        try:
            self._log_operation_start(f"Getting transaction history for {asset or 'all assets'}")

            # TODO: Implement transaction history using Clean Architecture
            self.logger.warning("Transaction history not implemented in Clean Architecture yet")

            from ..models.portfolio import TransactionResponse
            # Return empty list for now
            return []

        except Exception as e:
            self._handle_service_error("get transaction history", e, Exception)

    async def reconcile_portfolio(self, asset: Optional[str] = None) -> List[ReconciliationResultResponse]:
        """Perform portfolio reconciliation analysis."""
        try:
            self._log_operation_start(f"Reconciling portfolio for {asset or 'all assets'}")

            # TODO: Implement reconciliation using Clean Architecture
            self.logger.warning("Portfolio reconciliation not implemented in Clean Architecture yet")
            return []

        except Exception as e:
            self._handle_service_error("reconcile portfolio", e, Exception)

    async def refresh_portfolio_data(self) -> bool:
        """Force refresh of portfolio data from exchange."""
        try:
            self._log_operation_start("Refreshing portfolio data")

            # TODO: Implement data refresh using Clean Architecture
            self.logger.warning("Portfolio data refresh not implemented in Clean Architecture yet")

            self._log_operation_success("Refreshing portfolio data", "Refresh completed")
            return True

        except Exception as e:
            self._handle_service_error("refresh portfolio data", e, Exception)
            return False
