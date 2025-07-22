"""Tests for the Typer CLI interface.

Tests the command-line interface functionality including argument parsing,
error handling, and integration with the core portfolio logic.
"""

import os
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
import typer
from typer.testing import CliRunner

from src.portfolio.cli import _get_bitvavo_client, _parse_price_override, app


class TestPriceOverrideParsing:
    """Test price override string parsing."""

    def test_empty_override(self):
        """Test parsing empty override string."""
        result = _parse_price_override("")
        assert result == {}

    def test_single_override(self):
        """Test parsing single price override."""
        result = _parse_price_override("BTC=35000")
        assert result == {"BTC": Decimal("35000")}

    def test_multiple_overrides(self):
        """Test parsing multiple price overrides."""
        result = _parse_price_override("BTC=35000,ETH=1800,ADA=0.45")
        expected = {
            "BTC": Decimal("35000"),
            "ETH": Decimal("1800"),
            "ADA": Decimal("0.45"),
        }
        assert result == expected

    def test_override_with_spaces(self):
        """Test parsing overrides with spaces."""
        result = _parse_price_override(" BTC = 35000 , ETH = 1800 ")
        expected = {"BTC": Decimal("35000"), "ETH": Decimal("1800")}
        assert result == expected

    def test_invalid_format(self):
        """Test parsing invalid format raises error."""
        with pytest.raises(typer.Exit):
            _parse_price_override("BTC35000")  # Missing =

    def test_invalid_price(self):
        """Test parsing invalid price value raises error."""
        with pytest.raises(typer.Exit):
            _parse_price_override("BTC=invalid")


class TestBitvavoClientInit:
    """Test Bitvavo client initialization."""

    def test_missing_api_credentials(self):
        """Test error when API credentials are missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(typer.Exit):
                _get_bitvavo_client()

    @patch("src.portfolio.cli.Bitvavo")
    @patch("src.portfolio.cli.sync_time")
    def test_successful_client_init(self, mock_sync_time, mock_bitvavo):
        """Test successful client initialization."""
        mock_client = MagicMock()
        mock_bitvavo.return_value = mock_client

        with patch.dict(
            os.environ,
            {"BITVAVO_API_KEY": "test_key", "BITVAVO_API_SECRET": "test_secret"},
        ):
            client = _get_bitvavo_client()

            assert client == mock_client
            mock_bitvavo.assert_called_once_with(
                {"APIKEY": "test_key", "APISECRET": "test_secret"}
            )
            mock_sync_time.assert_called_once_with(mock_client)

    @patch("src.portfolio.cli.Bitvavo")
    @patch("src.portfolio.cli.sync_time")
    def test_sync_time_failure(self, mock_sync_time, mock_bitvavo):
        """Test error when time sync fails."""
        from src.portfolio.core import BitvavoAPIException

        mock_client = MagicMock()
        mock_bitvavo.return_value = mock_client
        mock_sync_time.side_effect = BitvavoAPIException("Time sync failed")

        with patch.dict(
            os.environ,
            {"BITVAVO_API_KEY": "test_key", "BITVAVO_API_SECRET": "test_secret"},
        ):
            with pytest.raises(typer.Exit):
                _get_bitvavo_client()


class TestReportCommand:
    """Test the report command."""

    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()

    @patch("src.portfolio.cli._get_bitvavo_client")
    @patch("src.portfolio.cli.get_portfolio_assets")
    @patch("src.portfolio.cli._generate_report_table")
    def test_report_default_assets(
        self, mock_generate, mock_get_assets, mock_get_client
    ):
        """Test report command with default assets."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_get_assets.return_value = ["BTC", "ETH"]

        result = self.runner.invoke(app, ["report"])

        assert result.exit_code == 0
        mock_get_assets.assert_called_once_with(mock_client)
        mock_generate.assert_called_once_with(mock_client, ["BTC", "ETH"], {})

    @patch("src.portfolio.cli._get_bitvavo_client")
    @patch("src.portfolio.cli._generate_report_table")
    def test_report_specific_assets(self, mock_generate, mock_get_client):
        """Test report command with specific assets."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = self.runner.invoke(app, ["report", "--assets", "BTC,ETH"])

        assert result.exit_code == 0
        mock_generate.assert_called_once_with(mock_client, ["BTC", "ETH"], {})

    @patch("src.portfolio.cli._get_bitvavo_client")
    @patch("src.portfolio.cli._generate_report_table")
    def test_report_with_price_override(self, mock_generate, mock_get_client):
        """Test report command with price overrides."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = self.runner.invoke(
            app, ["report", "--assets", "BTC", "--override", "BTC=35000"]
        )

        assert result.exit_code == 0
        expected_override = {"BTC": Decimal("35000")}
        mock_generate.assert_called_once_with(mock_client, ["BTC"], expected_override)

    @patch("src.portfolio.cli._get_bitvavo_client")
    @patch("src.portfolio.cli.get_portfolio_assets")
    def test_report_no_assets_found(self, mock_get_assets, mock_get_client):
        """Test report command when no assets are found."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_get_assets.return_value = []

        result = self.runner.invoke(app, ["report"])

        assert result.exit_code == 1
        assert "No assets found" in result.stdout


class TestWhatIfCommand:
    """Test the whatif command."""

    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()

    @patch("src.portfolio.cli._get_bitvavo_client")
    @patch("src.portfolio.cli._generate_report_table")
    def test_whatif_single_asset(self, mock_generate, mock_get_client):
        """Test whatif command with single asset."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = self.runner.invoke(app, ["whatif", "BTC=35000"])

        assert result.exit_code == 0
        expected_override = {"BTC": Decimal("35000")}
        mock_generate.assert_called_once_with(mock_client, ["BTC"], expected_override)

    @patch("src.portfolio.cli._get_bitvavo_client")
    @patch("src.portfolio.cli._generate_report_table")
    def test_whatif_multiple_assets(self, mock_generate, mock_get_client):
        """Test whatif command with multiple assets."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = self.runner.invoke(app, ["whatif", "BTC=35000", "--assets", "BTC,ETH"])

        assert result.exit_code == 0
        expected_override = {"BTC": Decimal("35000")}
        mock_generate.assert_called_once_with(
            mock_client, ["BTC", "ETH"], expected_override
        )

    def test_whatif_invalid_format(self):
        """Test whatif command with invalid price format."""
        result = self.runner.invoke(app, ["whatif", "BTC35000"])

        assert result.exit_code == 1
        assert "Price must be in format ASSET=PRICE" in result.output

    def test_whatif_invalid_price(self):
        """Test whatif command with invalid price value."""
        result = self.runner.invoke(app, ["whatif", "BTC=invalid"])

        assert result.exit_code == 1
        assert "Invalid price value" in result.output


class TestSyncBalancesCommand:
    """Test the sync-balances command."""

    def test_sync_balances_stub(self):
        """Test sync-balances command (stub implementation)."""
        runner = CliRunner()
        result = runner.invoke(app, ["sync-balances"])

        assert result.exit_code == 0
        assert "Feature coming soon" in result.stdout


class TestCLIIntegration:
    """Integration tests for CLI commands."""

    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()

    def test_help_message(self):
        """Test CLI help message."""
        result = self.runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "Crypto Portfolio FIFO P&L Analysis Tool" in result.stdout

    def test_report_help(self):
        """Test report command help."""
        result = self.runner.invoke(app, ["report", "--help"])

        assert result.exit_code == 0
        assert "Generate FIFO P&L report" in result.stdout

    def test_whatif_help(self):
        """Test whatif command help."""
        result = self.runner.invoke(app, ["whatif", "--help"])

        assert result.exit_code == 0
        assert "Run what-if scenario" in result.stdout
