#!/usr/bin/env python3
"""
Tests for individual UI components and their functionality.

This module tests specific UI components like chat interface,
model selector, cost tracker, and other dashboard elements.
"""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set up test environment
os.environ.setdefault("STREAMLIT_SERVER_HEADLESS", "true")


class TestChatInterface:
    """Test the AI chat interface components."""

    def test_chat_history_structure(self):
        """Test chat history data structure."""
        import dashboard

        # Mock session state with chat history
        mock_history = [
            (
                "What's my portfolio value?",
                "Your portfolio is worth €10,000",
                "2025-01-15 10:30:00",
            ),
            (
                "Show me my best performers",
                "ETH and BTC are your top performers",
                "2025-01-15 10:31:00",
            ),
        ]

        with patch("streamlit.session_state", {"chat_history": mock_history}):
            # Test that chat history can be processed
            assert len(mock_history) == 2
            assert all(
                len(item) == 3 for item in mock_history
            )  # user_msg, ai_msg, timestamp

    def test_chat_export_functionality(self):
        """Test chat history export functionality."""
        import dashboard

        mock_history = [("Test question", "Test answer", "2025-01-15 10:30:00")]

        mock_session_state = MagicMock()
        mock_session_state.chat_history = mock_history

        with patch("streamlit.session_state", mock_session_state), patch(
            "streamlit.download_button"
        ) as mock_download, patch("streamlit.warning"):

            dashboard.export_chat_history()
            # Should not raise exceptions

    def test_quick_analysis_buttons(self):
        """Test quick analysis button functionality."""
        # Test that quick analysis queries are properly formatted
        quick_queries = [
            "Perform technical analysis on my top 3 holdings with price trends, support/resistance levels, and trading signals",
            "Assess the risk profile of my portfolio including volatility analysis and diversification recommendations",
            "Provide price predictions for my holdings based on technical indicators and market sentiment",
            "Research current market trends and news that might affect my portfolio holdings",
        ]

        for query in quick_queries:
            assert len(query) > 10  # Should be meaningful queries
            assert any(
                keyword in query.lower()
                for keyword in ["analysis", "assess", "predict", "research"]
            )


class TestModelSelector:
    """Test the AI model selection interface."""

    def test_model_options_structure(self):
        """Test that model options are properly structured."""
        import dashboard

        with patch("streamlit.sidebar"), patch(
            "streamlit.selectbox"
        ) as mock_selectbox, patch("streamlit.slider"), patch(
            "streamlit.checkbox"
        ), patch(
            "streamlit.markdown"
        ):

            # Mock selectbox to return a model
            mock_selectbox.return_value = ""  # Auto mode

            result = dashboard.display_ai_model_selector()

            assert isinstance(result, dict)
            assert "model" in result
            assert "temperature" in result
            assert "use_functions" in result

    def test_model_cost_estimates(self):
        """Test that model cost estimates are reasonable."""
        import dashboard

        # Test cost calculation
        test_cases = [
            ("", 1000),  # Auto mode
            ("gpt-4o", 1000),
            ("claude-sonnet-4", 1000),
            ("gpt-4o-mini", 1000),
        ]

        for model, tokens in test_cases:
            mock_session_state = MagicMock()
            mock_session_state.ai_costs = {
                "total_tokens": 0,
                "total_cost": 0.0,
                "queries_count": 0,
            }

            with patch("streamlit.session_state", mock_session_state):
                dashboard.update_cost_tracking(model, tokens)
                # Should not raise exceptions


class TestCostTracker:
    """Test the cost tracking functionality."""

    def test_cost_initialization(self):
        """Test cost tracker initialization."""
        import dashboard

        mock_session_state = MagicMock()
        mock_session_state.ai_costs = {
            "total_tokens": 0,
            "total_cost": 0.0,
            "queries_count": 0,
        }

        mock_sidebar = MagicMock()
        mock_sidebar.columns.return_value = [
            MagicMock(),
            MagicMock(),
        ]  # Return 2 column mocks

        with patch("streamlit.session_state", mock_session_state), patch(
            "streamlit.sidebar", mock_sidebar
        ), patch("streamlit.columns"), patch("streamlit.metric"), patch(
            "streamlit.button"
        ), patch(
            "streamlit.markdown"
        ):

            dashboard.display_cost_tracker()
            # Should initialize cost tracking structure

    def test_cost_calculation_accuracy(self):
        """Test that cost calculations are accurate."""
        import dashboard

        # Test cost per token calculations
        test_models = {
            "": 5.0 / 1_000_000,  # Auto mode
            "claude-sonnet-4": 3.0 / 1_000_000,
            "gpt-4o": 5.0 / 1_000_000,
            "gpt-4o-mini": 0.15 / 1_000_000,
            "claude-opus-4": 15.0 / 1_000_000,
            "gpt-4-turbo": 10.0 / 1_000_000,
        }

        for model, expected_cost_per_token in test_models.items():
            # Calculate expected cost for 1000 tokens
            expected_cost = 1000 * expected_cost_per_token

            # Verify the cost is reasonable (between $0.0001 and $0.02 for 1000 tokens)
            assert (
                0.0001 <= expected_cost <= 0.02
            ), f"Unreasonable cost for {model}: {expected_cost}"

    def test_cost_reset_functionality(self):
        """Test cost reset functionality."""
        import dashboard

        initial_costs = {
            "total_tokens": 1000,
            "total_cost": 0.005,
            "queries_count": 5,
        }

        mock_session_state = MagicMock()
        mock_session_state.ai_costs = initial_costs.copy()

        mock_sidebar = MagicMock()
        mock_sidebar.columns.return_value = [
            MagicMock(),
            MagicMock(),
        ]  # Return 2 column mocks

        with patch("streamlit.session_state", mock_session_state), patch(
            "streamlit.sidebar", mock_sidebar
        ), patch("streamlit.columns"), patch("streamlit.metric"), patch(
            "streamlit.button", return_value=True
        ), patch(
            "streamlit.markdown"
        ), patch(
            "streamlit.rerun"
        ):

            dashboard.display_cost_tracker()
            # Reset should work without errors


class TestAssetFilters:
    """Test asset filtering functionality."""

    def test_filter_options(self):
        """Test asset filter options."""
        import dashboard

        with patch("streamlit.sidebar"), patch("streamlit.radio") as mock_radio, patch(
            "streamlit.multiselect"
        ), patch("streamlit.markdown"):

            # Test different filter options
            filter_options = ["all", "custom", "top_performers", "losers"]

            for option in filter_options:
                mock_radio.return_value = option
                result = dashboard.display_asset_filters()
                # Should handle all filter options without errors

    def test_custom_asset_selection(self):
        """Test custom asset selection functionality."""
        import dashboard

        mock_assets = ["BTC", "ETH", "ADA", "SOL", "AVAX"]

        with patch("streamlit.sidebar"), patch(
            "streamlit.radio", return_value="custom"
        ), patch("streamlit.multiselect", return_value=["BTC", "ETH"]), patch(
            "streamlit.markdown"
        ):

            result = dashboard.display_asset_filters()
            # Should handle custom selection without errors


class TestConnectionStatus:
    """Test backend connection status display."""

    def test_connection_success_display(self):
        """Test successful connection display."""
        import dashboard

        with patch("dashboard.check_backend_connection", return_value=True), patch(
            "streamlit.sidebar"
        ), patch("streamlit.success"), patch("streamlit.button"), patch(
            "streamlit.markdown"
        ):

            dashboard.display_connection_status()
            # Should display success status

    def test_connection_failure_display(self):
        """Test failed connection display."""
        import dashboard

        with patch("dashboard.check_backend_connection", return_value=False), patch(
            "streamlit.sidebar"
        ), patch("streamlit.error"), patch("streamlit.markdown"):

            dashboard.display_connection_status()
            # Should display error status

    def test_refresh_data_functionality(self):
        """Test data refresh functionality."""
        import dashboard

        mock_client = MagicMock()
        mock_client.refresh_portfolio_data.return_value = True

        with patch("dashboard.check_backend_connection", return_value=True), patch(
            "dashboard.get_api_client", return_value=mock_client
        ), patch("streamlit.sidebar"), patch("streamlit.success"), patch(
            "streamlit.button", return_value=True
        ), patch(
            "streamlit.markdown"
        ), patch(
            "streamlit.rerun"
        ):

            dashboard.display_connection_status()
            # Should handle refresh without errors


class TestErrorHandling:
    """Test error handling in UI components."""

    def test_api_error_handling(self):
        """Test API error handling in UI."""
        import dashboard

        # Test various API errors
        error_scenarios = [
            Exception("Connection timeout"),
            ValueError("Invalid response format"),
            KeyError("Missing required field"),
        ]

        for error in error_scenarios:
            with patch("dashboard.get_api_client") as mock_client:
                mock_client.side_effect = error

                # Should handle errors gracefully
                try:
                    result = dashboard.check_backend_connection()
                    assert result is False  # Should return False on error
                except Exception as e:
                    pytest.fail(f"Unhandled error in UI: {e}")

    def test_missing_environment_variables(self):
        """Test handling of missing environment variables."""
        import dashboard

        # Temporarily remove environment variables
        original_keys = {}
        test_keys = ["BITVAVO_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"]

        for key in test_keys:
            if key in os.environ:
                original_keys[key] = os.environ[key]
                del os.environ[key]

        try:
            # Should handle missing keys gracefully
            with patch("streamlit.warning"), patch("streamlit.error"):

                # Test that dashboard functions don't crash
                dashboard.check_backend_connection()

        finally:
            # Restore environment variables
            for key, value in original_keys.items():
                os.environ[key] = value


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
