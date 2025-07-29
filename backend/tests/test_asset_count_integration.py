"""
Comprehensive integration tests for asset count verification.

Tests the entire data flow from Bitvavo API -> Cache -> Portfolio Service -> Chat Service -> Frontend
to ensure consistent asset counts across all layers and identify where discrepancies occur.
"""

import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone
from typing import List, Dict, Any

# Test imports
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from backend.app.core.database import DevCacheDatabase
from backend.app.services.portfolio_service import PortfolioAPIService
from backend.app.services.chat_service import ChatService
from backend.app.core.config import Settings
from backend.app.models.portfolio import HoldingResponse


class TestAssetCountIntegration:
    """Integration tests for asset count consistency across all system layers."""
    
    @pytest.fixture
    def mock_settings(self):
        """Create mock settings for testing."""
        settings = Mock(spec=Settings)
        settings.enable_dev_cache = True
        settings.dev_cache_path = "test_cache.db"
        settings.openai_api_key = "test-key"
        settings.anthropic_api_key = "test-key"
        return settings
    
    @pytest.fixture
    def temp_cache_db(self):
        """Create temporary cache database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        cache = DevCacheDatabase(db_path)
        yield cache
        
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    @pytest.fixture
    def sample_holdings_data(self):
        """Create sample holdings data with mix of zero and non-zero balances."""
        return [
            # Non-zero holdings (active positions)
            {"asset": "BTC", "available": "0.5", "inOrder": "0.0"},
            {"asset": "ETH", "available": "2.5", "inOrder": "0.1"},
            {"asset": "ADA", "available": "1000.0", "inOrder": "0.0"},
            {"asset": "DOT", "available": "50.0", "inOrder": "5.0"},
            {"asset": "LINK", "available": "25.0", "inOrder": "0.0"},
            
            # Zero balance holdings (should be included with include_zero_balances=True)
            {"asset": "XRP", "available": "0.0", "inOrder": "0.0"},
            {"asset": "LTC", "available": "0.0", "inOrder": "0.0"},
            {"asset": "BCH", "available": "0.0", "inOrder": "0.0"},
            {"asset": "BNB", "available": "0.0", "inOrder": "0.0"},
            {"asset": "SOL", "available": "0.0", "inOrder": "0.0"},
            {"asset": "AVAX", "available": "0.0", "inOrder": "0.0"},
            {"asset": "MATIC", "available": "0.0", "inOrder": "0.0"},
            {"asset": "ATOM", "available": "0.0", "inOrder": "0.0"},
            {"asset": "ALGO", "available": "0.0", "inOrder": "0.0"},
            {"asset": "VET", "available": "0.0", "inOrder": "0.0"},
            
            # More zero balances to reach 48 total
            *[{"asset": f"TEST{i}", "available": "0.0", "inOrder": "0.0"} for i in range(1, 34)]
        ]
    
    @pytest.fixture
    def mock_bitvavo_client(self, sample_holdings_data):
        """Create mock Bitvavo client that returns sample data."""
        client = AsyncMock()
        
        # Mock balance method to return our sample data
        client.get_balance.return_value = sample_holdings_data
        
        # Mock price data for calculations
        client.get_ticker_price.return_value = {"price": "45000.0"}
        
        # Mock trade history (empty for simplicity)
        client.get_trades.return_value = []
        
        # Mock deposit/withdrawal history
        client.get_deposit_history.return_value = []
        client.get_withdrawal_history.return_value = []
        
        return client
    
    def test_sample_data_count(self, sample_holdings_data):
        """Verify our sample data has the expected count."""
        assert len(sample_holdings_data) == 48, f"Expected 48 holdings, got {len(sample_holdings_data)}"
        
        # Count non-zero vs zero balances
        non_zero = [h for h in sample_holdings_data if float(h["available"]) > 0 or float(h["inOrder"]) > 0]
        zero_balance = [h for h in sample_holdings_data if float(h["available"]) == 0 and float(h["inOrder"]) == 0]
        
        assert len(non_zero) == 5, f"Expected 5 non-zero holdings, got {len(non_zero)}"
        assert len(zero_balance) == 43, f"Expected 43 zero-balance holdings, got {len(zero_balance)}"
    
    @pytest.mark.asyncio
    async def test_bitvavo_client_returns_all_holdings(self, mock_bitvavo_client, sample_holdings_data):
        """Test that Bitvavo client returns all holdings including zeros."""
        holdings = await mock_bitvavo_client.get_balance()
        
        assert len(holdings) == 48, f"Bitvavo client should return 48 holdings, got {len(holdings)}"
        
        # Verify we have both zero and non-zero balances
        non_zero_count = sum(1 for h in holdings if float(h["available"]) > 0 or float(h["inOrder"]) > 0)
        zero_count = sum(1 for h in holdings if float(h["available"]) == 0 and float(h["inOrder"]) == 0)
        
        assert non_zero_count == 5, f"Expected 5 non-zero holdings, got {non_zero_count}"
        assert zero_count == 43, f"Expected 43 zero holdings, got {zero_count}"
    
    @pytest.mark.asyncio
    async def test_cache_stores_all_holdings(self, temp_cache_db, sample_holdings_data):
        """Test that cache stores all holdings including zeros."""
        cache = temp_cache_db
        
        # Cache the holdings data
        cache.cache_portfolio_holdings(sample_holdings_data, ttl_hours=1)
        
        # Retrieve cached data
        cached_holdings = cache.get_cached_portfolio_holdings()
        
        assert cached_holdings is not None, "Cache should return holdings data"
        assert len(cached_holdings) == 48, f"Cache should store 48 holdings, got {len(cached_holdings)}"
        
        # Verify cache stats
        stats = cache.get_cache_stats()
        assert stats["portfolio_holdings_total"] == 1, "Should have 1 portfolio holdings entry"
        assert stats["portfolio_holdings_valid"] == 1, "Should have 1 valid portfolio holdings entry"

    @pytest.mark.asyncio
    async def test_portfolio_service_include_zero_balances_true(self, mock_settings, mock_bitvavo_client):
        """Test portfolio service with include_zero_balances=True returns all holdings."""
        with patch('backend.app.core.container.Container') as mock_container:
            # Setup container mock
            container_instance = Mock()
            container_instance.get_bitvavo_api_client.return_value = mock_bitvavo_client
            mock_container.return_value = container_instance

            # Create portfolio service
            portfolio_service = PortfolioAPIService(mock_settings)

            # Test with include_zero_balances=True
            holdings = await portfolio_service.get_current_holdings(include_zero_balances=True)

            assert len(holdings) == 48, f"Portfolio service should return 48 holdings with include_zero_balances=True, got {len(holdings)}"

            # Verify we have both types of holdings
            non_zero_holdings = [h for h in holdings if h.quantity > 0]
            zero_holdings = [h for h in holdings if h.quantity == 0]

            assert len(non_zero_holdings) == 5, f"Expected 5 non-zero holdings, got {len(non_zero_holdings)}"
            assert len(zero_holdings) == 43, f"Expected 43 zero holdings, got {len(zero_holdings)}"

    @pytest.mark.asyncio
    async def test_portfolio_service_include_zero_balances_false(self, mock_settings, mock_bitvavo_client):
        """Test portfolio service with include_zero_balances=False filters out zero holdings."""
        with patch('backend.app.core.container.Container') as mock_container:
            # Setup container mock
            container_instance = Mock()
            container_instance.get_bitvavo_api_client.return_value = mock_bitvavo_client
            mock_container.return_value = container_instance

            # Create portfolio service
            portfolio_service = PortfolioAPIService(mock_settings)

            # Test with include_zero_balances=False (default)
            holdings = await portfolio_service.get_current_holdings(include_zero_balances=False)

            assert len(holdings) == 5, f"Portfolio service should return 5 holdings with include_zero_balances=False, got {len(holdings)}"

            # Verify all returned holdings have non-zero quantities
            for holding in holdings:
                assert holding.quantity > 0, f"All holdings should have quantity > 0, found {holding.asset} with {holding.quantity}"

    @pytest.mark.asyncio
    async def test_chat_service_gets_all_holdings(self, mock_settings, mock_bitvavo_client):
        """Test that chat service function handler gets all 48 holdings."""
        with patch('backend.app.core.container.Container') as mock_container:
            # Setup container mock
            container_instance = Mock()
            container_instance.get_bitvavo_api_client.return_value = mock_bitvavo_client
            mock_container.return_value = container_instance

            # Create portfolio service
            portfolio_service = PortfolioAPIService(mock_settings)

            # Create chat service
            chat_service = ChatService(mock_settings, portfolio_service)

            # Get function handler (this should use include_zero_balances=True)
            function_handler = await chat_service._get_function_handler()

            # Check the portfolio data in the function handler
            portfolio_df = function_handler.portfolio_data

            assert len(portfolio_df) == 48, f"Chat service function handler should have 48 holdings, got {len(portfolio_df)}"

            # Verify we have both zero and non-zero holdings
            non_zero_count = len(portfolio_df[portfolio_df["Actual Amount"] > 0])
            zero_count = len(portfolio_df[portfolio_df["Actual Amount"] == 0])

            assert non_zero_count == 5, f"Expected 5 non-zero holdings in chat service, got {non_zero_count}"
            assert zero_count == 43, f"Expected 43 zero holdings in chat service, got {zero_count}"

    @pytest.mark.asyncio
    async def test_frontend_api_endpoints_consistency(self, mock_settings, mock_bitvavo_client):
        """Test that frontend API endpoints return consistent data."""
        with patch('backend.app.core.container.Container') as mock_container:
            # Setup container mock
            container_instance = Mock()
            container_instance.get_bitvavo_api_client.return_value = mock_bitvavo_client
            mock_container.return_value = container_instance

            # Create portfolio service
            portfolio_service = PortfolioAPIService(mock_settings)

            # Test /api/v1/portfolio/holdings endpoint (default behavior)
            holdings_default = await portfolio_service.get_current_holdings()
            assert len(holdings_default) == 5, f"Default holdings endpoint should return 5 holdings, got {len(holdings_default)}"

            # Test /api/v1/portfolio/holdings?include_zero_balances=true
            holdings_with_zeros = await portfolio_service.get_current_holdings(include_zero_balances=True)
            assert len(holdings_with_zeros) == 48, f"Holdings with zeros should return 48 holdings, got {len(holdings_with_zeros)}"

            # Test /api/v1/portfolio/data endpoint (used by frontend overview)
            portfolio_data = await portfolio_service.get_portfolio_data()
            holdings_from_data = portfolio_data.holdings

            # This should match the default behavior (non-zero holdings only)
            assert len(holdings_from_data) == 5, f"Portfolio data should return 5 holdings, got {len(holdings_from_data)}"

    @pytest.mark.asyncio
    async def test_cache_consistency_across_calls(self, mock_settings, mock_bitvavo_client, temp_cache_db):
        """Test that cache provides consistent data across multiple calls."""
        with patch('backend.app.core.database.get_dev_cache') as mock_get_cache:
            mock_get_cache.return_value = temp_cache_db

            with patch('backend.app.core.container.Container') as mock_container:
                # Setup container mock
                container_instance = Mock()
                container_instance.get_bitvavo_api_client.return_value = mock_bitvavo_client
                mock_container.return_value = container_instance

                # Create portfolio service
                portfolio_service = PortfolioAPIService(mock_settings)

                # First call - should hit API and cache result
                holdings1 = await portfolio_service.get_current_holdings(include_zero_balances=True)
                assert len(holdings1) == 48, f"First call should return 48 holdings, got {len(holdings1)}"

                # Second call - should use cache
                holdings2 = await portfolio_service.get_current_holdings(include_zero_balances=True)
                assert len(holdings2) == 48, f"Second call should return 48 holdings, got {len(holdings2)}"

                # Verify cache has data
                cached_data = temp_cache_db.get_cached_portfolio_holdings()
                assert cached_data is not None, "Cache should contain portfolio data"
                assert len(cached_data) == 48, f"Cached data should have 48 holdings, got {len(cached_data)}"

    @pytest.mark.asyncio
    async def test_chat_service_performance_without_cache(self, mock_settings, mock_bitvavo_client):
        """Test that chat service performs well without its own cache layer."""
        import time

        with patch('backend.app.core.container.Container') as mock_container:
            # Setup container mock
            container_instance = Mock()
            container_instance.get_bitvavo_api_client.return_value = mock_bitvavo_client
            mock_container.return_value = container_instance

            # Create portfolio service and chat service
            portfolio_service = PortfolioAPIService(mock_settings)
            chat_service = ChatService(mock_settings, portfolio_service)

            # Time multiple function handler calls
            times = []
            for i in range(3):
                start_time = time.time()
                function_handler = await chat_service._get_function_handler()
                end_time = time.time()

                times.append(end_time - start_time)

                # Verify data consistency
                assert len(function_handler.portfolio_data) == 48, f"Call {i+1} should return 48 holdings"

            # Performance should be reasonable (under 1 second per call)
            avg_time = sum(times) / len(times)
            assert avg_time < 1.0, f"Average call time should be under 1 second, got {avg_time:.2f}s"

    def test_asset_filtering_logic(self, sample_holdings_data):
        """Test the logic for filtering zero vs non-zero balances."""
        # Test include_zero_balances=True logic
        all_holdings = sample_holdings_data
        assert len(all_holdings) == 48, "Should include all holdings"

        # Test include_zero_balances=False logic
        non_zero_holdings = [
            h for h in sample_holdings_data
            if float(h["available"]) > 0 or float(h["inOrder"]) > 0
        ]
        assert len(non_zero_holdings) == 5, f"Should filter to 5 non-zero holdings, got {len(non_zero_holdings)}"

        # Verify the specific assets that should be included
        non_zero_assets = {h["asset"] for h in non_zero_holdings}
        expected_assets = {"BTC", "ETH", "ADA", "DOT", "LINK"}
        assert non_zero_assets == expected_assets, f"Expected {expected_assets}, got {non_zero_assets}"

    @pytest.mark.asyncio
    async def test_real_world_scenario_simulation(self, mock_settings, temp_cache_db):
        """Simulate real-world scenario with actual API-like data."""
        # Create more realistic holdings data
        realistic_holdings = [
            # Active positions with various amounts
            {"asset": "BTC", "available": "0.12345678", "inOrder": "0.0"},
            {"asset": "ETH", "available": "2.5", "inOrder": "0.1"},
            {"asset": "ADA", "available": "1000.0", "inOrder": "0.0"},

            # Small positions
            {"asset": "DOT", "available": "0.001", "inOrder": "0.0"},
            {"asset": "LINK", "available": "0.0001", "inOrder": "0.0"},

            # Zero balances from previous trades
            *[{"asset": f"ASSET{i}", "available": "0.0", "inOrder": "0.0"} for i in range(1, 44)]
        ]

        # Mock client with realistic data
        mock_client = AsyncMock()
        mock_client.get_balance.return_value = realistic_holdings
        mock_client.get_ticker_price.return_value = {"price": "45000.0"}
        mock_client.get_trades.return_value = []
        mock_client.get_deposit_history.return_value = []
        mock_client.get_withdrawal_history.return_value = []

        with patch('backend.app.core.database.get_dev_cache') as mock_get_cache:
            mock_get_cache.return_value = temp_cache_db

            with patch('backend.app.core.container.Container') as mock_container:
                container_instance = Mock()
                container_instance.get_bitvavo_api_client.return_value = mock_client
                mock_container.return_value = container_instance

                # Test the full flow
                portfolio_service = PortfolioAPIService(mock_settings)
                chat_service = ChatService(mock_settings, portfolio_service)

                # Frontend overview call (non-zero balances)
                overview_holdings = await portfolio_service.get_current_holdings(include_zero_balances=False)
                assert len(overview_holdings) == 5, f"Overview should show 5 active holdings, got {len(overview_holdings)}"

                # Chat service call (all balances for analysis)
                function_handler = await chat_service._get_function_handler()
                chat_holdings = function_handler.portfolio_data
                assert len(chat_holdings) == 48, f"Chat should have 48 total holdings, got {len(chat_holdings)}"

                # Verify data consistency
                active_in_chat = len(chat_holdings[chat_holdings["Actual Amount"] > 0])
                assert active_in_chat == 5, f"Chat should show 5 active holdings, got {active_in_chat}"
