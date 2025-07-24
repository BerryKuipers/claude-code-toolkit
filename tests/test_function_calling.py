"""
Comprehensive tests for function calling capabilities.
Tests all new advanced functions including web search, market analysis, and portfolio awareness.
"""

import os
import sys
from unittest.mock import MagicMock, Mock, patch

import pandas as pd
import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


class TestFunctionCallingSuite:
    """Test suite for all function calling capabilities."""

    @pytest.fixture
    def sample_portfolio_data(self):
        """Create comprehensive sample portfolio data for testing."""
        return pd.DataFrame(
            {
                "Asset": ["BTC", "ETH", "ADA", "SOL", "MATIC"],
                "Actual Amount": [0.5, 2.0, 1000.0, 10.0, 500.0],
                "Current Price €": [45000, 3000, 0.5, 100, 1.2],
                "Actual Value €": [22500, 6000, 500, 1000, 600],
                "Cost €": [20000, 5500, 600, 800, 700],
                "Total Invested €": [20000, 5500, 600, 800, 700],
                "Realised €": [0, 0, 0, 0, 0],
                "Unrealised €": [2500, 500, -100, 200, -100],
                "Total Return %": [12.5, 9.1, -16.7, 25.0, -14.3],
            }
        )

    @pytest.fixture
    def function_handler(self, sample_portfolio_data):
        """Create PortfolioFunctionHandler instance."""
        from src.portfolio.chat.function_handlers import PortfolioFunctionHandler

        return PortfolioFunctionHandler(sample_portfolio_data)

    def test_get_current_holdings(self, function_handler):
        """Test get_current_holdings function."""
        result = function_handler.handle_function_call("get_current_holdings", "{}")

        # Parse JSON result
        import json

        parsed_result = json.loads(result)

        assert "total_holdings" in parsed_result
        assert "total_value_eur" in parsed_result
        assert "holdings" in parsed_result
        assert parsed_result["total_holdings"] == 5
        assert len(parsed_result["holdings"]) == 5

        # Check that holdings are sorted by value (BTC should be first)
        assert parsed_result["holdings"][0]["asset"] == "BTC"
        assert parsed_result["holdings"][0]["value_eur"] == 22500.0

        # Check allocation percentages
        btc_allocation = parsed_result["holdings"][0]["allocation_pct"]
        assert isinstance(btc_allocation, float)
        assert btc_allocation > 70  # BTC should be largest holding

    @patch.dict(
        os.environ, {"PERPLEXITY_API_KEY": "test_key", "PERPLEXITY_MODEL": "sonar-pro"}
    )
    @patch("requests.post")
    def test_search_crypto_news(self, mock_post, function_handler):
        """Test search_crypto_news function with Perplexity API."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "Bitcoin is showing strong momentum with institutional adoption increasing..."
                    }
                }
            ]
        }
        mock_post.return_value = mock_response

        # Test the function
        result = function_handler.handle_function_call(
            "search_crypto_news",
            '{"query": "Bitcoin price prediction 2024", "focus": "analysis"}',
        )

        # Parse result
        import json

        parsed_result = json.loads(result)

        assert "query" in parsed_result
        assert "research_results" in parsed_result
        assert "source" in parsed_result
        assert parsed_result["query"] == "Bitcoin price prediction 2024"
        assert parsed_result["focus"] == "analysis"
        assert parsed_result["source"] == "Perplexity AI"
        assert "Bitcoin" in parsed_result["research_results"]

        # Verify API was called correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "https://api.perplexity.ai/chat/completions" in call_args[0]

        # Check request data
        request_data = call_args[1]["json"]
        assert request_data["model"] == "sonar-pro"
        assert len(request_data["messages"]) == 2
        assert "Bitcoin price prediction 2024" in request_data["messages"][1]["content"]

    @patch.dict(os.environ, {"PERPLEXITY_API_KEY": "test_key"})
    @patch(
        "src.portfolio.chat.function_handlers.PortfolioFunctionHandler._search_crypto_news"
    )
    def test_analyze_market_opportunities(self, mock_search, function_handler):
        """Test analyze_market_opportunities function."""
        # Mock the search function
        mock_search.return_value = {
            "research_results": "DeFi sector showing strong growth with new protocols launching...",
            "query": "DeFi opportunities",
            "focus": "analysis",
        }

        result = function_handler.handle_function_call(
            "analyze_market_opportunities", '{"sector": "defi", "timeframe": "medium"}'
        )

        # Parse result
        import json

        parsed_result = json.loads(result)

        assert "sector" in parsed_result
        assert "timeframe" in parsed_result
        assert "market_analysis" in parsed_result
        assert parsed_result["sector"] == "defi"
        assert parsed_result["timeframe"] == "medium"
        assert "DeFi" in parsed_result["market_analysis"]

        # Verify search was called with correct query
        mock_search.assert_called_once()
        call_args = mock_search.call_args[0]
        assert "DeFi" in call_args[0]

    def test_compare_with_market(self, function_handler):
        """Test compare_with_market function."""
        with patch.object(function_handler, "_search_crypto_news") as mock_search:
            mock_search.return_value = {
                "research_results": "Bitcoin has gained 15% in the last 30 days...",
                "query": "Bitcoin performance",
            }

            result = function_handler.handle_function_call(
                "compare_with_market", '{"benchmark": "btc", "timeframe": "30d"}'
            )

            # Parse result
            import json

            parsed_result = json.loads(result)

            assert "portfolio_return_pct" in parsed_result
            assert "benchmark" in parsed_result
            assert "timeframe" in parsed_result
            assert "benchmark_analysis" in parsed_result
            assert parsed_result["benchmark"] == "btc"
            assert parsed_result["timeframe"] == "30d"
            assert isinstance(parsed_result["portfolio_return_pct"], (int, float))

    def test_get_trading_signals(self, function_handler):
        """Test get_trading_signals function."""
        with patch.object(function_handler, "_search_crypto_news") as mock_search:
            mock_search.return_value = {
                "research_results": "BTC showing bullish signals with RSI at 65...",
                "query": "BTC technical analysis",
            }

            result = function_handler.handle_function_call(
                "get_trading_signals",
                '{"assets": ["BTC", "ETH"], "strategy": "moderate"}',
            )

            # Parse result
            import json

            parsed_result = json.loads(result)

            assert "strategy" in parsed_result
            assert "signals_generated" in parsed_result
            assert "trading_signals" in parsed_result
            assert parsed_result["strategy"] == "moderate"
            assert parsed_result["signals_generated"] == 2
            assert len(parsed_result["trading_signals"]) == 2

            # Check signal structure
            signal = parsed_result["trading_signals"][0]
            assert "asset" in signal
            assert "analysis" in signal
            assert "recommendation" in signal

    def test_find_similar_assets(self, function_handler):
        """Test find_similar_assets function."""
        with patch.object(function_handler, "_search_crypto_news") as mock_search:
            mock_search.return_value = {
                "research_results": "Assets similar to Ethereum include Cardano, Solana, and Avalanche...",
                "query": "Ethereum similar assets",
            }

            result = function_handler.handle_function_call(
                "find_similar_assets",
                '{"reference_asset": "ETH", "criteria": "technology"}',
            )

            # Parse result
            import json

            parsed_result = json.loads(result)

            assert "reference_asset" in parsed_result
            assert "criteria" in parsed_result
            assert "currently_held" in parsed_result
            assert "similar_assets_analysis" in parsed_result
            assert "current_holdings" in parsed_result
            assert parsed_result["reference_asset"] == "ETH"
            assert parsed_result["criteria"] == "technology"
            assert parsed_result["currently_held"] is True  # ETH is in sample data
            assert "ETH" in parsed_result["current_holdings"]

    def test_function_availability(self, function_handler):
        """Test that all new functions are available."""
        functions = function_handler.get_available_functions()
        function_names = [f["name"] for f in functions]

        # Check that all new functions are available
        expected_functions = [
            "get_current_holdings",
            "search_crypto_news",
            "analyze_market_opportunities",
            "compare_with_market",
            "get_trading_signals",
            "find_similar_assets",
        ]

        for func_name in expected_functions:
            assert (
                func_name in function_names
            ), f"Function {func_name} not found in available functions"

        # Check total function count (should be more than before)
        assert (
            len(functions) >= 16
        ), f"Expected at least 16 functions, got {len(functions)}"

    def test_error_handling_missing_api_key(self, function_handler):
        """Test error handling when API keys are missing."""
        with patch.dict(os.environ, {}, clear=True):
            result = function_handler.handle_function_call(
                "search_crypto_news", '{"query": "Bitcoin news"}'
            )

            # Parse result
            import json

            parsed_result = json.loads(result)

            assert "error" in parsed_result
            assert "Perplexity API key not configured" in parsed_result["error"]

    @patch("requests.post")
    def test_api_error_handling(self, mock_post, function_handler):
        """Test handling of API errors."""
        with patch.dict(os.environ, {"PERPLEXITY_API_KEY": "test_key"}):
            # Mock API error response
            mock_response = Mock()
            mock_response.status_code = 429  # Rate limit error
            mock_post.return_value = mock_response

            result = function_handler.handle_function_call(
                "search_crypto_news", '{"query": "Bitcoin news"}'
            )

            # Parse result
            import json

            parsed_result = json.loads(result)

            assert "error" in parsed_result
            assert "429" in parsed_result["error"]


class TestFunctionIntegration:
    """Test integration between functions and chat system."""

    @pytest.fixture
    def sample_portfolio_data(self):
        """Create sample portfolio data."""
        return pd.DataFrame(
            {
                "Asset": ["BTC", "ETH", "MATIC", "SOL"],
                "Actual Amount": [0.5, 2.0, 500.0, 10.0],
                "Current Price €": [45000, 3000, 1.2, 100],
                "Actual Value €": [22500, 6000, 600, 1000],
                "Cost €": [20000, 5500, 700, 800],
                "Total Invested €": [20000, 5500, 700, 800],
                "Realised €": [0, 0, 0, 0],
                "Unrealised €": [2500, 500, -100, 200],
                "Total Return %": [12.5, 9.1, -14.3, 25.0],
            }
        )

    def test_investment_recommendation_workflow(self, sample_portfolio_data):
        """Test the complete workflow for investment recommendations."""
        from src.portfolio.chat.function_handlers import PortfolioFunctionHandler

        handler = PortfolioFunctionHandler(sample_portfolio_data)

        # Step 1: Get current holdings (should be called first)
        holdings_result = handler.handle_function_call("get_current_holdings", "{}")
        import json

        holdings = json.loads(holdings_result)

        assert "holdings" in holdings
        current_assets = [h["asset"] for h in holdings["holdings"]]
        assert "BTC" in current_assets
        assert "ETH" in current_assets
        assert "MATIC" in current_assets  # This should be mentioned if recommended

        # Step 2: Portfolio summary
        summary_result = handler.handle_function_call("get_portfolio_summary", "{}")
        summary = json.loads(summary_result)

        assert "total_value_eur" in summary
        assert float(summary["total_value_eur"]) > 0

        # The workflow should now be aware that MATIC is already held
        # when making recommendations
        assert len(current_assets) == 4  # BTC, ETH, MATIC, SOL


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
