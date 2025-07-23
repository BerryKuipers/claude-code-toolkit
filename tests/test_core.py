"""Tests for core FIFO P&L calculation logic.

Comprehensive test suite for the core portfolio analysis functionality,
including FIFO accounting, API integration, and edge cases.
"""

import time
from decimal import Decimal
from typing import Dict
from unittest.mock import MagicMock

import pytest

from src.portfolio.core import (
    BitvavoAPIException,
    InvalidAPIKeyError,
    PurchaseLot,
    RateLimitExceededError,
    _check_rate_limit,
    _decimal,
    calculate_pnl,
    fetch_trade_history,
    get_current_price,
    get_portfolio_assets,
    sync_time,
)


def _make_trade(
    side: str, amount: str, price: str, fee: str = "0", ts: int = None
) -> Dict[str, str]:
    """Helper to create trade dictionaries for testing."""
    return {
        "id": "test_trade_id",
        "timestamp": str(ts or int(time.time() * 1000)),
        "market": "TEST-EUR",
        "side": side,
        "amount": amount,
        "price": price,
        "fee": fee,
        "feeCurrency": "EUR",
    }


class TestDecimalHelper:
    """Test the _decimal helper function."""

    def test_decimal_from_string(self):
        assert _decimal("123.45") == Decimal("123.45")

    def test_decimal_from_int(self):
        assert _decimal(123) == Decimal("123")

    def test_decimal_from_float(self):
        assert _decimal(123.45) == Decimal("123.45")

    def test_decimal_from_decimal(self):
        original = Decimal("123.45")
        assert _decimal(original) == original


class TestPurchaseLot:
    """Test the PurchaseLot dataclass."""

    def test_purchase_lot_creation(self):
        lot = PurchaseLot(
            amount=Decimal("1.5"), cost_eur=Decimal("100.50"), timestamp=1234567890
        )
        assert lot.amount == Decimal("1.5")
        assert lot.cost_eur == Decimal("100.50")
        assert lot.timestamp == 1234567890


class TestFIFOCalculation:
    """Test the core FIFO P&L calculation logic."""

    def test_single_buy_no_sell(self):
        """Test portfolio with only buy trades."""
        trades = [_make_trade("buy", "2", "10", "0.1")]
        pnl = calculate_pnl(trades, Decimal("12"))

        assert pnl["amount"] == Decimal("2")
        assert pnl["cost_eur"] == Decimal("20.1")  # 2 * 10 + 0.1 fee
        assert pnl["value_eur"] == Decimal("24")  # 2 * 12
        assert pnl["realised_eur"] == Decimal("0")
        assert pnl["unrealised_eur"] == Decimal("3.9")  # 24 - 20.1
        assert pnl["total_buys_eur"] == Decimal("20.1")

    def test_partial_sell(self):
        """Test partial sale of holdings."""
        trades = [
            _make_trade("buy", "2", "10"),  # Buy 2 at €10 each
            _make_trade("sell", "1", "15"),  # Sell 1 at €15
        ]
        pnl = calculate_pnl(trades, Decimal("14"))

        assert pnl["amount"] == Decimal("1")  # 1 remaining
        assert pnl["cost_eur"] == Decimal("10")  # Cost of remaining 1 unit
        assert pnl["value_eur"] == Decimal("14")  # 1 * 14
        assert pnl["realised_eur"] == Decimal("5")  # 15 - 10 (FIFO)
        assert pnl["unrealised_eur"] == Decimal("4")  # 14 - 10
        assert pnl["total_buys_eur"] == Decimal("20")

    def test_full_lot_sell(self):
        """Test complete sale of a purchase lot."""
        trades = [
            _make_trade("buy", "1", "100", "1"),  # Buy 1 at €100 + €1 fee
            _make_trade("sell", "1", "150", "1"),  # Sell 1 at €150 - €1 fee
        ]
        pnl = calculate_pnl(trades, Decimal("140"))

        assert pnl["amount"] == Decimal("0")
        assert pnl["cost_eur"] == Decimal("0")
        assert pnl["value_eur"] == Decimal("0")
        assert pnl["realised_eur"] == Decimal(
            "48"
        )  # (150-1) - (100+1) = 149 - 101 = 48
        assert pnl["unrealised_eur"] == Decimal("0")
        assert pnl["total_buys_eur"] == Decimal("101")

    def test_complex_sell_across_lots(self):
        """Test sale that spans multiple purchase lots."""
        trades = [
            _make_trade("buy", "1", "100"),  # Buy 1 at €100
            _make_trade("buy", "2", "120"),  # Buy 2 at €120 each
            _make_trade("sell", "1.5", "130"),  # Sell 1.5 at €130 each
        ]
        pnl = calculate_pnl(trades, Decimal("125"))

        # Should sell: 1 from first lot + 0.5 from second lot
        # Remaining: 1.5 from second lot at €120 each = €180 cost
        assert pnl["amount"] == Decimal("1.5")
        assert pnl["cost_eur"] == Decimal("180")  # 1.5 * 120
        assert pnl["value_eur"] == Decimal("187.5")  # 1.5 * 125
        assert pnl["realised_eur"] == Decimal("35")  # (1.5 * 130) - (100 + 0.5 * 120)
        assert pnl["unrealised_eur"] == Decimal("7.5")  # 187.5 - 180
        assert pnl["total_buys_eur"] == Decimal("340")  # 100 + 2*120

    def test_multiple_buys_and_sells(self):
        """Test complex scenario with multiple buys and sells."""
        trades = [
            _make_trade("buy", "3", "100"),  # Buy 3 at €100
            _make_trade("sell", "1", "150"),  # Sell 1 at €150
            _make_trade("buy", "2", "80"),  # Buy 2 at €80
            _make_trade("sell", "2", "120"),  # Sell 2 at €120
        ]
        pnl = calculate_pnl(trades, Decimal("110"))

        # Remaining: 2 units from second buy at €80 each (first buy was fully sold)
        assert pnl["amount"] == Decimal("2")
        assert pnl["cost_eur"] == Decimal("160")  # 2 * 80
        assert pnl["value_eur"] == Decimal("220")  # 2 * 110
        # Realised: (150-100) + (2*120 - 2*100) = 50 + 40 = 90
        assert pnl["realised_eur"] == Decimal("90")
        assert pnl["unrealised_eur"] == Decimal("60")  # 220 - 160
        assert pnl["total_buys_eur"] == Decimal("460")  # 3*100 + 2*80

    def test_invalid_trade_side(self):
        """Test error handling for invalid trade side."""
        trades = [_make_trade("invalid", "1", "100")]

        with pytest.raises(ValueError, match="Unknown trade side: invalid"):
            calculate_pnl(trades, Decimal("100"))

    def test_empty_trades_list(self):
        """Test calculation with no trades."""
        pnl = calculate_pnl([], Decimal("100"))

        assert pnl["amount"] == Decimal("0")
        assert pnl["cost_eur"] == Decimal("0")
        assert pnl["value_eur"] == Decimal("0")
        assert pnl["realised_eur"] == Decimal("0")
        assert pnl["unrealised_eur"] == Decimal("0")
        assert pnl["total_buys_eur"] == Decimal("0")


class TestAPIHelpers:
    """Test API helper functions with mocked Bitvavo client."""

    def test_check_rate_limit_sufficient(self, mocker):
        """Test rate limit check when limit is sufficient."""
        mock_client = mocker.MagicMock()
        mock_client.getRemainingLimit.return_value = 100

        # Should not sleep
        mock_sleep = mocker.patch("time.sleep")
        _check_rate_limit(mock_client, threshold=10)
        mock_sleep.assert_not_called()

    def test_check_rate_limit_insufficient(self, mocker):
        """Test rate limit check when limit is low."""
        mock_client = mocker.MagicMock()
        mock_client.getRemainingLimit.return_value = 5

        # Should sleep
        mock_sleep = mocker.patch("time.sleep")
        _check_rate_limit(mock_client, threshold=10)
        mock_sleep.assert_called_once_with(15)

    def test_sync_time_success(self, mocker):
        """Test successful time synchronization."""
        mock_client = mocker.MagicMock()
        mock_client.time.return_value = {"time": "1234567890000"}

        mock_datetime = mocker.patch("src.portfolio.core.datetime")
        mock_now = mocker.MagicMock()
        mock_now.timestamp.return_value = 1234567890.5
        mock_datetime.now.return_value = mock_now

        sync_time(mock_client)

        assert mock_client.timeDifference == -500  # 1234567890000 - 1234567890500

    def test_sync_time_failure(self, mocker):
        """Test time synchronization failure."""
        mock_client = mocker.MagicMock()
        mock_client.time.side_effect = Exception("Network error")

        with pytest.raises(BitvavoAPIException, match="Failed to fetch /time"):
            sync_time(mock_client)

    def test_get_current_price(self, mocker):
        """Test getting current price."""
        mock_client = mocker.MagicMock()
        mock_client.getRemainingLimit.return_value = 100
        mock_client.tickerPrice.return_value = {"price": "45000.50"}

        price = get_current_price(mock_client, "BTC")

        assert price == Decimal("45000.50")
        mock_client.tickerPrice.assert_called_once_with({"market": "BTC-EUR"})

    def test_get_current_price_empty_response(self, mocker):
        """Test getting current price with empty response."""
        mock_client = mocker.MagicMock()
        mock_client.getRemainingLimit.return_value = 100
        mock_client.tickerPrice.return_value = []

        price = get_current_price(mock_client, "BTC")

        assert price == Decimal("0")

    def test_get_portfolio_assets(self, mocker):
        """Test getting portfolio assets."""
        mock_client = mocker.MagicMock()
        mock_client.balance.return_value = [
            {"symbol": "BTC-EUR", "available": "1.5", "inOrder": "0"},
            {"symbol": "ETH-EUR", "available": "0", "inOrder": "2.0"},
            {
                "symbol": "ADA-EUR",
                "available": "0",
                "inOrder": "0",
            },  # Should be filtered out
        ]

        assets = get_portfolio_assets(mock_client)

        assert assets == ["BTC", "ETH"]
