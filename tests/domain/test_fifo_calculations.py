"""
Tests for FIFO calculation service - the SINGLE SOURCE OF TRUTH.

These tests verify that the core FIFO calculation logic works correctly
and maintains consistency across all scenarios.
"""

from decimal import Decimal
from uuid import uuid4

import pytest

from portfolio_core.domain.entities import PurchaseLot, Trade
from portfolio_core.domain.services import FIFOCalculationService
from portfolio_core.domain.value_objects import (
    AssetAmount,
    AssetSymbol,
    Money,
    Timestamp,
    TradeType,
)


class TestFIFOCalculationService:
    """Test the core FIFO calculation service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.fifo_service = FIFOCalculationService()
        self.btc = AssetSymbol("BTC")
        self.eur = "EUR"

    def create_trade(
        self,
        trade_type: TradeType,
        amount: str,
        price: str,
        fee: str = "0",
        timestamp: int = 1000,
    ) -> Trade:
        """Helper to create a trade."""
        return Trade(
            asset=self.btc,
            trade_type=trade_type,
            amount=AssetAmount(Decimal(amount), self.btc),
            price=Money(Decimal(price), self.eur),
            fee=Money(Decimal(fee), self.eur),
            timestamp=Timestamp(timestamp),
        )

    def test_empty_trades_returns_zero_pnl(self):
        """Test that empty trade list returns zero P&L."""
        current_price = Money(Decimal("50000"), self.eur)
        result = self.fifo_service.calculate_asset_pnl([], current_price)

        assert result["amount"] == Decimal("0")
        assert result["cost_eur"] == Decimal("0")
        assert result["value_eur"] == Decimal("0")
        assert result["realised_eur"] == Decimal("0")
        assert result["unrealised_eur"] == Decimal("0")
        assert result["total_buys_eur"] == Decimal("0")

    def test_single_buy_trade(self):
        """Test FIFO calculation with single buy trade."""
        trades = [self.create_trade(TradeType.BUY, "1.0", "40000", "100", 1000)]
        current_price = Money(Decimal("50000"), self.eur)

        result = self.fifo_service.calculate_asset_pnl(trades, current_price)

        assert result["amount"] == Decimal("1.0")
        assert result["cost_eur"] == Decimal("40100")  # 40000 + 100 fee
        assert result["value_eur"] == Decimal("50000")  # 1.0 * 50000
        assert result["realised_eur"] == Decimal("0")
        assert result["unrealised_eur"] == Decimal("9900")  # 50000 - 40100
        assert result["total_buys_eur"] == Decimal("40100")

    def test_buy_then_sell_fifo_order(self):
        """Test FIFO calculation with buy then sell."""
        trades = [
            self.create_trade(TradeType.BUY, "2.0", "30000", "50", 1000),
            self.create_trade(TradeType.BUY, "1.0", "40000", "25", 2000),
            self.create_trade(TradeType.SELL, "1.5", "50000", "75", 3000),
        ]
        current_price = Money(Decimal("45000"), self.eur)

        result = self.fifo_service.calculate_asset_pnl(trades, current_price)

        # First buy: 2.0 BTC at 30000 + 50 fee = 60050 total
        # Second buy: 1.0 BTC at 40000 + 25 fee = 40025 total
        # Sell 1.5 BTC at 50000 - 75 fee = 74925 proceeds

        # FIFO: Sell consumes first 1.5 BTC from first lot
        # Cost basis of sold: (60050 / 2.0) * 1.5 = 45037.5
        # Realized P&L: 74925 - 45037.5 = 29887.5

        # Remaining: 0.5 BTC from first lot + 1.0 BTC from second lot = 1.5 BTC
        # Remaining cost: (60050 / 2.0) * 0.5 + 40025 = 15012.5 + 40025 = 55037.5

        assert result["amount"] == Decimal("1.5")
        assert result["cost_eur"] == Decimal("55037.5")
        assert result["value_eur"] == Decimal("67500")  # 1.5 * 45000
        assert result["realised_eur"] == Decimal("29887.5")
        assert result["unrealised_eur"] == Decimal("12462.5")  # 67500 - 55037.5
        assert result["total_buys_eur"] == Decimal("100075")  # 60050 + 40025

    def test_multiple_buys_and_sells(self):
        """Test complex FIFO scenario with multiple buys and sells."""
        trades = [
            self.create_trade(TradeType.BUY, "1.0", "30000", "30", 1000),
            self.create_trade(TradeType.BUY, "2.0", "35000", "70", 2000),
            self.create_trade(TradeType.SELL, "0.5", "40000", "20", 3000),
            self.create_trade(TradeType.BUY, "1.0", "38000", "38", 4000),
            self.create_trade(TradeType.SELL, "2.0", "42000", "84", 5000),
        ]
        current_price = Money(Decimal("45000"), self.eur)

        result = self.fifo_service.calculate_asset_pnl(trades, current_price)

        # This tests the complete FIFO logic with multiple transactions
        assert result["amount"] == Decimal("1.5")
        assert result["cost_eur"] > Decimal("0")
        assert result["value_eur"] == Decimal("67500")  # 1.5 * 45000
        assert result["total_buys_eur"] > Decimal("0")

    def test_sell_more_than_available_logs_warning(self, caplog):
        """Test that selling more than available logs a warning."""
        trades = [
            self.create_trade(TradeType.BUY, "1.0", "30000", "30", 1000),
            self.create_trade(TradeType.SELL, "2.0", "40000", "80", 2000),
        ]
        current_price = Money(Decimal("45000"), self.eur)

        result = self.fifo_service.calculate_asset_pnl(trades, current_price)

        # Should log warning about overselling
        assert "Sold more BTC than available" in caplog.text

        # Result should still be calculated
        assert result["amount"] == Decimal("0")  # No remaining holdings

    def test_trades_sorted_by_timestamp(self):
        """Test that trades are properly sorted by timestamp for FIFO."""
        # Create trades in wrong chronological order
        trades = [
            self.create_trade(TradeType.SELL, "0.5", "50000", "25", 3000),  # Later
            self.create_trade(TradeType.BUY, "1.0", "30000", "30", 1000),  # Earlier
            self.create_trade(TradeType.BUY, "1.0", "40000", "40", 2000),  # Middle
        ]
        current_price = Money(Decimal("45000"), self.eur)

        result = self.fifo_service.calculate_asset_pnl(trades, current_price)

        # Should process in correct chronological order: buy, buy, sell
        # Sell should consume from first buy (FIFO)
        assert result["amount"] == Decimal("1.5")  # 1.0 + 1.0 - 0.5

    def test_different_assets_raises_error(self):
        """Test that trades for different assets raise an error."""
        eth = AssetSymbol("ETH")
        trades = [
            self.create_trade(TradeType.BUY, "1.0", "30000", "30", 1000),
            Trade(
                asset=eth,  # Different asset
                trade_type=TradeType.BUY,
                amount=AssetAmount(Decimal("10"), eth),
                price=Money(Decimal("2000"), self.eur),
                fee=Money(Decimal("20"), self.eur),
                timestamp=Timestamp(2000),
            ),
        ]
        current_price = Money(Decimal("45000"), self.eur)

        with pytest.raises(ValueError, match="All trades must be for the same asset"):
            self.fifo_service.calculate_asset_pnl(trades, current_price)

    def test_precision_maintained_in_calculations(self):
        """Test that decimal precision is maintained throughout calculations."""
        trades = [
            self.create_trade(TradeType.BUY, "0.12345678", "30000.12345", "1.23", 1000),
            self.create_trade(
                TradeType.SELL, "0.06172839", "50000.98765", "2.34", 2000
            ),
        ]
        current_price = Money(Decimal("45000.55555"), self.eur)

        result = self.fifo_service.calculate_asset_pnl(trades, current_price)

        # Verify high precision is maintained
        assert isinstance(result["amount"], Decimal)
        assert isinstance(result["cost_eur"], Decimal)
        assert isinstance(result["value_eur"], Decimal)

        # Check that we have reasonable precision (not rounded to whole numbers)
        assert result["amount"] == Decimal("0.06172839")  # 0.12345678 - 0.06172839
