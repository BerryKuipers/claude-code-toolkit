"""Tests for AI explanations module, focusing on price formatting and coin explanations."""

import re

import pytest

from src.portfolio.ai_explanations import (
    _safe_float_conversion,
    format_crypto_amount,
    format_currency,
    generate_coin_explanation,
    get_position_summary,
)


class TestFormatCurrency:
    """Test the format_currency function with various price ranges."""

    def test_large_amounts(self):
        """Test formatting for large amounts (≥ €1000)."""
        assert format_currency(45000.123) == "€45,000"
        assert format_currency(1500.789) == "€1,501"  # Rounds to nearest integer
        assert format_currency(999999.99) == "€1,000,000"  # Rounds up

    def test_medium_amounts(self):
        """Test formatting for medium amounts (≥ €1, < €1000)."""
        assert format_currency(500.45) == "€500.45"
        assert format_currency(1.23) == "€1.23"
        assert format_currency(999.99) == "€999.99"

    def test_small_amounts(self):
        """Test formatting for small amounts (≥ €0.01)."""
        assert format_currency(0.45) == "€0.4500"
        assert format_currency(0.0789) == "€0.0789"
        assert format_currency(0.01) == "€0.0100"

    def test_very_small_amounts(self):
        """Test formatting for very small amounts (≥ €0.0001)."""
        assert format_currency(0.001234) == "€0.001234"
        assert format_currency(0.0001) == "€0.000100"
        assert format_currency(0.009999) == "€0.009999"

    def test_extremely_small_amounts(self):
        """Test formatting for extremely small amounts (< €0.0001) - typical for SHIB."""
        assert format_currency(0.00001234) == "€0.00001234"
        assert format_currency(0.000000456) == "€0.00000046"
        assert format_currency(0.00000001) == "€0.00000001"

    def test_zero_amount(self):
        """Test formatting for zero amount."""
        assert format_currency(0.0) == "€0.00000000"

    def test_negative_amounts(self):
        """Test formatting for negative amounts."""
        assert format_currency(-45000.123) == "€-45,000"
        assert format_currency(-1.23) == "€-1.23"
        assert format_currency(-0.00001234) == "€-0.00001234"

    def test_custom_currency_symbol(self):
        """Test formatting with custom currency symbol."""
        assert format_currency(1.23, "$") == "$1.23"
        assert format_currency(0.00001234, "USD") == "USD0.00001234"


class TestFormatCryptoAmount:
    """Test the format_crypto_amount function."""

    def test_large_crypto_amounts(self):
        """Test formatting for large crypto amounts (≥ 1)."""
        assert format_crypto_amount(1000.123456, "BTC") == "1000.123456 BTC"
        assert format_crypto_amount(1.0, "ETH") == "1.000000 ETH"

    def test_small_crypto_amounts(self):
        """Test formatting for small crypto amounts (< 1)."""
        assert format_crypto_amount(0.12345678, "BTC") == "0.12345678 BTC"
        assert format_crypto_amount(0.00000001, "SHIB") == "0.00000001 SHIB"


class TestGenerateCoinExplanation:
    """Test the generate_coin_explanation function with various scenarios."""

    def test_shib_realistic_scenario(self):
        """Test SHIB explanation with realistic small price data."""
        shib_data = {
            "Asset": "SHIB",
            "FIFO Amount": 10010090.770000,
            "Actual Amount": 10010090.770000,
            "Amount Diff": 0.0,
            "Cost €": 522.96,
            "FIFO Value €": 126.36,
            "Actual Value €": 126.36,
            "Realised €": 0.0,
            "Unrealised €": -396.60,
            "Total Return %": -75.8,
            "Current Price €": 0.00001262,  # Realistic SHIB price
            "Net Transfers": 0,
            "Total Deposits": 0,
            "Total Withdrawals": 0,
        }

        explanation = generate_coin_explanation(shib_data)

        # Check that the explanation contains properly formatted prices
        assert (
            "€0.00005224" in explanation
        )  # Average price should be formatted correctly
        assert (
            "€0.00001262" in explanation
        )  # Current price should be formatted correctly
        # The key fix: prices should never be exactly €0.00 (check for problematic patterns)
        # Look for "€0.00" followed by word boundary (space, comma, period) - not part of longer number
        zero_price_pattern = r"€0\.00(?=\s|,|\.|\))"
        assert not re.search(
            zero_price_pattern, explanation
        ), f"Found €0.00 price in: {explanation}"
        assert "SHIB" in explanation
        assert "10010090.770000" in explanation
        assert "-75.8%" in explanation

    def test_btc_standard_scenario(self):
        """Test BTC explanation with standard price data."""
        btc_data = {
            "Asset": "BTC",
            "FIFO Amount": 0.5,
            "Actual Amount": 0.5,
            "Amount Diff": 0.0,
            "Cost €": 20000.0,
            "FIFO Value €": 22500.0,
            "Actual Value €": 22500.0,
            "Realised €": 0.0,
            "Unrealised €": 2500.0,
            "Total Return %": 12.5,
            "Current Price €": 45000.0,
            "Net Transfers": 0,
            "Total Deposits": 0,
            "Total Withdrawals": 0,
        }

        explanation = generate_coin_explanation(btc_data)

        # Check that BTC prices are formatted correctly (should use €X,XXX format)
        assert "€40,000" in explanation  # Average price
        assert "€45,000" in explanation  # Current price
        assert "profit" in explanation
        assert "+12.5%" in explanation

    def test_doge_small_price_scenario(self):
        """Test DOGE explanation with small but not extremely small price."""
        doge_data = {
            "Asset": "DOGE",
            "FIFO Amount": 1000.0,
            "Actual Amount": 1000.0,
            "Amount Diff": 0.0,
            "Cost €": 100.0,
            "FIFO Value €": 80.0,
            "Actual Value €": 80.0,
            "Realised €": 0.0,
            "Unrealised €": -20.0,
            "Total Return %": -20.0,
            "Current Price €": 0.08,  # Typical DOGE price range
            "Net Transfers": 0,
            "Total Deposits": 0,
            "Total Withdrawals": 0,
        }

        explanation = generate_coin_explanation(doge_data)

        # Check that DOGE prices are formatted with appropriate precision
        assert "€0.1000" in explanation  # Average price (0.10)
        assert "€0.0800" in explanation  # Current price (0.08)
        assert "lose" in explanation
        assert "-20.0%" in explanation

    def test_no_position_scenario(self):
        """Test explanation when there's no position."""
        no_position_data = {
            "Asset": "ETH",
            "FIFO Amount": 0.0,
            "Actual Amount": 0.0,
            "Amount Diff": 0.0,
            "Cost €": 0.0,
            "FIFO Value €": 0.0,
            "Actual Value €": 0.0,
            "Realised €": 0.0,
            "Unrealised €": 0.0,
            "Total Return %": 0.0,
            "Current Price €": 2500.0,
            "Net Transfers": 0,
            "Total Deposits": 0,
            "Total Withdrawals": 0,
        }

        explanation = generate_coin_explanation(no_position_data)
        assert "no ETH position" in explanation


class TestGetPositionSummary:
    """Test the get_position_summary function."""

    def test_profitable_position(self):
        """Test summary for profitable position."""
        data = {
            "Asset": "BTC",
            "Actual Amount": 0.5,
            "Unrealised €": 1000.0,
            "Total Return %": 25.0,
        }
        summary = get_position_summary(data)
        assert "Profitable BTC position (+25.0%)" == summary

    def test_loss_position(self):
        """Test summary for loss position."""
        data = {
            "Asset": "SHIB",
            "Actual Amount": 1000000.0,
            "Unrealised €": -500.0,
            "Total Return %": -75.8,
        }
        summary = get_position_summary(data)
        assert "Loss SHIB position (-75.8%)" == summary

    def test_no_position(self):
        """Test summary for no position."""
        data = {
            "Asset": "ETH",
            "Actual Amount": 0.0,
            "Unrealised €": 0.0,
            "Total Return %": 0.0,
        }
        summary = get_position_summary(data)
        assert "No ETH position" == summary


class TestPriceFormattingRegression:
    """Regression tests to ensure small crypto prices are never displayed as €0.00."""

    @pytest.mark.parametrize(
        "price,expected_contains",
        [
            (0.00001234, "0.00001234"),  # SHIB-like price
            (0.000000456, "0.00000046"),  # Even smaller
            (0.00000001, "0.00000001"),  # Minimum precision
            (0.0001, "0.000100"),  # Boundary case
            (0.01, "0.0100"),  # Another boundary
        ],
    )
    def test_small_prices_never_show_zero(self, price, expected_contains):
        """Ensure small prices never display as €0.00."""
        formatted = format_currency(price)
        assert "€0.00" != formatted  # Should never be exactly €0.00
        assert expected_contains in formatted
        assert formatted.startswith("€")

    def test_shib_explanation_never_shows_zero_price(self):
        """Regression test: SHIB explanation should never show €0.00 prices."""
        shib_data = {
            "Asset": "SHIB",
            "FIFO Amount": 1000000.0,
            "Actual Amount": 1000000.0,
            "Amount Diff": 0.0,
            "Cost €": 50.0,
            "FIFO Value €": 12.0,
            "Actual Value €": 12.0,
            "Realised €": 0.0,
            "Unrealised €": -38.0,
            "Total Return %": -76.0,
            "Current Price €": 0.000012,  # Very small SHIB price
            "Net Transfers": 0,
            "Total Deposits": 0,
            "Total Withdrawals": 0,
        }

        explanation = generate_coin_explanation(shib_data)

        # Should never contain €0.00 for prices (but may contain it for amounts)
        # Look for "€0.00" followed by word boundary (space, comma, period) - not part of longer number
        zero_price_pattern = r"€0\.00(?=\s|,|\.|\))"
        assert not re.search(
            zero_price_pattern, explanation
        ), f"Found €0.00 price in: {explanation}"
        # Should contain properly formatted small prices
        assert "€0.00005000" in explanation  # Average price
        assert "€0.00001200" in explanation  # Current price


class TestSafeFloatConversion:
    """Test the _safe_float_conversion function for robust type handling."""

    def test_string_numbers(self):
        """Test conversion of string numbers."""
        assert _safe_float_conversion("123.45") == 123.45
        assert _safe_float_conversion("0.0001") == 0.0001
        assert _safe_float_conversion("-50.25") == -50.25

    def test_string_with_currency_symbols(self):
        """Test conversion of strings with currency symbols."""
        assert _safe_float_conversion("€123.45") == 123.45
        assert _safe_float_conversion("$50.00") == 50.0
        assert _safe_float_conversion("€0.00001234") == 0.00001234

    def test_string_with_formatting(self):
        """Test conversion of formatted strings."""
        assert _safe_float_conversion("1,234.56") == 1234.56
        assert _safe_float_conversion(" 123.45 ") == 123.45

    def test_empty_and_invalid_strings(self):
        """Test conversion of empty and invalid strings."""
        assert _safe_float_conversion("") == 0.0
        assert _safe_float_conversion("-") == 0.0
        assert _safe_float_conversion("invalid") == 0.0
        assert _safe_float_conversion("€") == 0.0

    def test_none_values(self):
        """Test conversion of None values."""
        assert _safe_float_conversion(None) == 0.0
        assert _safe_float_conversion(None, 5.0) == 5.0

    def test_numeric_types(self):
        """Test conversion of numeric types."""
        assert _safe_float_conversion(123.45) == 123.45
        assert _safe_float_conversion(123) == 123.0
        assert _safe_float_conversion(0) == 0.0


class TestStringInputBugFix:
    """Test the bug fix for string inputs causing abs() errors."""

    def test_amount_diff_as_string_no_error(self):
        """Test that Amount Diff as string doesn't cause abs() error."""
        # This was the exact error case: abs() called on string Amount Diff
        test_data = {
            "Asset": "BTC",
            "FIFO Amount": 1.5,
            "Actual Amount": 1.6,
            "Amount Diff": "0.1",  # String instead of float - caused original error
            "Cost €": 50000.0,
            "Actual Value €": 52000.0,
            "Unrealised €": 2000.0,
            "Total Return %": 4.0,
            "Current Price €": 32500.0,
            "Net Transfers": 0,
            "Total Deposits": 0,
            "Total Withdrawals": 0,
        }

        # Should not raise any exception
        explanation = generate_coin_explanation(test_data)
        assert "BTC" in explanation
        assert isinstance(explanation, str)
        assert len(explanation) > 0

    def test_all_string_inputs(self):
        """Test that all numeric fields as strings work correctly."""
        test_data = {
            "Asset": "ETH",
            "FIFO Amount": "2.5",  # All numeric fields as strings
            "Actual Amount": "2.7",
            "Amount Diff": "0.2",
            "Cost €": "5000.00",
            "Actual Value €": "5400.00",
            "Unrealised €": "400.00",
            "Total Return %": "8.0",
            "Current Price €": "€2000.00",  # With currency symbol
            "Net Transfers": "0.2",
            "Total Deposits": "0.2",
            "Total Withdrawals": "0",
        }

        # Should not raise any exception
        explanation = generate_coin_explanation(test_data)
        assert "ETH" in explanation
        assert isinstance(explanation, str)
        assert len(explanation) > 0

    def test_mixed_string_and_numeric_inputs(self):
        """Test mixed string and numeric inputs."""
        test_data = {
            "Asset": "DOGE",
            "FIFO Amount": 1000.0,  # Float
            "Actual Amount": "1100.0",  # String
            "Amount Diff": "100.0",  # String (the problematic field)
            "Cost €": 100,  # Int
            "Actual Value €": "110.00",  # String
            "Unrealised €": 10.0,  # Float
            "Total Return %": "10.0",  # String
            "Current Price €": 0.1,  # Float
            "Net Transfers": "100.0",  # String
            "Total Deposits": 100.0,  # Float
            "Total Withdrawals": "0",  # String
        }

        # Should not raise any exception
        explanation = generate_coin_explanation(test_data)
        assert "DOGE" in explanation
        assert isinstance(explanation, str)
        assert len(explanation) > 0
