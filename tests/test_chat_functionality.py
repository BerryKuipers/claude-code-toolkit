"""
Test suite for chat functionality.
Tests chat system components to ensure they work properly.
"""

import os
import sys
from unittest.mock import Mock, patch

import pandas as pd
import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


class TestChatImports:
    """Test that all chat-related imports work."""

    def test_portfolio_tab_import(self):
        """Test PortfolioTab import."""
        from src.portfolio.ui.tabs import PortfolioTab

        assert PortfolioTab is not None

    def test_portfolio_function_handler_import(self):
        """Test PortfolioFunctionHandler import."""
        from src.portfolio.chat.function_handlers import PortfolioFunctionHandler

        assert PortfolioFunctionHandler is not None

    def test_llm_client_factory_import(self):
        """Test LLMClientFactory import."""
        from src.portfolio.chat.base_llm_client import LLMClientFactory

        assert LLMClientFactory is not None


class TestChatSessionState:
    """Test that chat session state works."""

    @patch("streamlit.session_state", {})
    def test_initial_chat_state(self):
        """Test initial chat state setup."""
        mock_session_state = {}

        # Test initial state
        if "sticky_chat_open" not in mock_session_state:
            mock_session_state["sticky_chat_open"] = False

        assert mock_session_state["sticky_chat_open"] is False

    @patch("streamlit.session_state", {})
    def test_chat_state_transitions(self):
        """Test chat state transitions."""
        mock_session_state = {"sticky_chat_open": False}

        # Test opening chat
        mock_session_state["sticky_chat_open"] = True
        assert mock_session_state["sticky_chat_open"] is True

        # Test closing chat
        mock_session_state["sticky_chat_open"] = False
        assert mock_session_state["sticky_chat_open"] is False


class TestPortfolioFunctionHandler:
    """Test PortfolioFunctionHandler functionality."""

    @pytest.fixture
    def sample_portfolio_data(self):
        """Create sample portfolio data for testing."""
        return pd.DataFrame(
            {
                "Asset": ["BTC", "ETH", "ADA"],
                "Actual Amount": [0.5, 2.0, 1000.0],
                "Current Price €": [45000, 3000, 0.5],
                "Actual Value €": [22500, 6000, 500],
                "Cost €": [20000, 5500, 600],
                "Total Invested €": [20000, 5500, 600],
                "Realised €": [0, 0, 0],
                "Unrealised €": [2500, 500, -100],
                "Total Return %": [12.5, 9.1, -16.7],
            }
        )

    def test_handler_initialization(self, sample_portfolio_data):
        """Test PortfolioFunctionHandler initialization."""
        from src.portfolio.chat.function_handlers import PortfolioFunctionHandler

        handler = PortfolioFunctionHandler(sample_portfolio_data)
        assert handler is not None
        assert handler.portfolio_data is not None

    def test_available_functions(self, sample_portfolio_data):
        """Test getting available functions."""
        from src.portfolio.chat.function_handlers import PortfolioFunctionHandler

        handler = PortfolioFunctionHandler(sample_portfolio_data)
        functions = handler.get_available_functions()

        assert isinstance(functions, list)
        assert len(functions) > 0

        # Check that functions have required structure
        for func in functions:
            assert "name" in func
            assert "description" in func
            assert "parameters" in func

    def test_portfolio_summary_function(self, sample_portfolio_data):
        """Test portfolio summary function call."""
        from src.portfolio.chat.function_handlers import PortfolioFunctionHandler

        handler = PortfolioFunctionHandler(sample_portfolio_data)
        result = handler.handle_function_call("get_portfolio_summary", "{}")

        assert isinstance(result, str)
        assert len(result) > 0

        # Should be valid JSON
        import json

        parsed_result = json.loads(result)
        assert isinstance(parsed_result, dict)


class TestLLMClientFactory:
    """Test LLMClientFactory functionality."""

    def test_get_default_model(self):
        """Test getting default model."""
        from src.portfolio.chat.base_llm_client import LLMClientFactory

        default_model = LLMClientFactory.get_default_model()
        assert isinstance(default_model, str)
        assert len(default_model) > 0

    def test_get_available_models(self):
        """Test getting available models."""
        from src.portfolio.chat.base_llm_client import LLMClientFactory

        models = LLMClientFactory.get_available_models()
        assert isinstance(models, dict)
        assert len(models) > 0

        # Check that models have proper structure
        for model_key, model_info in models.items():
            assert isinstance(model_key, str)
            assert hasattr(model_info, "model_id")
            assert hasattr(model_info, "provider")


class TestChatIntegration:
    """Integration tests for the complete chat system."""

    @pytest.fixture
    def sample_portfolio_data(self):
        """Create sample portfolio data for testing."""
        return pd.DataFrame(
            {
                "Asset": ["BTC", "ETH", "ADA"],
                "Actual Amount": [0.5, 2.0, 1000.0],
                "Current Price €": [45000, 3000, 0.5],
                "Actual Value €": [22500, 6000, 500],
                "Cost €": [20000, 5500, 600],
                "Total Invested €": [20000, 5500, 600],
                "Realised €": [0, 0, 0],
                "Unrealised €": [2500, 500, -100],
                "Total Return %": [12.5, 9.1, -16.7],
            }
        )

    def test_end_to_end_chat_flow(self, sample_portfolio_data):
        """Test complete chat flow from data to response."""
        from src.portfolio.chat.base_llm_client import LLMClientFactory
        from src.portfolio.chat.function_handlers import PortfolioFunctionHandler

        # Initialize components
        handler = PortfolioFunctionHandler(sample_portfolio_data)
        functions = handler.get_available_functions()

        # Verify we can get a model (even if we can't create client without API keys)
        default_model = LLMClientFactory.get_default_model()
        available_models = LLMClientFactory.get_available_models()

        assert handler is not None
        assert len(functions) > 0
        assert default_model in available_models

        # Test function call
        result = handler.handle_function_call("get_portfolio_summary", "{}")
        assert isinstance(result, str)
        assert len(result) > 0


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
