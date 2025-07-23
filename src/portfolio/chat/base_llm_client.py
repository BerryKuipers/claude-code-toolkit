"""Base LLM client interface for multiple AI providers."""

import logging
import os
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Supported LLM providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    PERPLEXITY = "perplexity"


class ModelInfo:
    """Information about an LLM model."""

    def __init__(
        self,
        provider: LLMProvider,
        model_id: str,
        display_name: str,
        description: str,
        strengths: List[str],
        cost_per_1k_input: float,
        cost_per_1k_output: float,
        context_window: int,
        supports_function_calling: bool = True,
        supports_vision: bool = False,
    ):
        self.provider = provider
        self.model_id = model_id
        self.display_name = display_name
        self.description = description
        self.strengths = strengths
        self.cost_per_1k_input = cost_per_1k_input
        self.cost_per_1k_output = cost_per_1k_output
        self.context_window = context_window
        self.supports_function_calling = supports_function_calling
        self.supports_vision = supports_vision


# Available models configuration
AVAILABLE_MODELS = {
    "claude-sonnet-4": ModelInfo(
        provider=LLMProvider.ANTHROPIC,
        model_id="claude-sonnet-4-20250514",
        display_name="Claude Sonnet 4 (Recommended)",
        description="High-performance model with exceptional reasoning capabilities. Best balance of speed, intelligence, and cost for financial analysis.",
        strengths=[
            "Excellent financial reasoning",
            "Fast response times",
            "Cost-effective",
            "Latest training data (March 2025)",
            "Superior analytical capabilities",
        ],
        cost_per_1k_input=0.003,
        cost_per_1k_output=0.015,
        context_window=200000,
        supports_function_calling=True,
        supports_vision=True,
    ),
    "claude-opus-4": ModelInfo(
        provider=LLMProvider.ANTHROPIC,
        model_id="claude-opus-4-20250514",
        display_name="Claude Opus 4 (Premium)",
        description="Our most capable and intelligent model. Best for complex financial analysis and sophisticated reasoning tasks.",
        strengths=[
            "Highest level of intelligence",
            "Superior complex reasoning",
            "Best for detailed analysis",
            "Advanced problem solving",
            "Premium financial insights",
        ],
        cost_per_1k_input=0.015,
        cost_per_1k_output=0.075,
        context_window=200000,
        supports_function_calling=True,
        supports_vision=True,
    ),
    "gpt-4o": ModelInfo(
        provider=LLMProvider.OPENAI,
        model_id="gpt-4o",
        display_name="GPT-4o (OpenAI Default)",
        description="OpenAI's latest flagship model with exceptional reasoning, function calling, and multimodal capabilities. Optimized for speed and intelligence.",
        strengths=[
            "Latest OpenAI technology",
            "Excellent function calling",
            "Fast response times",
            "Superior reasoning capabilities",
            "Multimodal support (text + vision)",
            "Cost-effective for performance",
        ],
        cost_per_1k_input=0.005,
        cost_per_1k_output=0.015,
        context_window=128000,
        supports_function_calling=True,
        supports_vision=True,
    ),
    "gpt-4-turbo": ModelInfo(
        provider=LLMProvider.OPENAI,
        model_id="gpt-4-turbo-preview",
        display_name="GPT-4 Turbo",
        description="OpenAI's advanced model with strong reasoning capabilities and function calling support.",
        strengths=[
            "Strong general capabilities",
            "Good function calling",
            "Reliable performance",
            "Wide knowledge base",
            "Established ecosystem",
        ],
        cost_per_1k_input=0.01,
        cost_per_1k_output=0.03,
        context_window=128000,
        supports_function_calling=True,
        supports_vision=True,
    ),
    "gpt-4o-mini": ModelInfo(
        provider=LLMProvider.OPENAI,
        model_id="gpt-4o-mini",
        display_name="GPT-4o Mini (Budget)",
        description="OpenAI's efficient and cost-effective model with GPT-4 level intelligence at a fraction of the cost. Perfect for budget-conscious portfolio analysis.",
        strengths=[
            "GPT-4 level intelligence",
            "Very cost-effective",
            "Fast responses",
            "Excellent function calling",
            "Good reasoning capabilities",
            "Latest training data",
        ],
        cost_per_1k_input=0.00015,
        cost_per_1k_output=0.0006,
        context_window=128000,
        supports_function_calling=True,
        supports_vision=True,
    ),
}


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""

    def __init__(self, model_info: ModelInfo):
        self.model_info = model_info
        self.provider = model_info.provider
        self.model_id = model_info.model_id

    @abstractmethod
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        functions: Optional[List[Dict[str, Any]]] = None,
        function_call: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
    ) -> Any:
        """Create a chat completion with the LLM."""
        pass

    @abstractmethod
    def get_response_content(self, response: Any) -> str:
        """Extract text content from the response."""
        pass

    @abstractmethod
    def get_function_calls(self, response: Any) -> List[Dict[str, Any]]:
        """Extract function calls from the response."""
        pass

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count tokens in a text string."""
        pass

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Estimate cost of API call based on token usage."""
        prompt_cost = (prompt_tokens / 1000) * self.model_info.cost_per_1k_input
        completion_cost = (
            completion_tokens / 1000
        ) * self.model_info.cost_per_1k_output
        return prompt_cost + completion_cost

    def track_usage(
        self, prompt_tokens: int, completion_tokens: int, query_type: str = "chat"
    ):
        """Track usage with cost tracker if available.

        Args:
            prompt_tokens: Number of input tokens
            completion_tokens: Number of output tokens
            query_type: Type of query (chat, function_call, etc.)
        """
        try:
            import streamlit as st

            if "cost_tracker" in st.session_state:
                cost = self.estimate_cost(prompt_tokens, completion_tokens)
                st.session_state.cost_tracker.track_usage(
                    self.provider,
                    self.model_id,
                    prompt_tokens,
                    completion_tokens,
                    cost,
                    query_type,
                )
        except Exception as e:
            # Don't fail if cost tracking fails
            import logging

            logging.warning(f"Cost tracking failed: {e}")

    def get_model_info(self) -> ModelInfo:
        """Get information about the current model."""
        return self.model_info

    def supports_function_calling(self) -> bool:
        """Check if the model supports function calling."""
        return self.model_info.supports_function_calling

    def supports_vision(self) -> bool:
        """Check if the model supports vision/image input."""
        return self.model_info.supports_vision


class LLMClientFactory:
    """Factory for creating LLM clients."""

    @staticmethod
    def create_client(model_key: str) -> BaseLLMClient:
        """Create an LLM client for the specified model.

        Args:
            model_key: Key from AVAILABLE_MODELS

        Returns:
            Configured LLM client instance

        Raises:
            ValueError: If model_key is not supported
        """
        if model_key not in AVAILABLE_MODELS:
            raise ValueError(
                f"Unsupported model: {model_key}. Available: {list(AVAILABLE_MODELS.keys())}"
            )

        model_info = AVAILABLE_MODELS[model_key]

        if model_info.provider == LLMProvider.ANTHROPIC:
            from .anthropic_client import AnthropicClient

            return AnthropicClient(model_info)
        elif model_info.provider == LLMProvider.OPENAI:
            from .openai_client import OpenAIClient

            return OpenAIClient(model_info)
        else:
            raise ValueError(f"Provider {model_info.provider} not implemented yet")

    @staticmethod
    def get_available_models() -> Dict[str, ModelInfo]:
        """Get all available models."""
        return AVAILABLE_MODELS.copy()

    @staticmethod
    def get_default_model() -> str:
        """Get the default model key based on available API keys.

        Priority:
        1. GPT-4o (if OpenAI API key available and model exists)
        2. Claude Sonnet 4 (if Anthropic API key available and model exists)
        3. First model with available API key
        4. Final fallback to first available model
        """
        # Check for OpenAI API key first (GPT-4o as preferred default)
        if os.getenv("OPENAI_API_KEY") and "gpt-4o" in AVAILABLE_MODELS:
            return "gpt-4o"

        # Fallback to Claude Sonnet 4 if Anthropic key available
        if os.getenv("ANTHROPIC_API_KEY") and "claude-sonnet-4" in AVAILABLE_MODELS:
            return "claude-sonnet-4"

        # Find first model with available API key
        for model_key in AVAILABLE_MODELS:
            model_info = AVAILABLE_MODELS[model_key]
            if (
                model_info.provider == LLMProvider.OPENAI
                and os.getenv("OPENAI_API_KEY")
            ) or (
                model_info.provider == LLMProvider.ANTHROPIC
                and os.getenv("ANTHROPIC_API_KEY")
            ):
                return model_key

        # Final fallback to first available model (may fail if no API keys)
        return list(AVAILABLE_MODELS.keys())[0]

    @staticmethod
    def get_recommended_openai_model() -> str:
        """Get the recommended OpenAI model (GPT-4o)."""
        return "gpt-4o"

    @staticmethod
    def get_recommended_anthropic_model() -> str:
        """Get the recommended Anthropic model (Claude Sonnet 4)."""
        return "claude-sonnet-4"
