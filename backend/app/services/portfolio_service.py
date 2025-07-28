"""
Portfolio service implementation.

Provides business logic for portfolio operations with full type safety
and integration with existing portfolio calculation logic.
"""

from datetime import datetime
from decimal import Decimal, getcontext
from typing import Dict, List, Optional

# Import existing portfolio logic via shared module
from ..shared.portfolio_core import (
    PurchaseLot,
    TransferSummary,
    analyze_transfers,
    calculate_pnl,
    fetch_trade_history,
    get_current_price,
    get_portfolio_assets,
    reconcile_portfolio_balances,
)

from ..core.config import Settings
from ..core.exceptions import AssetNotFoundException, PortfolioServiceException
from ..models.portfolio import (
    HoldingResponse,
    PortfolioHoldingsResponse,
    PortfolioSummaryResponse,
    ReconciliationResponse,
    TransactionResponse,
    TransferSummaryResponse,
)
from .base_service import BaseService
from .interfaces.bitvavo_client import IBitvavoClient
from .interfaces.portfolio_service import IPortfolioService

# Set high precision for Decimal calculations
getcontext().prec = 28


class PortfolioService(BaseService, IPortfolioService):
    """
    Portfolio service implementation providing C#-like business logic layer.

    This service integrates with the existing portfolio calculation logic
    and provides strongly typed responses for the API.
    Follows Single Responsibility Principle by focusing only on portfolio operations.
    """

    def __init__(self, settings: Settings, bitvavo_client: IBitvavoClient):
        """
        Initialize portfolio service with dependencies.

        Args:
            settings: Application settings
            bitvavo_client: Bitvavo client for API operations
        """
        super().__init__(settings, "PortfolioService")
        self.bitvavo_client = bitvavo_client
        self._portfolio_data_cache: Optional[Dict] = None
        self._cache_timestamp: Optional[datetime] = None
        self._assets_cache: Optional[List[str]] = None

    async def _get_portfolio_assets(self) -> List[str]:
        """Get list of portfolio assets with caching."""
        if self._assets_cache is None:
            try:
                self._log_operation_start("Getting portfolio assets")
                client = self.bitvavo_client._get_client()
                self._assets_cache = get_portfolio_assets(client)
                self._log_operation_success(
                    "Getting portfolio assets", f"Found {len(self._assets_cache)} assets"
                )
            except Exception as e:
                self._handle_service_error("get portfolio assets", e, PortfolioServiceException)
        return self._assets_cache

    def _calculate_asset_pnl(self, client, asset: str) -> Dict[str, Decimal]:
        """
        Calculate PnL for a specific asset using existing logic.

        Args:
            client: Bitvavo client instance
            asset: Asset symbol

        Returns:
            Dict[str, Decimal]: PnL calculation results
        """
        self._validate_required_param("asset", asset)

        trades = fetch_trade_history(client, asset)
        if not trades:
            return self._create_empty_pnl_result()

        current_price = get_current_price(client, asset)
        return calculate_pnl(trades, current_price)

    def _create_empty_pnl_result(self) -> Dict[str, Decimal]:
        """Create empty PnL result for assets with no trades."""
        return {
            "amount": Decimal("0"),
            "cost_eur": Decimal("0"),
            "value_eur": Decimal("0"),
            "realised_eur": Decimal("0"),
            "unrealised_eur": Decimal("0"),
            "total_buys_eur": Decimal("0"),
        }

    def _convert_pnl_to_holding(
        self,
        asset: str,
        pnl_data: Dict[str, Decimal],
        current_price: Decimal,
        total_portfolio_value: Decimal,
    ) -> HoldingResponse:
        """Convert PnL calculation result to HoldingResponse."""
        value_eur = pnl_data["value_eur"]
        portfolio_percentage = (
            (value_eur / total_portfolio_value * 100) if total_portfolio_value > 0 else Decimal("0")
        )

        # Calculate total return percentage
        invested = pnl_data["total_buys_eur"]
        total_return_pct = (
            ((value_eur + pnl_data["realised_eur"]) - invested) / invested * 100
            if invested > 0
            else Decimal("0")
        )

        return HoldingResponse(
            asset=asset,
            quantity=pnl_data["amount"],
            current_price=current_price,
            value_eur=value_eur,
            cost_basis=pnl_data["cost_eur"],
            unrealized_pnl=pnl_data["unrealised_eur"],
            realized_pnl=pnl_data["realised_eur"],
            portfolio_percentage=portfolio_percentage,
            total_return_percentage=total_return_pct,
        )

    async def get_portfolio_summary(self) -> PortfolioSummaryResponse:
        """
        Get comprehensive portfolio summary with all key metrics.

        Returns:
            PortfolioSummaryResponse: Complete portfolio overview

        Raises:
            PortfolioServiceException: If portfolio data cannot be retrieved
        """
        try:
            self._log_operation_start("Getting portfolio summary")

            assets = await self._get_portfolio_assets()
            client = self.bitvavo_client._get_client()

            summary_data = self._calculate_portfolio_totals(client, assets)

            return PortfolioSummaryResponse(
                total_value=summary_data["total_value"],
                total_cost=summary_data["total_cost"],
                realized_pnl=summary_data["total_realized_pnl"],
                unrealized_pnl=summary_data["total_unrealized_pnl"],
                total_pnl=summary_data["total_pnl"],
                total_return_percentage=summary_data["total_return_percentage"],
                asset_count=summary_data["asset_count"],
                last_updated=datetime.utcnow(),
            )

        except Exception as e:
            self._handle_service_error("get portfolio summary", e, PortfolioServiceException)

    def _calculate_portfolio_totals(self, client, assets: List[str]) -> Dict[str, Decimal]:
        """
        Calculate portfolio totals from asset list.

        Args:
            client: Bitvavo client instance
            assets: List of asset symbols

        Returns:
            Dict[str, Decimal]: Portfolio totals
        """
        totals = {
            "total_value": Decimal("0"),
            "total_cost": Decimal("0"),
            "total_realized_pnl": Decimal("0"),
            "total_unrealized_pnl": Decimal("0"),
            "asset_count": 0,
        }

        for asset in assets:
            try:
                pnl = self._calculate_asset_pnl(client, asset)

                if pnl["amount"] > 0:  # Only count assets with holdings
                    totals["total_value"] += pnl["value_eur"]
                    totals["total_cost"] += pnl["cost_eur"]
                    totals["total_realized_pnl"] += pnl["realised_eur"]
                    totals["total_unrealized_pnl"] += pnl["unrealised_eur"]
                    totals["asset_count"] += 1

            except Exception as e:
                self.logger.warning(f"Error processing asset {asset}: {e}")
                continue

        totals["total_pnl"] = totals["total_realized_pnl"] + totals["total_unrealized_pnl"]
        totals["total_return_percentage"] = (
            (totals["total_pnl"] / totals["total_cost"] * 100)
            if totals["total_cost"] > 0
            else Decimal("0")
        )

        return totals

    async def get_current_holdings(self) -> List[HoldingResponse]:
        """
        Get list of all currently held assets with detailed information.

        Returns:
            List[HoldingResponse]: All current holdings

        Raises:
            PortfolioServiceException: If holdings data cannot be retrieved
        """
        try:
            self._log_operation_start("Getting current holdings")

            assets = await self._get_portfolio_assets()
            client = self.bitvavo_client._get_client()
            holdings = []

            # First pass: calculate all holdings to get total portfolio value
            all_pnl_data = {}
            total_portfolio_value = Decimal("0")

            for asset in assets:
                try:
                    pnl = self._calculate_asset_pnl(client, asset)
                    current_price = get_current_price(client, asset)

                    if pnl["amount"] > 0 and current_price > 0:  # Only include assets with holdings
                        all_pnl_data[asset] = (pnl, current_price)
                        total_portfolio_value += pnl["value_eur"]

                except Exception as e:
                    self.logger.warning(f"Error processing asset {asset}: {e}")
                    continue

            # Second pass: create HoldingResponse objects with portfolio percentages
            for asset, (pnl, current_price) in all_pnl_data.items():
                holding = self._convert_pnl_to_holding(
                    asset, pnl, current_price, total_portfolio_value
                )
                holdings.append(holding)

            # Sort by value (largest first)
            holdings.sort(key=lambda h: h.value_eur, reverse=True)

            return holdings

        except Exception as e:
            self._handle_service_error("get current holdings", e, PortfolioServiceException)

    async def get_portfolio_holdings(self) -> PortfolioHoldingsResponse:
        """
        Get complete portfolio data including holdings and summary.

        Returns:
            PortfolioHoldingsResponse: Holdings with summary

        Raises:
            PortfolioServiceException: If portfolio data cannot be retrieved
        """
        try:
            self.logger.info("Getting complete portfolio holdings")

            summary = await self.get_portfolio_summary()
            holdings = await self.get_current_holdings()

            return PortfolioHoldingsResponse(
                holdings=holdings, summary=summary, last_updated=datetime.utcnow()
            )

        except Exception as e:
            self.logger.error(f"Error getting portfolio holdings: {e}")
            raise PortfolioServiceException(f"Failed to get portfolio holdings: {str(e)}")

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
        try:
            self.logger.info(f"Getting asset performance for {asset}")

            holdings = await self.get_current_holdings()

            for holding in holdings:
                if holding.asset == asset:
                    return holding

            raise AssetNotFoundException(asset)

        except AssetNotFoundException:
            raise
        except Exception as e:
            self.logger.error(f"Error getting asset performance for {asset}: {e}")
            raise PortfolioServiceException(f"Failed to get asset performance: {str(e)}")

    async def get_transaction_history(
        self, asset: Optional[str] = None
    ) -> List[TransactionResponse]:
        """
        Get transaction history for all assets or a specific asset.

        Args:
            asset: Optional asset symbol to filter by

        Returns:
            List[TransactionResponse]: Transaction history

        Raises:
            PortfolioServiceException: If transaction data cannot be retrieved
        """
        try:
            self.logger.info(f"Getting transaction history for asset: {asset or 'all'}")

            client = self.bitvavo_client._get_client()
            transactions = []

            if asset:
                assets_to_process = [asset]
            else:
                assets_to_process = await self._get_portfolio_assets()

            for asset_symbol in assets_to_process:
                try:
                    trades = fetch_trade_history(client, asset_symbol)

                    for trade in trades:
                        transactions.append(
                            TransactionResponse(
                                id=trade.get("id", ""),
                                asset=asset_symbol,
                                side=trade.get("side", "").lower(),
                                amount=Decimal(str(trade.get("amount", "0"))),
                                price=Decimal(str(trade.get("price", "0"))),
                                fee=Decimal(str(trade.get("fee", "0"))),
                                timestamp=int(trade.get("timestamp", "0")),
                            )
                        )

                except Exception as e:
                    self.logger.warning(f"Error getting trades for {asset_symbol}: {e}")
                    continue

            # Sort by timestamp (newest first)
            transactions.sort(key=lambda t: t.timestamp, reverse=True)

            return transactions

        except Exception as e:
            self.logger.error(f"Error getting transaction history: {e}")
            raise PortfolioServiceException(f"Failed to get transaction history: {str(e)}")

    def _convert_transfer_summary(
        self, transfer_summary: TransferSummary
    ) -> TransferSummaryResponse:
        """Convert TransferSummary to TransferSummaryResponse."""
        return TransferSummaryResponse(
            total_deposits=transfer_summary.total_deposits,
            total_withdrawals=transfer_summary.total_withdrawals,
            net_transfers=transfer_summary.net_transfers,
            deposit_count=transfer_summary.deposit_count,
            withdrawal_count=transfer_summary.withdrawal_count,
            potential_rewards=transfer_summary.potential_rewards,
        )

    async def reconcile_portfolio(
        self, asset: Optional[str] = None
    ) -> List[ReconciliationResponse]:
        """
        Perform portfolio reconciliation analysis.

        Args:
            asset: Optional asset symbol to reconcile (all assets if None)

        Returns:
            List[ReconciliationResponse]: Reconciliation results

        Raises:
            PortfolioServiceException: If reconciliation cannot be performed
        """
        try:
            self.logger.info(f"Performing portfolio reconciliation for asset: {asset or 'all'}")

            client = self.bitvavo_client._get_client()

            if asset:
                assets_to_reconcile = [asset]
            else:
                assets_to_reconcile = await self._get_portfolio_assets()

            # Use existing reconciliation logic
            reconciliation_data = reconcile_portfolio_balances(client, assets_to_reconcile)

            reconciliations = []
            for asset_data in reconciliation_data["assets"]:
                asset_symbol = asset_data["asset"]

                reconciliations.append(
                    ReconciliationResponse(
                        asset=asset_symbol,
                        fifo_amount=asset_data["fifo_amount"],
                        actual_amount=asset_data["actual_amount"],
                        discrepancy=asset_data["discrepancy"],
                        transfer_summary=self._convert_transfer_summary(
                            asset_data["transfer_summary"]
                        ),
                        explanation=asset_data["explanation"],
                        confidence_level=asset_data["confidence_level"],
                    )
                )

            return reconciliations

        except Exception as e:
            self.logger.error(f"Error performing portfolio reconciliation: {e}")
            raise PortfolioServiceException(f"Failed to perform reconciliation: {str(e)}")

    async def refresh_portfolio_data(self) -> bool:
        """
        Force refresh of portfolio data from exchange.

        Returns:
            bool: True if refresh was successful

        Raises:
            PortfolioServiceException: If data refresh fails
        """
        try:
            self.logger.info("Refreshing portfolio data from exchange")

            # Clear all caches to force fresh data fetch
            self._portfolio_data_cache = None
            self._cache_timestamp = None
            self._assets_cache = None

            # Test connection by getting portfolio assets
            await self._get_portfolio_assets()

            self.logger.info("Portfolio data refreshed successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error refreshing portfolio data: {e}")
            raise PortfolioServiceException(f"Failed to refresh portfolio data: {str(e)}")
