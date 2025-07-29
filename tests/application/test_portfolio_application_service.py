"""
Tests for Portfolio Application Service.

These tests verify that the application service correctly orchestrates
domain services and handles use cases properly.
"""

from decimal import Decimal
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from portfolio_core.application.commands import CalculatePortfolioCommand
from portfolio_core.application.queries import (
    GetAssetHoldingsQuery,
    GetPortfolioSummaryQuery,
)
from portfolio_core.application.services import PortfolioApplicationService
from portfolio_core.domain.entities import Asset, Portfolio, Trade
from portfolio_core.domain.services import (
    FIFOCalculationService,
    PortfolioCalculationService,
)
from portfolio_core.domain.value_objects import (
    AssetAmount,
    AssetSymbol,
    Money,
    Timestamp,
    TradeType,
)


class TestPortfolioApplicationService:
    """Test the portfolio application service."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create mocks for dependencies
        self.portfolio_repository = AsyncMock()
        self.market_data_repository = AsyncMock()
        self.fifo_service = Mock(spec=FIFOCalculationService)
        self.portfolio_calculation_service = Mock(spec=PortfolioCalculationService)

        # Create the application service
        self.app_service = PortfolioApplicationService(
            portfolio_repository=self.portfolio_repository,
            market_data_repository=self.market_data_repository,
            fifo_service=self.fifo_service,
            portfolio_calculation_service=self.portfolio_calculation_service,
        )

        # Common test data
        self.portfolio_id = uuid4()
        self.btc = AssetSymbol("BTC")
        self.eth = AssetSymbol("ETH")

    def create_mock_portfolio(self) -> Portfolio:
        """Create a mock portfolio for testing."""
        portfolio = Portfolio(id=self.portfolio_id)

        # Add BTC asset
        btc_asset = Asset(
            symbol=self.btc,
            current_price=Money(Decimal("50000"), "EUR"),
            holdings=AssetAmount(Decimal("1.5"), self.btc),
            cost_basis=Money(Decimal("60000"), "EUR"),
            realized_pnl=Money(Decimal("5000"), "EUR"),
        )
        portfolio.add_asset(btc_asset)

        # Add ETH asset
        eth_asset = Asset(
            symbol=self.eth,
            current_price=Money(Decimal("3000"), "EUR"),
            holdings=AssetAmount(Decimal("10"), self.eth),
            cost_basis=Money(Decimal("25000"), "EUR"),
            realized_pnl=Money(Decimal("2000"), "EUR"),
        )
        portfolio.add_asset(eth_asset)

        return portfolio

    def create_mock_trades(self) -> dict:
        """Create mock trades for testing."""
        btc_trades = [
            Trade(
                asset=self.btc,
                trade_type=TradeType.BUY,
                amount=AssetAmount(Decimal("2.0"), self.btc),
                price=Money(Decimal("30000"), "EUR"),
                fee=Money(Decimal("100"), "EUR"),
                timestamp=Timestamp(1000),
            ),
            Trade(
                asset=self.btc,
                trade_type=TradeType.SELL,
                amount=AssetAmount(Decimal("0.5"), self.btc),
                price=Money(Decimal("40000"), "EUR"),
                fee=Money(Decimal("50"), "EUR"),
                timestamp=Timestamp(2000),
            ),
        ]

        eth_trades = [
            Trade(
                asset=self.eth,
                trade_type=TradeType.BUY,
                amount=AssetAmount(Decimal("10"), self.eth),
                price=Money(Decimal("2500"), "EUR"),
                fee=Money(Decimal("75"), "EUR"),
                timestamp=Timestamp(1500),
            )
        ]

        return {self.btc: btc_trades, self.eth: eth_trades}

    @pytest.mark.asyncio
    async def test_get_portfolio_summary_success(self):
        """Test successful portfolio summary retrieval."""
        # Arrange
        mock_portfolio = self.create_mock_portfolio()
        mock_trades = self.create_mock_trades()
        mock_prices = {
            self.btc: Money(Decimal("50000"), "EUR"),
            self.eth: Money(Decimal("3000"), "EUR"),
        }

        # Setup mocks
        self.portfolio_repository.get_portfolio.return_value = mock_portfolio
        self.portfolio_repository.get_all_trades.return_value = mock_trades
        self.market_data_repository.get_current_prices.return_value = mock_prices
        self.portfolio_calculation_service.update_portfolio_from_trades.return_value = (
            mock_portfolio
        )

        # Act
        query = GetPortfolioSummaryQuery(portfolio_id=self.portfolio_id)
        result = await self.app_service.get_portfolio_summary(query)

        # Assert
        assert result.total_value > Decimal("0")
        assert result.asset_count == 2
        assert result.currency == "EUR"

        # Verify repository calls
        self.portfolio_repository.get_portfolio.assert_called_once_with(
            self.portfolio_id
        )
        self.portfolio_repository.get_all_trades.assert_called_once_with(
            self.portfolio_id
        )
        self.portfolio_repository.save_portfolio.assert_called_once()

        # Verify market data call
        self.market_data_repository.get_current_prices.assert_called_once()

        # Verify portfolio calculation service call
        self.portfolio_calculation_service.update_portfolio_from_trades.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_portfolio_summary_portfolio_not_found(self):
        """Test portfolio summary when portfolio doesn't exist."""
        # Arrange
        self.portfolio_repository.get_portfolio.return_value = None

        # Act & Assert
        query = GetPortfolioSummaryQuery(portfolio_id=self.portfolio_id)
        with pytest.raises(ValueError, match="Portfolio .* not found"):
            await self.app_service.get_portfolio_summary(query)

    @pytest.mark.asyncio
    async def test_get_asset_holdings_success(self):
        """Test successful asset holdings retrieval."""
        # Arrange
        mock_portfolio = self.create_mock_portfolio()
        mock_trades = self.create_mock_trades()
        mock_prices = {
            self.btc: Money(Decimal("50000"), "EUR"),
            self.eth: Money(Decimal("3000"), "EUR"),
        }

        # Setup mocks
        self.portfolio_repository.get_portfolio.return_value = mock_portfolio
        self.portfolio_repository.get_all_trades.return_value = mock_trades
        self.market_data_repository.get_current_prices.return_value = mock_prices
        self.portfolio_calculation_service.update_portfolio_from_trades.return_value = (
            mock_portfolio
        )
        self.portfolio_calculation_service.calculate_asset_allocation.return_value = (
            Decimal("60.0")
        )

        # Act
        query = GetAssetHoldingsQuery(portfolio_id=self.portfolio_id)
        result = await self.app_service.get_asset_holdings(query)

        # Assert
        assert len(result) == 2  # BTC and ETH
        assert all(holding.symbol in ["BTC", "ETH"] for holding in result)
        assert all(holding.current_value > Decimal("0") for holding in result)
        assert all(holding.portfolio_percentage >= Decimal("0") for holding in result)

    @pytest.mark.asyncio
    async def test_get_asset_holdings_with_filters(self):
        """Test asset holdings with filtering options."""
        # Arrange
        mock_portfolio = self.create_mock_portfolio()
        mock_trades = self.create_mock_trades()
        mock_prices = {
            self.btc: Money(Decimal("50000"), "EUR"),
            self.eth: Money(Decimal("3000"), "EUR"),
        }

        # Setup mocks
        self.portfolio_repository.get_portfolio.return_value = mock_portfolio
        self.portfolio_repository.get_all_trades.return_value = mock_trades
        self.market_data_repository.get_current_prices.return_value = mock_prices
        self.portfolio_calculation_service.update_portfolio_from_trades.return_value = (
            mock_portfolio
        )
        self.portfolio_calculation_service.calculate_asset_allocation.return_value = (
            Decimal("100.0")
        )

        # Act - Filter for only BTC
        query = GetAssetHoldingsQuery(
            portfolio_id=self.portfolio_id,
            asset_symbols=["BTC"],
            sort_by="symbol",
            sort_descending=False,
        )
        result = await self.app_service.get_asset_holdings(query)

        # Assert
        assert len(result) == 1
        assert result[0].symbol == "BTC"

    @pytest.mark.asyncio
    async def test_calculate_portfolio_success(self):
        """Test successful portfolio calculation."""
        # Arrange
        mock_portfolio = self.create_mock_portfolio()
        mock_trades = self.create_mock_trades()
        mock_prices = {
            self.btc: Money(Decimal("50000"), "EUR"),
            self.eth: Money(Decimal("3000"), "EUR"),
        }

        # Setup mocks
        self.portfolio_repository.get_portfolio.return_value = mock_portfolio
        self.portfolio_repository.get_all_trades.return_value = mock_trades
        self.market_data_repository.get_current_prices.return_value = mock_prices
        self.portfolio_calculation_service.update_portfolio_from_trades.return_value = (
            mock_portfolio
        )

        # Act
        command = CalculatePortfolioCommand(portfolio_id=self.portfolio_id)
        result = await self.app_service.calculate_portfolio(command)

        # Assert
        assert result.total_value > Decimal("0")
        assert result.asset_count == 2

        # Verify that calculation was performed
        self.portfolio_calculation_service.update_portfolio_from_trades.assert_called_once()

    @pytest.mark.asyncio
    async def test_calculate_portfolio_with_force_refresh(self):
        """Test portfolio calculation with forced data refresh."""
        # Arrange
        mock_portfolio = self.create_mock_portfolio()
        mock_trades = self.create_mock_trades()
        mock_prices = {
            self.btc: Money(Decimal("50000"), "EUR"),
            self.eth: Money(Decimal("3000"), "EUR"),
        }

        # Setup mocks
        self.portfolio_repository.get_portfolio.return_value = mock_portfolio
        self.portfolio_repository.get_all_trades.return_value = mock_trades
        self.portfolio_repository.get_portfolio_assets.return_value = {
            self.btc,
            self.eth,
        }
        self.market_data_repository.get_current_prices.return_value = mock_prices
        self.portfolio_calculation_service.update_portfolio_from_trades.return_value = (
            mock_portfolio
        )

        # Act
        command = CalculatePortfolioCommand(
            portfolio_id=self.portfolio_id, force_refresh=True
        )
        result = await self.app_service.calculate_portfolio(command)

        # Assert
        assert result.total_value > Decimal("0")

        # Verify that refresh was called
        self.portfolio_repository.get_portfolio_assets.assert_called_once()

        # Verify that prices were refreshed (called twice: once for refresh, once for calculation)
        assert self.market_data_repository.get_current_prices.call_count == 2
