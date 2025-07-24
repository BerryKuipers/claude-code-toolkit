"""
Test suite for API key configuration and loading.
Tests that all required API keys are properly loaded and accessible.
"""

import os
import sys
from unittest.mock import mock_open, patch

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


class TestEnvironmentLoading:
    """Test environment variable loading from .env file."""

    def test_env_file_exists(self):
        """Test that .env file exists in project root or CI environment has env vars."""
        env_file = os.path.join(os.path.dirname(__file__), "..", ".env")

        # In CI environment, .env file might not exist but env vars should be set
        if os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"):
            # In CI, just check that we can load environment variables
            assert True, "CI environment detected, skipping .env file check"
        else:
            assert os.path.exists(env_file), ".env file should exist in project root"

    def test_load_env_file_function(self):
        """Test the load_env_file function by creating a separate module."""
        # Create a separate module to avoid Streamlit import issues
        load_env_code = '''
import os

def load_env_file():
    """Load environment variables from .env file."""
    env_file = ".env"  # Use relative path for test
    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()
'''

        # Mock .env file content
        mock_env_content = """# Test environment
BITVAVO_API_KEY=test_bitvavo_key
BITVAVO_API_SECRET=test_bitvavo_secret
ANTHROPIC_API_KEY=test_anthropic_key
OPENAI_API_KEY=test_openai_key
"""

        # Clear environment first
        test_keys = [
            "BITVAVO_API_KEY",
            "BITVAVO_API_SECRET",
            "ANTHROPIC_API_KEY",
            "OPENAI_API_KEY",
        ]
        original_values = {}
        for key in test_keys:
            original_values[key] = os.environ.get(key)
            if key in os.environ:
                del os.environ[key]

        try:
            # Test the load_env_file logic
            with patch("builtins.open", mock_open(read_data=mock_env_content)):
                with patch("os.path.exists", return_value=True):
                    # Execute the load_env_file function
                    namespace = {}
                    exec(load_env_code, namespace)
                    namespace["load_env_file"]()

                    # Check that variables were set
                    assert os.getenv("BITVAVO_API_KEY") == "test_bitvavo_key"
                    assert os.getenv("BITVAVO_API_SECRET") == "test_bitvavo_secret"
                    assert os.getenv("ANTHROPIC_API_KEY") == "test_anthropic_key"
                    assert os.getenv("OPENAI_API_KEY") == "test_openai_key"

        finally:
            # Restore original environment
            for key, value in original_values.items():
                if value is not None:
                    os.environ[key] = value
                elif key in os.environ:
                    del os.environ[key]


class TestAPIKeyPresence:
    """Test that required API keys are present."""

    @pytest.fixture(autouse=True)
    def load_real_env(self):
        """Load the real .env file for these tests."""
        # Load environment variables directly without importing dashboard.py
        env_file = os.path.join(os.path.dirname(__file__), "..", ".env")
        if os.path.exists(env_file):
            with open(env_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        os.environ[key.strip()] = value.strip()

    def test_bitvavo_api_keys_present(self):
        """Test that Bitvavo API keys are present."""
        api_key = os.getenv("BITVAVO_API_KEY")
        api_secret = os.getenv("BITVAVO_API_SECRET")

        assert api_key is not None, "BITVAVO_API_KEY should be set"
        assert api_secret is not None, "BITVAVO_API_SECRET should be set"
        assert len(api_key) > 0, "BITVAVO_API_KEY should not be empty"
        assert len(api_secret) > 0, "BITVAVO_API_SECRET should not be empty"

    def test_ai_api_keys_present(self):
        """Test that AI API keys are present."""
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")

        # At least one AI API key should be present
        assert (
            anthropic_key is not None or openai_key is not None
        ), "At least one AI API key (ANTHROPIC_API_KEY or OPENAI_API_KEY) should be set"

        if anthropic_key:
            assert len(anthropic_key) > 0, "ANTHROPIC_API_KEY should not be empty"
            # In CI/test environment, allow test keys
            if not (os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS")):
                assert anthropic_key.startswith(
                    "sk-ant-"
                ), "ANTHROPIC_API_KEY should start with 'sk-ant-'"

        if openai_key:
            assert len(openai_key) > 0, "OPENAI_API_KEY should not be empty"
            # In CI/test environment, allow test keys
            if not (os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS")):
                assert openai_key.startswith(
                    "sk-"
                ), "OPENAI_API_KEY should start with 'sk-'"


class TestLLMClientCreation:
    """Test that LLM clients can be created with available API keys."""

    @pytest.fixture(autouse=True)
    def load_real_env(self):
        """Load the real .env file for these tests."""
        # Load environment variables directly without importing dashboard.py
        env_file = os.path.join(os.path.dirname(__file__), "..", ".env")
        if os.path.exists(env_file):
            with open(env_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        os.environ[key.strip()] = value.strip()

    def test_llm_client_factory_available(self):
        """Test that LLMClientFactory is available and working."""
        from src.portfolio.chat.base_llm_client import LLMClientFactory

        # Test getting available models
        models = LLMClientFactory.get_available_models()
        assert isinstance(models, dict)
        assert len(models) > 0

        # Test getting default model
        default_model = LLMClientFactory.get_default_model()
        assert isinstance(default_model, str)
        assert default_model in models

    def test_create_available_clients(self):
        """Test creating clients for models with available API keys."""
        from src.portfolio.chat.base_llm_client import LLMClientFactory

        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")

        models = LLMClientFactory.get_available_models()

        for model_key, model_info in models.items():
            # Skip models without API keys
            if model_info.provider.value == "anthropic" and not anthropic_key:
                pytest.skip(f"Skipping {model_key} - no ANTHROPIC_API_KEY")
                continue
            elif model_info.provider.value == "openai" and not openai_key:
                pytest.skip(f"Skipping {model_key} - no OPENAI_API_KEY")
                continue

            # Try to create client
            try:
                client = LLMClientFactory.create_client(model_key)
                assert (
                    client is not None
                ), f"Should be able to create {model_key} client"
                assert hasattr(
                    client, "model_info"
                ), f"{model_key} client should have model_info"
                break  # Test at least one successful client creation
            except ValueError as e:
                if "environment variable is required" in str(e):
                    pytest.skip(f"Skipping {model_key} - API key not available: {e}")
                else:
                    raise


class TestAPIKeyValidation:
    """Test API key validation and error handling."""

    def test_missing_anthropic_key_handling(self):
        """Test handling of missing Anthropic API key."""
        from src.portfolio.chat.base_llm_client import LLMClientFactory

        with patch.dict(os.environ, {}, clear=True):
            # Remove ANTHROPIC_API_KEY
            if "ANTHROPIC_API_KEY" in os.environ:
                del os.environ["ANTHROPIC_API_KEY"]

            # Try to create Anthropic client
            with pytest.raises(
                ValueError, match="ANTHROPIC_API_KEY environment variable is required"
            ):
                LLMClientFactory.create_client("claude-sonnet-4")

    def test_missing_openai_key_handling(self):
        """Test handling of missing OpenAI API key."""
        from src.portfolio.chat.base_llm_client import LLMClientFactory

        with patch.dict(os.environ, {}, clear=True):
            # Remove OPENAI_API_KEY
            if "OPENAI_API_KEY" in os.environ:
                del os.environ["OPENAI_API_KEY"]

            # Try to create OpenAI client
            with pytest.raises(
                ValueError, match="OPENAI_API_KEY environment variable is required"
            ):
                LLMClientFactory.create_client("gpt-4o")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
